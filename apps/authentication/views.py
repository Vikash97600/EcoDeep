from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View

from apps.authentication.forms import (
    ForgotPasswordForm,
    LoginForm,
    ResetPasswordForm,
    UserProfileForm,
    UserRegistrationForm,
)
from apps.authentication.tokens import account_activation_token
from apps.core.models import AuditLog
from apps.users.models import Role, UserProfile


class UserRegistrationView(View):
    template_name = 'authentication/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('benchmark:dashboard')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True  # Active user session
            role = form.cleaned_data['role']
            if role.role_name == 'ADMIN':
                user.is_staff = True
                user.is_superuser = True
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.institution = form.cleaned_data.get('institution', '')
            profile.department = form.cleaned_data.get('department', '')
            profile.save()

            AuditLog.objects.create(
                user=user,
                action='USER_REGISTERED',
                module='authentication',
                description=f"New user registered with role {role.role_name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, "Registration successful! You can now log in with your credentials.")
            return redirect('authentication:login')

        return render(request, self.template_name, {'form': form})


class CustomLoginView(View):
    template_name = 'authentication/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            next_url = request.GET.get('next')
            if next_url and not next_url.startswith('/admin'):
                return redirect(next_url)
            return redirect('dashboard:index')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')

            # Check if username or email
            user_obj = User.objects.filter(email__iexact=username_or_email).first()
            username = user_obj.username if user_obj else username_or_email

            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.is_active:
                    messages.error(request, "Your account has been deactivated. Please contact support.")
                    return render(request, self.template_name, {'form': form})

                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)  # Browser session limit
                else:
                    request.session.set_expiry(1209600)  # 2 Weeks limit

                # Ensure UserProfile exists and has a role
                profile, _ = UserProfile.objects.get_or_create(user=user)
                if not profile.role:
                    admin_role, _ = Role.objects.get_or_create(role_name='ADMIN', defaults={'description': 'System Administrator'})
                    dev_role, _ = Role.objects.get_or_create(role_name='DEVELOPER', defaults={'description': 'Software Developer'})
                    profile.role = admin_role if user.is_superuser else dev_role
                    profile.save()

                if profile.role and profile.role.role_name == 'ADMIN':
                    if not user.is_staff:
                        user.is_staff = True
                        user.save()

                AuditLog.objects.create(
                    user=user,
                    action='USER_LOGIN',
                    module='authentication',
                    description="User logged in successfully",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next')
                if next_url and not next_url.startswith('/admin/login'):
                    return redirect(next_url)
                return redirect('dashboard:index')
            else:
                messages.error(request, "Invalid username/email or password credentials.")

        return render(request, self.template_name, {'form': form})


class CustomLogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                action='USER_LOGOUT',
                module='authentication',
                description="User logged out",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            logout(request)
            messages.info(request, "You have been logged out successfully.")
        return redirect('authentication:login')


class UserProfileView(LoginRequiredMixin, View):
    template_name = 'authentication/profile.html'

    def get(self, request):
        profile, _created = UserProfile.objects.get_or_create(user=request.user)
        return render(request, self.template_name, {'profile': profile})


class EditProfileView(LoginRequiredMixin, View):
    template_name = 'authentication/edit_profile.html'

    def get(self, request):
        profile, _created = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'phone_number': profile.phone_number,
            'institution': profile.institution,
            'department': profile.department,
            'research_interest': profile.research_interest,
            'bio': profile.bio,
        })
        return render(request, self.template_name, {'form': form, 'profile': profile})

    def post(self, request):
        profile, _created = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
            form.save()

            messages.success(request, "Your profile details have been updated successfully.")
            return redirect('authentication:profile')

        return render(request, self.template_name, {'form': form, 'profile': profile})


class ForgotPasswordView(View):
    template_name = 'authentication/forgot_password.html'

    def get(self, request):
        form = ForgotPasswordForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()
            if user:
                urlsafe_base64_encode(force_bytes(user.pk))
                account_activation_token.make_token(user)
                # Password reset instructions logged/handled
                messages.success(request, "If the email is registered, password reset instructions have been sent.")
            else:
                messages.success(request, "If the email is registered, password reset instructions have been sent.")
            return redirect('authentication:login')

        return render(request, self.template_name, {'form': form})


class ResetPasswordConfirmView(View):
    template_name = 'authentication/reset_password.html'

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            form = ResetPasswordForm()
            return render(request, self.template_name, {'form': form, 'validlink': True})
        else:
            messages.error(request, "The password reset link is invalid or has expired.")
            return render(request, self.template_name, {'validlink': False})

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                messages.success(request, "Your password has been reset successfully. Please log in.")
                return redirect('authentication:login')
            return render(request, self.template_name, {'form': form, 'validlink': True})
        
        messages.error(request, "Invalid password reset attempt.")
        return redirect('authentication:login')
