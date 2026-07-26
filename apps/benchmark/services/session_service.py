from django.utils import timezone
from apps.benchmark.models import BenchmarkSession, BenchmarkJob, BenchmarkStatusChoices
from apps.benchmark.services.environment_service import EnvironmentService

class SessionService:
    """Manages benchmark session creation, job queuing, and state transitions."""

    @staticmethod
    def create_session(session_name, admin_user, task, library_versions, notes=""):
        env_specs = EnvironmentService.get_host_environment()
        
        session = BenchmarkSession.objects.create(
            session_name=session_name,
            admin=admin_user,
            machine_name=env_specs['machine_name'],
            operating_system=env_specs['operating_system'],
            cpu=env_specs['cpu'],
            ram=env_specs['ram'],
            python_version=env_specs['python_version'],
            status=BenchmarkStatusChoices.PENDING,
            notes=notes
        )

        # Enqueue individual BenchmarkJobs for each candidate LibraryVersion
        for index, version in enumerate(library_versions, start=1):
            BenchmarkJob.objects.create(
                session=session,
                library_version=version,
                task=task,
                status=BenchmarkStatusChoices.PENDING,
                priority=index
            )

        return session

    @staticmethod
    def cancel_session(session_id, user):
        session = BenchmarkSession.objects.get(pk=session_id)
        session.status = BenchmarkStatusChoices.CANCELLED
        session.end_time = timezone.now()
        session.save()

        session.jobs.filter(status=BenchmarkStatusChoices.PENDING).update(status=BenchmarkStatusChoices.CANCELLED)
        return session
