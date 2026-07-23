from django.urls import path
from . import views

app_name = 'invitation'

urlpatterns = [
    path('download/<uuid:token>/', views.GenerateInvitationPDFView.as_view(), name='download_pdf'),
    path('preview/<uuid:token>/', views.InvitationPreviewView.as_view(), name='preview_pdf'),
]