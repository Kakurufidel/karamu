from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # ============================================================
    # GESTION DES ÉVÉNEMENTS
    # ============================================================
    path('', views.EventListView.as_view(), name='event_list'),
    path('create/', views.EventCreateView.as_view(), name='event_create'),
    path('<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<slug:slug>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('<slug:slug>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    
    # ============================================================
    # CO-ORGANISATEURS
    # ============================================================
    path('<slug:slug>/join/<str:token>/', views.JoinCoOrganizerView.as_view(), name='join_coorganizer'),
    path('join/<str:short_code>/', views.JoinCoOrganizerShortCodeView.as_view(), name='join_coorganizer_short'),
    path('collaborator/<int:pk>/toggle-scan/', views.CollaboratorScanPermissionView.as_view(), name='collaborator_toggle_scan'),
    path('collaborator/<int:pk>/delete/', views.CollaboratorDeleteView.as_view(), name='collaborator_delete'),
    
    # ============================================================
    # RSVP PUBLIC
    # ============================================================
    path('<slug:slug>/rsvp/<str:token>/', views.RSVPFormView.as_view(), name='rsvp'),
    
    # ============================================================
    # GESTION DES TABLES
    # ============================================================
    path('<int:event_id>/tables/', views.TableListView.as_view(), name='table_list'),
    path('<int:event_id>/tables/create/', views.TableCreateView.as_view(), name='table_create'),
    path('tables/<int:pk>/edit/', views.TableUpdateView.as_view(), name='table_update'),
    path('tables/<int:pk>/delete/', views.TableDeleteView.as_view(), name='table_delete'),
    path('tables/<int:pk>/detail/', views.TableDetailAjaxView.as_view(), name='table_detail_ajax'),
    path('<int:event_id>/tables/auto-assign/', views.AutoAssignTablesView.as_view(), name='auto_assign_tables'),
    path('<int:event_id>/tables/assign/', views.AssignGuestTableView.as_view(), name='assign_guest_table'),
    
    # ============================================================
    # EXPORTS TABLES
    # ============================================================
    path('<int:event_id>/tables/pdf/', views.TablesPDFView.as_view(), name='tables_pdf'),
    path('<int:event_id>/tables/export/csv/', views.ExportTablesCSVView.as_view(), name='export_tables_csv'),
    path('<int:event_id>/tables/export/excel/', views.ExportTablesExcelView.as_view(), name='export_tables_excel'),
]