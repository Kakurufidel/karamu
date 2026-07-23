import csv
import json
import logging
import uuid
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView, TemplateView, FormView, CreateView, DeleteView
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.template.loader import render_to_string

from apps.events.models import Event, Table
from .models import GuestResponse, InvitedGuest
from .forms import RSVPForm, InvitedGuestForm, GuestBulkImportForm
from .services import import_guests_from_excel, generate_invitation_pdf

logger = logging.getLogger(__name__)


# ============================================================
# 1. LISTE DES RÉPONSES (GUEST RESPONSE)
# ============================================================

class GuestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Liste des réponses des invités pour un événement."""
    template_name = 'guests/guest_list.html'
    context_object_name = 'guests'

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs.get('event_id'))
        user = self.request.user
        return (self.event.main_organizer == user or
                self.event.collaborators.filter(user=user, status='accepted').exists())

    def get_paginate_by(self, queryset):
        per_page = self.request.GET.get('per_page')
        if per_page and per_page.isdigit():
            per_page = int(per_page)
            if per_page in [10, 15, 20, 30, 50, 100]:
                return per_page
        return getattr(settings, 'GUESTS_PER_PAGE', 20)

    def get_queryset(self):
        return self.event.responses.all().order_by('-submitted_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        context['current_per_page'] = self.get_paginate_by(self.get_queryset())
        responses = self.event.responses
        context['stats'] = {
            'total': responses.count(),
            'attending': responses.filter(will_attend=True).count(),
            'not_attending': responses.filter(will_attend=False).count(),
            'verified': responses.filter(verification_status='verified').count(),
            'unverified': responses.filter(verification_status='unverified').count(),
        }
        return context


# ============================================================
# 2. EXPORTS DES RÉPONSES (CSV / EXCEL)
# ============================================================

class ExportGuestsCSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Export CSV des réponses invités."""
    
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return (self.event.main_organizer == self.request.user or
                self.event.collaborators.filter(user=self.request.user, status='accepted').exists())

    def get(self, request, event_id):
        responses = self.event.responses.all().order_by('-submitted_at')
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="responses_{self.event.id}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            _('First name'), _('Last name'), _('Email'), _('Phone'),
            _('Will attend'), _('Number of guests'), _('Accompanied'),
            _('Drink choice'), _('Other drink'), _('Verification status'),
            _('Submitted at')
        ])
        
        for r in responses:
            writer.writerow([
                r.first_name, r.last_name, r.email, r.phone,
                _('Yes') if r.will_attend else _('No'),
                r.number_of_guests,
                _('Yes') if r.is_accompanied else _('No'),
                r.drink_display, r.drink_other or '',
                r.get_verification_status_display(),
                r.submitted_at.strftime('%d/%m/%Y %H:%M'),
            ])
        return response


class ExportGuestsExcelView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Export Excel des réponses invités."""
    
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return (self.event.main_organizer == self.request.user or
                self.event.collaborators.filter(user=self.request.user, status='accepted').exists())

    def get(self, request, event_id):
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        
        responses = self.event.responses.all().order_by('-submitted_at')
        
        wb = Workbook()
        ws = wb.active
        ws.title = str(_('Responses'))
        
        headers = [
            _('First name'), _('Last name'), _('Email'), _('Phone'),
            _('Will attend'), _('Number of guests'), _('Accompanied'),
            _('Drink choice'), _('Other drink'), _('Verification status'),
            _('Submitted at')
        ]
        
        header_font = Font(bold=True)
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        
        for row, r in enumerate(responses, 2):
            ws.cell(row=row, column=1, value=r.first_name)
            ws.cell(row=row, column=2, value=r.last_name)
            ws.cell(row=row, column=3, value=r.email)
            ws.cell(row=row, column=4, value=r.phone)
            ws.cell(row=row, column=5, value=_('Yes') if r.will_attend else _('No'))
            ws.cell(row=row, column=6, value=r.number_of_guests)
            ws.cell(row=row, column=7, value=_('Yes') if r.is_accompanied else _('No'))
            ws.cell(row=row, column=8, value=r.drink_display)
            ws.cell(row=row, column=9, value=r.drink_other or '')
            ws.cell(row=row, column=10, value=r.get_verification_status_display())
            ws.cell(row=row, column=11, value=r.submitted_at.strftime('%d/%m/%Y %H:%M'))
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="responses_{self.event.id}.xlsx"'
        wb.save(response)
        return response


# ============================================================
# 3. EXPORT DES CHECK-INS
# ============================================================

class ExportCheckinsCSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Export CSV des check-ins."""
    
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return self.request.user == self.event.main_organizer

    def get(self, request, event_id):
        responses = GuestResponse.objects.filter(
            event=self.event,
            checkin_time__isnull=False
        ).select_related('table').order_by('checkin_time')
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="checkins_{self.event.id}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow(['Nom', 'Email', 'Table', "Heure d'arrivée"])
        
        for r in responses:
            writer.writerow([
                r.get_full_name(),
                r.email,
                r.table.number if r.table else '-',
                r.checkin_time.strftime('%d/%m/%Y %H:%M')
            ])
        return response


class ExportCheckinsExcelView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Export Excel des check-ins."""
    
    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return self.request.user == self.event.main_organizer

    def get(self, request, event_id):
        from openpyxl import Workbook
        from openpyxl.styles import Font
        
        responses = GuestResponse.objects.filter(
            event=self.event,
            checkin_time__isnull=False
        ).select_related('table').order_by('checkin_time')
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Check-ins"
        
        headers = ['Nom', 'Email', 'Table', "Heure d'arrivée"]
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header).font = Font(bold=True)
        
        for row, r in enumerate(responses, 2):
            ws.cell(row=row, column=1, value=r.get_full_name())
            ws.cell(row=row, column=2, value=r.email)
            ws.cell(row=row, column=3, value=r.table.number if r.table else '-')
            ws.cell(row=row, column=4, value=r.checkin_time.strftime('%d/%m/%Y %H:%M'))
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="checkins_{self.event.id}.xlsx"'
        wb.save(response)
        return response


# ============================================================
# 4. RSVP - MERCI
# ============================================================

class RSVPThanksView(TemplateView):
    """Page de remerciement après RSVP."""
    template_name = 'guests/rsvp_thanks.html'


# ============================================================
# 5. IMPORT EXCEL
# ============================================================

class BulkImportGuestsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Import Excel d'invités pré-enregistrés."""
    template_name = 'guests/bulk_import.html'

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return self.request.user == self.event.main_organizer

    def get(self, request, event_id):
        form = GuestBulkImportForm()
        return render(request, self.template_name, {'form': form, 'event': self.event})

    def post(self, request, event_id):
        form = GuestBulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            result = import_guests_from_excel(excel_file, self.event, request.user)
            
            if result['created'] > 0:
                messages.success(
                    request,
                    _(' Import terminé : %(created)s invités ajoutés, %(updated)s mis à jour.') % {
                        'created': result['created'],
                        'updated': result['updated']
                    }
                )
            elif result['updated'] > 0:
                messages.info(
                    request,
                    _('ℹ️ %(updated)s invités ont été mis à jour. Aucun nouvel invité ajouté.') % {
                        'updated': result['updated']
                    }
                )
            
            if result['errors'] > 0:
                messages.error(
                    request,
                    _(' %(errors)s erreurs rencontrées. Détails : %(details)s') % {
                        'errors': result['errors'],
                        'details': ', '.join(result['error_messages'][:3]) 
                    }
                )
            
            if result['created'] == 0 and result['updated'] == 0 and result['errors'] == 0:
                messages.warning(
                    request,
                    _('Aucune donnée importée. Vérifiez le format du fichier.')
                )
            
            return redirect('guests:invited_list', event_id=self.event.id)
        
        messages.error(request, _('Le fichier n\'est pas valide. Vérifiez le format (Excel ou CSV).'))
        return render(request, self.template_name, {'form': form, 'event': self.event})

# ============================================================
# 6. CHECK-IN SCAN (AFFICHAGE DU SCANNER)
# ============================================================

class CheckinScanView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Vue pour afficher le scanner de QR code.
    Accessible uniquement aux organisateurs et co-organisateurs avec can_scan=True.
    """
    template_name = 'guests/checkin_scan.html'

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        user = self.request.user
        is_organizer = (self.event.main_organizer == user)
        is_collaborator_with_scan = self.event.collaborators.filter(user=user, can_scan=True).exists()
        return is_organizer or is_collaborator_with_scan

    def get(self, request, event_id):
        return render(request, self.template_name, {
            'event': self.event,
        })


# ============================================================
# 7. CHECK-IN PAR QR CODE (VALIDATION)
# ============================================================

class CheckinQRView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vue pour afficher les infos du QR code scanné et valider le check-in"""
    template_name = 'guests/checkin_qr.html'

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        user = self.request.user
        is_organizer = (self.event.main_organizer == user)
        is_collaborator_with_scan = self.event.collaborators.filter(user=user, can_scan=True).exists()
        return is_organizer or is_collaborator_with_scan

    def post(self, request, event_id):
        data = request.POST.get('data')
        if not data:
            messages.error(request, _('Données QR code invalides.'))
            return redirect('guests:checkin_scan', event_id=event_id)
        
        try:
            import json
            guest_data = json.loads(data)
            
            # Récupérer les informations du QR code
            short_code = guest_data.get('short_code')
            first_name = guest_data.get('first_name')
            last_name = guest_data.get('last_name')
            
            guest = None
            
            # 1. Essayer par short_code
            if short_code:
                try:
                    guest = GuestResponse.objects.get(short_code=short_code, event=self.event)
                except GuestResponse.DoesNotExist:
                    pass
            
            # 2. Essayer par nom + prénom
            if not guest and first_name and last_name:
                try:
                    guest = GuestResponse.objects.get(
                        event=self.event,
                        first_name=first_name,
                        last_name=last_name
                    )
                except GuestResponse.DoesNotExist:
                    pass
                except GuestResponse.MultipleObjectsReturned:
                    # Si plusieurs invités avec le même nom, on prend le plus récent
                    guest = GuestResponse.objects.filter(
                        event=self.event,
                        first_name=first_name,
                        last_name=last_name
                    ).latest('submitted_at')
            
            if not guest:
                messages.error(request, _('Invité non trouvé.'))
                return redirect('guests:checkin_scan', event_id=event_id)
            
            # Vérifier si déjà scanné
            if guest.checkin_time:
                messages.warning(request, _('Cet invité a déjà été scanné à {}.').format(
                    guest.checkin_time.strftime("%H:%M")
                ))
                return render(request, self.template_name, {
                    'guest': guest,
                    'already_checked_in': True,
                    'event': self.event,
                })
            
            # Enregistrer le check-in
            guest.checkin_time = timezone.now()
            guest.save(update_fields=['checkin_time'])
            
            messages.success(request, _('Check-in validé pour {} !').format(guest.get_full_name()))
            
            # Afficher les informations du guest
            return render(request, self.template_name, {
                'guest': guest,
                'success': True,
                'event': self.event,
            })
            
        except json.JSONDecodeError:
            messages.error(request, _('QR code invalide.'))
            return redirect('guests:checkin_scan', event_id=event_id)
        except Exception as e:
            messages.error(request, _('Erreur lors du traitement: {}').format(str(e)))
            return redirect('guests:checkin_scan', event_id=event_id)

# ============================================================
# 8. CHECK-IN MANUEL (CODE COURT)
# ============================================================

class CheckinManualView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vue pour la saisie manuelle du code court"""

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        user = self.request.user
        is_organizer = (self.event.main_organizer == user)
        is_collaborator_with_scan = self.event.collaborators.filter(user=user, can_scan=True).exists()
        return is_organizer or is_collaborator_with_scan

    def get(self, request, event_id):
        code = request.GET.get('code', '').strip().upper()
        if not code:
            messages.error(request, _('Veuillez saisir un code.'))
            return redirect('guests:checkin_scan', event_id=event_id)

        try:
            guest = GuestResponse.objects.get(short_code=code, event=self.event)
            return redirect('guests:checkin', token=guest.short_code)
        except GuestResponse.DoesNotExist:
            messages.error(request, _('Code invalide. Aucun invité trouvé.'))
            return redirect('guests:checkin_scan', event_id=event_id)


# ============================================================
# 9. CHECK-IN (VALIDATION FINALE)
# ============================================================

class CheckInView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Vue pour scanner le QR code (ou saisir le code court) et valider l'arrivée d'un invité.
    """
    template_name = 'guests/checkin.html'
    success_template = 'guests/checkin_success.html'

    def test_func(self):
        return True

    def dispatch(self, request, *args, **kwargs):
        token = kwargs.get('token')
        
        # Nettoyer le token
        token = token.strip('"{}')
        guest_response = None
        
        # 1. Essayer par UUID
        try:
            uuid_obj = uuid.UUID(token)
            guest_response = GuestResponse.objects.get(invitation_token=uuid_obj)
        except (ValueError, GuestResponse.DoesNotExist):
            pass
        
        # 2. Essayer par short_code
        if not guest_response:
            try:
                guest_response = GuestResponse.objects.get(short_code=token)
            except GuestResponse.DoesNotExist:
                pass
        
        # 3. Essayer par ID
        if not guest_response and token.isdigit():
            try:
                guest_response = GuestResponse.objects.get(id=int(token))
            except GuestResponse.DoesNotExist:
                pass
        
        if not guest_response:
            messages.error(request, _('Code invalide. Aucun invité trouvé.'))
            return redirect('guests:checkin_scan', event_id=0)
        
        self.guest_response = guest_response

        user = request.user
        event = self.guest_response.event
        is_organizer = (event.main_organizer == user)
        is_collaborator_with_scan = event.collaborators.filter(user=user, can_scan=True).exists()

        if not (is_organizer or is_collaborator_with_scan):
            messages.error(request, _("Vous n'avez pas l'autorisation de scanner pour cet événement."))
            return redirect('events:event_list')

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        guest = self.guest_response
        if guest.checkin_time:
            return render(request, self.template_name, {
                'guest': guest,
                'already_checked_in': True,
                'message': _("Cette invitation a déjà été scannée à {}.").format(
                    guest.checkin_time.strftime("%H:%M:%S")
                )
            })
        return render(request, self.template_name, {
            'guest': guest,
            'already_checked_in': False,
        })

    def post(self, request, *args, **kwargs):
        guest = self.guest_response
        if guest.checkin_time:
            messages.warning(request, _("Cette invitation a déjà été utilisée."))
            return redirect('guests:checkin', token=kwargs.get('token'))

        guest.checkin_time = timezone.now()
        guest.save(update_fields=['checkin_time'])

        table_number = guest.table.number if guest.table else _("non assignée")
        messages.success(request, _("Bienvenue {} ! Table {}.").format(guest.get_full_name(), table_number))

        return render(request, self.success_template, {
            'guest': guest,
            'table_number': table_number,
        })


# ============================================================
# 10. INVITATION PDF
# ============================================================

class InvitationPDFView(View):
    """Génère et télécharge l'invitation PDF."""

    def get(self, request, token):
        guest_response = get_object_or_404(GuestResponse, invitation_token=token)

        if not guest_response.submitted_at:
            messages.warning(request, _("Vous devez d'abord confirmer votre présence."))
            return redirect('guests:rsvp', token=token)

        pdf = generate_invitation_pdf(guest_response)
        if not pdf:
            messages.error(request, _("Impossible de générer l'invitation."))
            return redirect('events:event_detail', slug=guest_response.event.slug)

        filename = f"invitation_{guest_response.event.slug}_{guest_response.first_name}_{guest_response.last_name}.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class InvitationPreviewView(View):
    """Prévisualiser l'invitation PDF dans le navigateur."""

    def get(self, request, token):
        guest_response = get_object_or_404(GuestResponse, invitation_token=token)

        if request.user.is_authenticated:
            event = guest_response.event
            is_organizer = (event.main_organizer == request.user)
            is_collaborator = event.collaborators.filter(user=request.user, status='accepted').exists()
        else:
            is_organizer = False
            is_collaborator = False

        is_guest = (request.GET.get('email') == guest_response.email)

        if not (is_organizer or is_collaborator or is_guest):
            messages.error(request, _("Accès non autorisé."))
            return redirect('authentication:login')

        pdf = generate_invitation_pdf(guest_response)
        if not pdf:
            messages.error(request, _("Impossible de générer l'invitation."))
            return redirect('events:event_detail', slug=guest_response.event.slug)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="invitation_{guest_response.event.slug}.pdf"'
        return response


# ============================================================
# 11. AJOUT MANUEL D'UN INVITÉ PRÉ-ENREGISTRÉ
# ============================================================

class AddInvitedGuestView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Ajouter manuellement un invité à la liste officielle."""
    model = InvitedGuest
    form_class = InvitedGuestForm
    template_name = 'guests/add_guest.html'

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return self.request.user == self.event.main_organizer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context

    def form_valid(self, form):
        form.instance.event = self.event
        form.instance.created_by = self.request.user
        messages.success(self.request, _('Invité ajouté avec succès.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('guests:invited_list', kwargs={'event_id': self.event.id})


# ============================================================
# 12. LISTE DES INVITÉS PRÉ-ENREGISTRÉS (INVITED GUEST)
# ============================================================

class InvitedGuestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Liste des invités pré-enregistrés (InvitedGuest)."""
    model = InvitedGuest
    template_name = 'guests/invited_guest_list.html'
    context_object_name = 'invited_guests'
    paginate_by = 20

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs.get('event_id'))
        user = self.request.user
        return (self.event.main_organizer == user or
                self.event.collaborators.filter(user=user, status='accepted').exists())

    def get_paginate_by(self, queryset):
        per_page = self.request.GET.get('per_page')
        if per_page and per_page.isdigit():
            per_page = int(per_page)
            if per_page in [10, 15, 20, 30, 50, 100]:
                return per_page
        return getattr(settings, 'GUESTS_PER_PAGE', 20)

    def get_queryset(self):
        queryset = InvitedGuest.objects.filter(event=self.event)
        queryset = queryset.only(
            'id', 'first_name', 'last_name', 'middle_name',
            'email', 'phone', 'created_at', 'table_id'
        ).select_related('table')

        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        sort_by = self.request.GET.get('sort', 'last_name')
        if sort_by in ['first_name', 'last_name', 'email', 'created_at']:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('last_name', 'first_name')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event

        qs = InvitedGuest.objects.filter(event=self.event)
        context['total'] = qs.count()
        context['has_table'] = qs.filter(table__isnull=False).count()
        context['no_table'] = context['total'] - context['has_table']

        context['search_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'last_name')
        context['current_per_page'] = self.get_paginate_by(self.get_queryset())

        return context


# ============================================================
# 13. EXPORTS DES INVITÉS PRÉ-ENREGISTRÉS
# ============================================================

class ExportInvitedCSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Export CSV des invités pré-enregistrés."""

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return self.request.user == self.event.main_organizer

    def get(self, request, event_id):
        guests = InvitedGuest.objects.filter(event=self.event).order_by('last_name', 'first_name')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="invited_guests_{self.event.id}.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Prénom', 'Nom', 'Postnom', 'Email', 'Téléphone', 'Table'])
        for g in guests:
            writer.writerow([
                g.first_name, g.last_name, g.middle_name or '',
                g.email or '', g.phone or '',
                g.table.number if g.table else ''
            ])
        return response


class ExportInvitedExcelView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Export Excel des invités pré-enregistrés."""

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return self.request.user == self.event.main_organizer

    def get(self, request, event_id):
        from openpyxl import Workbook
        from openpyxl.styles import Font

        guests = InvitedGuest.objects.filter(event=self.event).order_by('last_name', 'first_name')
        wb = Workbook()
        ws = wb.active
        ws.title = "Invités"
        headers = ['Prénom', 'Nom', 'Postnom', 'Email', 'Téléphone', 'Table']
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header).font = Font(bold=True)
        for row, g in enumerate(guests, 2):
            ws.cell(row=row, column=1, value=g.first_name)
            ws.cell(row=row, column=2, value=g.last_name)
            ws.cell(row=row, column=3, value=g.middle_name or '')
            ws.cell(row=row, column=4, value=g.email or '')
            ws.cell(row=row, column=5, value=g.phone or '')
            ws.cell(row=row, column=6, value=g.table.number if g.table else '')
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="invited_guests_{self.event.id}.xlsx"'
        wb.save(response)
        return response


# ============================================================
# 14. ASSIGNATION MANUELLE D'UNE TABLE
# ============================================================

class AssignGuestTableView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vue pour assigner/déplacer un invité vers une table"""
    template_name = 'events/assign_guest_table.html'

    def test_func(self):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return self.request.user == self.event.main_organizer

    def get(self, request, event_id):
        guests = GuestResponse.objects.filter(
            event=self.event,
            will_attend=True
        ).select_related('table').order_by('first_name', 'last_name')
        
        tables = Table.objects.filter(event=self.event).order_by('number')
        
        context = {
            'event': self.event,
            'guests': guests,
            'tables': tables,
            'selected_guest_id': request.GET.get('guest_id'),
        }
        return render(request, self.template_name, context)

    def post(self, request, event_id):
        guest_id = request.POST.get('guest_id')
        table_id = request.POST.get('table_id')
        
        if not guest_id or not table_id:
            messages.error(request, _('Veuillez sélectionner un invité et une table.'))
            return redirect('events:assign_guest_table', event_id=event_id)
        
        try:
            guest = GuestResponse.objects.get(id=guest_id, event=self.event)
            table = Table.objects.get(id=table_id, event=self.event)
            
            if table.guests.count() >= table.capacity:
                messages.error(request, _('Cette table est pleine (capacité: {capacity}).').format(capacity=table.capacity))
                return redirect('events:assign_guest_table', event_id=event_id)
            
            old_table = guest.table
            guest.table = table
            guest.save()
            
            messages.success(
                request,
                _('{guest} a été déplacé(e) de la table {old} vers la table {new}.').format(
                    guest=guest.get_full_name(),
                    old=old_table.number if old_table else 'aucune',
                    new=table.number
                )
            )
        except GuestResponse.DoesNotExist:
            messages.error(request, _('Invité introuvable.'))
        except Table.DoesNotExist:
            messages.error(request, _('Table introuvable.'))
        
        return redirect('events:assign_guest_table', event_id=event_id)