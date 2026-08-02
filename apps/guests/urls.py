from django.urls import path
from . import views

app_name = 'guests'

urlpatterns = [
    # ============================================================================
    # GESTION DES REPONSES (GuestResponse)
    # ============================================================================
    
    # Liste des reponses des invites pour un evenement
    path('<int:event_id>/responses/', views.GuestListView.as_view(), name='guest_list'),
    
    
    # ============================================================================
    # GESTION DES INVITES PRE-ENREGISTRES (InvitedGuest)
    # ============================================================================
    
    # Liste des invites pre-enregistres
    path('<int:event_id>/invited/', views.InvitedGuestListView.as_view(), name='invited_list'),
    
    # Ajout manuel d'un invite
    path('<int:event_id>/invited/add/', views.AddInvitedGuestView.as_view(), name='add_invited'),
    
    # Import Excel des invites
    path('<int:event_id>/invited/import/', views.BulkImportGuestsView.as_view(), name='bulk_import'),
    
    
    # ============================================================================
    # EXPORTS DES INVITES ET REPONSES
    # ============================================================================
    
    # Export des reponses au format CSV
    path('<int:event_id>/responses/export/csv/', views.ExportGuestsCSVView.as_view(), name='export_guests_csv'),
    
    # Export des reponses au format Excel
    path('<int:event_id>/responses/export/excel/', views.ExportGuestsExcelView.as_view(), name='export_guests_excel'),
    
    # Export des check-ins au format CSV
    path('<int:event_id>/checkins/export/csv/', views.ExportCheckinsCSVView.as_view(), name='export_checkins_csv'),
    
    # Export des check-ins au format Excel
    path('<int:event_id>/checkins/export/excel/', views.ExportCheckinsExcelView.as_view(), name='export_checkins_excel'),
    
    # Export des invites pre-enregistres au format CSV
    path('<int:event_id>/invited/export/csv/', views.ExportInvitedCSVView.as_view(), name='export_invited_csv'),
    
    # Export des invites pre-enregistres au format Excel
    path('<int:event_id>/invited/export/excel/', views.ExportInvitedExcelView.as_view(), name='export_invited_excel'),
    
    
    # ============================================================================
    # RSVP (PUBLIC)
    # ============================================================================
    
    # Formulaire RSVP public
    path('rsvp/<slug:slug>/<str:token>/', views.RSVPFormView.as_view(), name='rsvp'),
    
    # Page de remerciement apres RSVP
    path('rsvp/thanks/', views.RSVPThanksView.as_view(), name='rsvp_thanks'),
    
    
    # ============================================================================
    # CHECK-IN
    # ============================================================================
    
    # Scanner QR code (affichage)
    path('<int:event_id>/scan/', views.CheckinScanView.as_view(), name='checkin_scan'),
    
    # Validation QR code (ajax)
    path('<int:event_id>/scan/qr/', views.CheckinQRView.as_view(), name='checkin_qr'),
    
    # Saisie manuelle du code court
    path('<int:event_id>/scan/manual/', views.CheckinManualView.as_view(), name='checkin_manual'),
    
    # Validation finale du check-in
    path('checkin/<str:token>/', views.CheckInView.as_view(), name='checkin'),
    
    
    # ============================================================================
    # ASSIGNATION DES TABLES (DELEGUE A GUESTS)
    # ============================================================================
    
    # Assigner un invite a une table
    path('<int:event_id>/assign-table/', views.AssignGuestTableView.as_view(), name='assign_guest_table'),
]