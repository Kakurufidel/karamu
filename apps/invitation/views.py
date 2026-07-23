from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.utils.translation import gettext as _

from apps.guests.models import GuestResponse
from .services import InvitationPDFService


class GenerateInvitationPDFView(View):
    """Génère et télécharge l'invitation PDF"""

    def get(self, request, token):
        guest = get_object_or_404(GuestResponse, invitation_token=token)

        # Vérifier que l'invité est vérifié
        if guest.verification_status != 'verified':
            messages.warning(request, 'Seuls les invités vérifiés peuvent télécharger leur invitation.')
            return redirect('guests:guest_list', event_id=guest.event.id)

        # Vérifier que l'événement a une date
        if not guest.event.date:
            messages.error(request, "L'événement n'a pas de date configurée.")
            return redirect('guests:guest_list', event_id=guest.event.id)

        try:
            service = InvitationPDFService(guest_response=guest)
            pdf_content = service.generate()

            if not pdf_content:
                messages.error(request, 'Erreur lors de la génération du PDF. Veuillez réessayer.')
                return redirect('guests:guest_list', event_id=guest.event.id)

            # Nom du fichier
            filename = f"invitation_{guest.event.slug}_{guest.first_name}_{guest.last_name}.pdf"

            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
            return redirect('guests:guest_list', event_id=guest.event.id)


class InvitationPreviewView(View):
    """Prévisualise l'invitation PDF dans le navigateur"""

    def get(self, request, token):
        guest = get_object_or_404(GuestResponse, invitation_token=token)

        # Vérifier que l'invité est vérifié
        if guest.verification_status != 'verified':
            messages.warning(request, 'Seuls les invités vérifiés peuvent voir leur invitation.')
            return redirect('guests:guest_list', event_id=guest.event.id)

        # Vérifier que l'événement a une date
        if not guest.event.date:
            messages.error(request, "L'événement n'a pas de date configurée.")
            return redirect('guests:guest_list', event_id=guest.event.id)

        try:
            service = InvitationPDFService(guest_response=guest)
            pdf_content = service.generate()

            if not pdf_content:
                messages.error(request, 'Erreur lors de la génération du PDF. Veuillez réessayer.')
                return redirect('guests:guest_list', event_id=guest.event.id)

            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="invitation_{guest.event.slug}.pdf"'
            return response

        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
            return redirect('guests:guest_list', event_id=guest.event.id)