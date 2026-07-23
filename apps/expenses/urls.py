from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # ============================================================
    # PRÉVISIONS (la page principale)
    # ============================================================
    path('event/<int:event_id>/forecast/', 
         views.ForecastView.as_view(), 
         name='forecast'),
    
    path('event/<int:event_id>/forecast/save/', 
         views.SaveForecastView.as_view(), 
         name='save_forecast'),
    
    path('event/<int:event_id>/forecast/pdf/', 
         views.ExportForecastPDFView.as_view(), 
         name='export_forecast_pdf'),
    
    path('event/<int:event_id>/remove-drink/', 
         views.RemoveDrinkView.as_view(), 
         name='remove_drink'),

    # ============================================================
    # ESTIMATION (basée sur les réponses)
    # ============================================================
    path('event/<int:event_id>/estimation/', 
         views.EstimationDashboardView.as_view(), 
         name='estimation'),
    
    path('event/<int:event_id>/estimation/save-settings/', 
         views.SaveEstimationSettingsView.as_view(), 
         name='save_estimation_settings'),

    path('event/<int:event_id>/devis/', 
         views.ExportDevisPDFView.as_view(), 
         name='export_devis'),
    
    path('event/<int:event_id>/devis/summary/', 
         views.ExportDevisSummaryView.as_view(), 
         name='export_devis_summary'),
]