from django.urls import path
from . import views

app_name = 'guests'

urlpatterns = [
    # RSVP public (lien unique pour tous les invités – géré dans events/urls.py)
    # path('rsvp/<uuid:token>/', views.RSVPView.as_view(), name='rsvp'),  # SUPPRIMÉ

    # Page de remerciement
    path('thanks/', views.RSVPThanksView.as_view(), name='rsvp_thanks'),

    # Gestion des invités (organisateur)
    path('event/<int:event_id>/', views.GuestListView.as_view(), name='guest_list'),
    path('event/<int:event_id>/import/', views.BulkImportGuestsView.as_view(), name='bulk_import'),
    path('checkin/<str:token>/', views.CheckInView.as_view(), name='checkin'),

    # Exports
    path('export/csv/<int:event_id>/', views.ExportGuestsCSVView.as_view(), name='export_csv'),
    path('export/excel/<int:event_id>/', views.ExportGuestsExcelView.as_view(), name='export_excel'),

    # PDF invitation (si nécessaire)
    path('invitation/<uuid:token>/', views.InvitationPDFView.as_view(), name='invitation_pdf'),
    path('event/<int:event_id>/invited/', views.InvitedGuestListView.as_view(), name='invited_list'),
    path('event/<int:event_id>/export-invited-csv/', views.ExportInvitedCSVView.as_view(), name='export_invited_csv'),
    path('event/<int:event_id>/export-invited-excel/', views.ExportInvitedExcelView.as_view(), name='export_invited_excel'),
    path('event/<int:event_id>/add/', views.AddInvitedGuestView.as_view(), name='add_guest'),
    path('guest/<int:guest_id>/assign-table/', views.AssignGuestTableView.as_view(), name='assign_guest_table'),
# Invitation PDF
    path('invitation/<uuid:token>/', views.InvitationPDFView.as_view(), name='invitation_pdf'),
    path('invitation/<uuid:token>/preview/', views.InvitationPreviewView.as_view(), name='invitation_preview'),
    path('export/checkins-csv/<int:event_id>/', views.ExportCheckinsCSVView.as_view(), name='export_checkins_csv'),
    path('export/checkins-excel/<int:event_id>/', views.ExportCheckinsExcelView.as_view(), name='export_checkins_excel'),
    
    path('checkin/scan/<int:event_id>/', views.CheckinScanView.as_view(), name='checkin_scan'),
    path('checkin/qr/<int:event_id>/', views.CheckinQRView.as_view(), name='checkin_qr'),
    path('checkin/manual/<int:event_id>/', views.CheckinManualView.as_view(), name='checkin_manual'),
    path('checkin/<str:token>/', views.CheckInView.as_view(), name='checkin'),
]
