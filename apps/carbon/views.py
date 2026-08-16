from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from apps.carbon.models import (
    RegionalGridCarbonFactor, CarbonEmissionRecord, CarbonSavingsEstimate, CarbonForecast
)
from apps.carbon.forms import CarbonComparisonForm, CarbonSavingsCalculatorForm
from apps.carbon.services.regional_carbon_service import RegionalCarbonService
from apps.carbon.services.carbon_comparison_service import CarbonComparisonService
from apps.carbon.services.carbon_savings_service import CarbonSavingsService
from apps.carbon.services.carbon_forecast_service import CarbonForecastService
from apps.libraries.models import Library

class CarbonIntelligenceDashboardView(View):
    template_name = 'carbon/carbon_dashboard.html'

    def get(self, request):
        RegionalCarbonService.get_or_create_default_regions()
        context = {
            'total_regions': RegionalGridCarbonFactor.objects.count(),
            'total_records': CarbonEmissionRecord.objects.count(),
            'total_savings_estimates': CarbonSavingsEstimate.objects.count(),
            'recent_savings': CarbonSavingsEstimate.objects.select_related('source_library', 'target_library', 'regional_grid').order_by('-created_at')[:6],
            'regional_grids': RegionalGridCarbonFactor.objects.all()[:6]
        }
        return render(request, self.template_name, context)


class RegionalGridListView(ListView):
    model = RegionalGridCarbonFactor
    template_name = 'carbon/regional_grids.html'
    context_object_name = 'grids'


class CarbonComparisonStudioView(View):
    template_name = 'carbon/carbon_comparison.html'

    def get(self, request):
        RegionalCarbonService.get_or_create_default_regions()
        form = CarbonComparisonForm()
        lib_a_id = request.GET.get('library_a')
        lib_b_id = request.GET.get('library_b')
        grid_id = request.GET.get('regional_grid')
        comparison = None

        if lib_a_id and lib_b_id:
            lib_a = get_object_or_404(Library, pk=lib_a_id)
            lib_b = get_object_or_404(Library, pk=lib_b_id)
            grid = RegionalGridCarbonFactor.objects.filter(pk=grid_id).first() if grid_id else RegionalCarbonService.get_default_region()
            form = CarbonComparisonForm(initial={'library_a': lib_a, 'library_b': lib_b, 'regional_grid': grid})
            comparison = CarbonComparisonService.compare_libraries(lib_a, lib_b, grid)

        context = {
            'form': form,
            'comparison': comparison
        }
        return render(request, self.template_name, context)


class CarbonSavingsCalculatorView(View):
    template_name = 'carbon/carbon_savings.html'

    def get(self, request):
        RegionalCarbonService.get_or_create_default_regions()
        form = CarbonSavingsCalculatorForm()
        src_id = request.GET.get('source_library')
        tgt_id = request.GET.get('target_library')
        grid_id = request.GET.get('regional_grid')
        reqs = int(request.GET.get('annual_requests', 10000000))
        estimate = None

        if src_id and tgt_id:
            src_lib = get_object_or_404(Library, pk=src_id)
            tgt_lib = get_object_or_404(Library, pk=tgt_id)
            grid = RegionalGridCarbonFactor.objects.filter(pk=grid_id).first() if grid_id else RegionalCarbonService.get_default_region()
            
            src_e = 5.80 if 'json' in src_lib.library_name.lower() else 4.5
            tgt_e = 2.15 if 'ujson' in tgt_lib.library_name.lower() or 'fast' in tgt_lib.library_name.lower() else 3.0

            estimate = CarbonSavingsService.calculate_savings(
                source_lib=src_lib,
                target_lib=tgt_lib,
                source_energy_joules=src_e,
                target_energy_joules=tgt_e,
                grid=grid,
                requests_per_year=reqs
            )
            form = CarbonSavingsCalculatorForm(initial={'source_library': src_lib, 'target_library': tgt_lib, 'regional_grid': grid, 'annual_requests': reqs})

        context = {
            'form': form,
            'estimate': estimate,
            'recent_estimates': CarbonSavingsEstimate.objects.select_related('source_library', 'target_library', 'regional_grid')[:5]
        }
        return render(request, self.template_name, context)


class CarbonForecastView(View):
    template_name = 'carbon/carbon_forecast.html'

    def get(self, request):
        RegionalCarbonService.get_or_create_default_regions()
        lib_id = request.GET.get('library')
        forecast = None
        library = None

        if lib_id:
            library = get_object_or_404(Library, pk=lib_id)
            grid = RegionalCarbonService.get_default_region()
            forecast = CarbonForecastService.generate_12_month_forecast(library, grid)

        context = {
            'libraries': Library.objects.all(),
            'selected_library': library,
            'forecast': forecast
        }
        return render(request, self.template_name, context)
