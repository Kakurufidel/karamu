"""
Vues de l'application invitation.
Generation et telechargement des invitations PDF.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.utils.translation import gettext as _

from apps.guests.models import GuestResponse
from .services import InvitationPDFService


class GenerateInvitationPDFView(View):
    """
    Genere et telecharge l'invitation PDF pour un invite verifie.
    """
    
    def get(self, request, token):
        """
        Telecharge le PDF d'invitation.
        
        Args:
            token: Token d'invitation de l'invite
        """
        guest = get_object_or_404(GuestResponse, invitation_token=token)
        
        # Verifier que l'invite est verifie
        if guest.verification_status != 'verified':
            messages.warning(
                request,
                _('Seuls les invites verifies peuvent telecharger leur invitation.')
            )
            return redirect('guests:guest_list', event_id=guest.event.id)
        
        # Verifier que l'evenement a une date
        if not guest.event.date:
            messages.error(
                request,
                _("L'evenement n'a pas de date configuree.")
            )
            return redirect('guests:guest_list', event_id=guest.event.id)
        
        try:
            service = InvitationPDFService(guest_response=guest)
            pdf_content = service.generate()
            
            if not pdf_content:
                messages.error(
                    request,
                    _('Erreur lors de la generation du PDF. Veuillez reessayer.')
                )
                return redirect('guests:guest_list', event_id=guest.event.id)
            
            # Nom du fichier
            filename = (
                f"invitation_{guest.event.slug}"
                f"_{guest.first_name}_{guest.last_name}.pdf"
            )
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        except Exception as e:
            messages.error(
                request,
                _('Erreur lors de la generation du PDF: {error}').format(error=str(e))
            )
            return redirect('guests:guest_list', event_id=guest.event.id)


class InvitationPreviewView(View):
    """
    Previsualise l'invitation PDF dans le navigateur.
    """
    
    def get(self, request, token):
        """
        Affiche le PDF d'invitation dans le navigateur.
        
        Args:
            token: Token d'invitation de l'invite
        """
        guest = get_object_or_404(GuestResponse, invitation_token=token)
        
        # Verifier que l'invite est verifie
        if guest.verification_status != 'verified':
            messages.warning(
                request,
                _('Seuls les invites verifies peuvent visualiser leur invitation.')
            )
            return redirect('guests:guest_list', event_id=guest.event.id)
        
        # Verifier que l'evenement a une date
        if not guest.event.date:
            messages.error(
                request,
                _("L'evenement n'a pas de date configuree.")
            )
            return redirect('guests:guest_list', event_id=guest.event.id)
        
        try:
            service = InvitationPDFService(guest_response=guest)
            pdf_content = service.generate()
            
            if not pdf_content:
                messages.error(
                    request,
                    _('Erreur lors de la generation du PDF. Veuillez reessayer.')
                )
                return redirect('guests:guest_list', event_id=guest.event.id)
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'inline; filename="invitation_{guest.event.slug}.pdf"'
            )
            return response
        
        except Exception as e:
            messages.error(
                request,
                _('Erreur lors de la generation du PDF: {error}').format(error=str(e))
            )
            return redirect('guests:guest_list', event_id=guest.event.id)