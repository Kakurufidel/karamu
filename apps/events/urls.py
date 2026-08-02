from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # ============================================================================
    # GESTION DES EVENEMENTS
    # ============================================================================
    
    # Liste des evenements de l'utilisateur
    path('', views.EventListView.as_view(), name='event_list'),
    
    # Creation d'un evenement
    path('create/', views.EventCreateView.as_view(), name='event_create'),
    
    # Detail d'un evenement
    path('<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    
    # Modification d'un evenement
    path('<slug:slug>/update/', views.EventUpdateView.as_view(), name='event_update'),
    
    # Suppression d'un evenement
    path('<slug:slug>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    
    
    # ============================================================================
    # CO-ORGANISATEURS
    # ============================================================================
    
    # Rejoindre comme co-organisateur avec token
    path('join/<slug:slug>/<str:token>/', views.JoinCoOrganizerView.as_view(), name='join_coorganizer'),
    
    # Rejoindre comme co-organisateur avec code court
    path('join/<str:short_code>/', views.JoinCoOrganizerShortCodeView.as_view(), name='join_coorganizer_short'),
    
    # Activer/desactiver le droit de scan d'un co-organisateur
    path('collaborator/<int:pk>/toggle-scan/', views.CollaboratorScanPermissionView.as_view(), name='collaborator_toggle_scan'),
    
    # Retirer un co-organisateur
    path('collaborator/<int:pk>/delete/', views.CollaboratorDeleteView.as_view(), name='collaborator_delete'),
    
    
    # ============================================================================
    # GESTION DES TABLES
    # ============================================================================
    
    # Liste des tables d'un evenement
    path('<int:event_id>/tables/', views.TableListView.as_view(), name='table_list'),
    
    # Creation d'une table
    path('<int:event_id>/tables/create/', views.TableCreateView.as_view(), name='table_create'),
    
    # Modification d'une table
    path('tables/<int:pk>/update/', views.TableUpdateView.as_view(), name='table_update'),
    
    # Suppression d'une table
    path('tables/<int:pk>/delete/', views.TableDeleteView.as_view(), name='table_delete'),
    
    # Assignation automatique des tables
    path('<int:event_id>/tables/auto-assign/', views.AutoAssignTablesView.as_view(), name='auto_assign_tables'),
    
    
    # ============================================================================
    # EXPORTS DES TABLES
    # ============================================================================
    
    # Export des tables au format PDF
    path('<int:event_id>/tables/pdf/', views.TablesPDFView.as_view(), name='tables_pdf'),
    
    # Export des tables au format CSV
    path('<int:event_id>/tables/csv/', views.ExportTablesCSVView.as_view(), name='tables_csv'),
    
    # Export des tables au format Excel
    path('<int:event_id>/tables/excel/', views.ExportTablesExcelView.as_view(), name='tables_excel'),
]