from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import FormView, TemplateView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Q, Count, Sum
from .forms import LoginForm, RegisterForm
from apps.events.models import Event, EventCollaborator
from apps.guests.models import GuestResponse


class HomeView(TemplateView):
    """Page d'accueil - redirige vers le dashboard si connecté"""
    template_name = 'landing.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('events:event_list')
        return super().get(request, *args, **kwargs)


def redirect_after_auth(request, user):
    """
    Fonction utilitaire pour rediriger après authentification.
    Si un code co-organisateur est fourni, redirige vers l'événement correspondant
    et ajoute l'utilisateur comme co-organisateur.
    """
    coorganizer_code = request.POST.get('coorganizer_code')
    if coorganizer_code:
        try:
            event = Event.objects.get(coorganizer_short_code=coorganizer_code.upper())
            
            # Ajouter l'utilisateur comme co-organisateur
            collaborator, created = EventCollaborator.objects.get_or_create(
                event=event,
                user=user,
                defaults={'status': 'accepted', 'accepted_at': timezone.now()}
            )
            if not created and collaborator.status == 'pending':
                collaborator.status = 'accepted'
                collaborator.accepted_at = timezone.now()
                collaborator.save()
            
            messages.success(
                request, 
                _('Vous êtes maintenant co-organisateur de l\'événement "%s".') % event.name
            )
            return redirect('events:event_detail', slug=event.slug)
        except Event.DoesNotExist:
            messages.warning(request, _('Le code co-organisateur est invalide.'))
    
    # Sinon, rediriger vers la liste des événements
    return redirect('events:event_list')


class LoginView(FormView):
    template_name = 'authentication/login.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('events:event_list')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        coorganizer_code = self.request.GET.get('coorganizer_code')
        if coorganizer_code:
            initial['coorganizer_code'] = coorganizer_code
        return initial

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        messages.success(
            self.request, 
            _('Bon retour parmis nous, %(name)s !') % {'name': user.first_name}
        )
        return redirect_after_auth(self.request, user)

    def form_invalid(self, form):
        messages.error(self.request, _('Email ou mot de passe incorrect.'))
        return super().form_invalid(form)


class RegisterView(FormView):
    template_name = 'authentication/register.html'
    form_class = RegisterForm

    def get_initial(self):
        initial = super().get_initial()
        coorganizer_code = self.request.GET.get('coorganizer_code')
        if coorganizer_code:
            initial['coorganizer_code'] = coorganizer_code
        return initial

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('events:event_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _('Bienvenue ! Votre compte a été créé avec succès.'))
        
        return redirect('events:event_list')

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

class LogoutView(View):
    """Vue de déconnexion"""

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, _('Vous avez été déconnecté avec succès.'))
        return redirect(reverse('authentication:home'))


class ContactView(View):
    """Vue pour traiter le formulaire de contact"""

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not email or not message:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect(reverse('authentication:home') + '#contact')

        messages.success(
            request,
            f"Merci {name} ! Votre message a bien été envoyé. Nous vous répondrons dans les plus brefs délais."
        )

        return redirect(reverse('authentication:home') + '#contact')

    def get(self, request, *args, **kwargs):
        return redirect('authentication:home')


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Tableau de bord de l'utilisateur
    Affiche les statistiques des événements dont l'utilisateur est
    organisateur principal ou co-organisateur
    """
    template_name = 'authentication/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # ============================================================
        # Événements dont l'utilisateur est l'organisateur principal
        # ============================================================
        owned_events = Event.objects.filter(
            main_organizer=user,
            is_deleted=False  # ✅ Filtrer les événements non supprimés
        )
        is_organizer = owned_events.exists()

        # ============================================================
        # Co-organisateurs des événements dont il est main_organizer
        # ============================================================
        collaborators = EventCollaborator.objects.filter(
            event__main_organizer=user,
            status='accepted',
            is_deleted=False  # ✅ Filtrer les collaborateurs non supprimés
        ).select_related('user')

        # ============================================================
        # Événements où l'utilisateur est co-organisateur (et non main_organizer)
        # ============================================================
        coorganized_events = Event.objects.filter(
            collaborators__user=user,
            collaborators__status='accepted',
            is_deleted=False  # ✅ Filtrer les événements non supprimés
        ).exclude(main_organizer=user)

        # ============================================================
        # Tous les événements où l'utilisateur est impliqué
        # ============================================================
        all_events = (owned_events | coorganized_events).distinct()

        # ============================================================
        # Statistiques globales
        # ============================================================
        total_guests = 0
        total_responses = 0
        total_attending = 0
        total_verified = 0
        
        # Récupérer les GuestResponse pour les événements de l'utilisateur
        # ✅ Filtrer les GuestResponse non supprimées
        responses = GuestResponse.objects.filter(
            event__in=all_events,
            is_deleted=False  # ✅ Filtrer les réponses non supprimées
        )
        
        # Compter les invités pré-enregistrés (InvitedGuest)
        for event in all_events:
            total_guests += event.invited_guests.filter(is_deleted=False).count()  # ✅ Filtrer les invités non supprimés
        
        total_responses = responses.count()
        total_attending = responses.filter(will_attend=True).count()
        total_verified = responses.filter(verification_status='verified').count()
        
        # Taux de présence (basé sur les réponses vérifiées)
        attendance_rate = 0
        if total_verified > 0:
            attending_verified = responses.filter(
                will_attend=True, 
                verification_status='verified'
            ).count()
            attendance_rate = round((attending_verified / total_verified) * 100, 1)

        # ============================================================
        # Statistiques par événement (pour le template)
        # ============================================================
        events_stats = []
        for event in all_events:
            event_responses = responses.filter(event=event)
            event_guests = event.invited_guests.filter(is_deleted=False).count()
            
            events_stats.append({
                'event': event,
                'total_guests': event_guests,
                'total_responses': event_responses.count(),
                'will_attend': event_responses.filter(will_attend=True).count(),
                'verified': event_responses.filter(verification_status='verified').count(),
            })

        context.update({
            'events': all_events,
            'total_events': all_events.count(),
            'owned_events': owned_events,
            'coorganized_events': coorganized_events,
            'collaborators': collaborators,
            'total_guests': total_guests,
            'total_responses': total_responses,
            'total_attending': total_attending,
            'total_verified': total_verified,
            'attendance_rate': attendance_rate,
            'events_stats': events_stats,
            'is_organizer': is_organizer,
        })
        return context