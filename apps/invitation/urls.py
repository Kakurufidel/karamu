from django.urls import path
from . import views

app_name = 'invitation'

urlpatterns = [
    # Telechargement du PDF d'invitation (attachment)
    path('download/<str:token>/', views.GenerateInvitationPDFView.as_view(), name='download_pdf'),
    
    # Previsualisation du PDF dans le navigateur (inline)
    path('preview/<str:token>/', views.InvitationPreviewView.as_view(), name='preview_pdf'),
]