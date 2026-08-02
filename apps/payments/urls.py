from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # ============================================================================
    # DEMANDES DE PAIEMENT (ORGANISATEUR)
    # ============================================================================
    
    # Creer une demande de paiement pour un evenement
    path('request/<int:event_id>/', views.PaymentRequestCreateView.as_view(), name='payment_request'),
    
    
    # ============================================================================
    # ADMINISTRATION DES PAIEMENTS (STAFF UNIQUEMENT)
    # ============================================================================
    
    # Liste des demandes de paiement pour l'admin
    path('admin/list/', views.AdminPaymentListView.as_view(), name='admin_list'),
    
    # Approuver ou rejeter une demande de paiement
    path('admin/approve/<int:pk>/', views.AdminPaymentApproveView.as_view(), name='admin_approve'),
]

