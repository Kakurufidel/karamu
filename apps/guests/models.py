# apps/guests/models.py
import uuid
import unicodedata
import logging
import secrets
import string
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


class InvitedGuest(BaseModel):
    """
    Liste des invités pré-enregistrés par l'organisateur (import Excel).
    Ces personnes sont considérées comme des invités officiels.
    """
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='invited_guests',
        verbose_name=_('événement'),
        db_index=True,
    )
    first_name = models.CharField(_('prénom'), max_length=100, db_index=True)
    last_name = models.CharField(_('nom'), max_length=100, db_index=True)
    middle_name = models.CharField(_('postnom'), max_length=100, blank=True)
    email = models.EmailField(_('email'), blank=True, null=True, db_index=True)
    phone = models.CharField(_('téléphone'), max_length=20, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('créé par'),
        db_index=True,
    )
    table = models.ForeignKey(
        'events.Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_guests',
        verbose_name=_('table assignée'),
        db_index=True,
    )

    class Meta:
        verbose_name = _('invité pré-enregistré')
        verbose_name_plural = _('invités pré-enregistrés')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['event', 'last_name', 'first_name']),
            models.Index(fields=['event', 'email']),
            models.Index(fields=['event', 'is_deleted']),
            models.Index(fields=['event', 'table']),
        ]
        # ✅ Garder unique_together pour éviter les doublons
        unique_together = ['event', 'email']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.event.name})"

    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def normalize_name(text):
        """Normalise un nom pour la comparaison (sans accents, minuscule)"""
        if not text:
            return ""
        text = text.lower().strip()
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        return text

    @property
    def has_responded(self):
        """Vérifie si l'invité a déjà répondu au RSVP"""
        from .models import GuestResponse
        if self.email:
            return GuestResponse.objects.filter(
                event=self.event,
                email=self.email,
                is_deleted=False
            ).exists()
        return GuestResponse.objects.filter(
            event=self.event,
            first_name__iexact=self.first_name,
            last_name__iexact=self.last_name,
            is_deleted=False
        ).exists()


class GuestResponse(BaseModel):
    """
    Réponse d'un invité (RSVP) via le formulaire public.
    """
    
    class DrinkChoice(models.TextChoices):
        VIN = 'vin', _('Vin')
        BIERE = 'biere', _('Bière')
        SOFT = 'soft', _('Soft')
        JUS = 'jus', _('Jus')
        EAU = 'eau', _('Eau')
        OTHER = 'other', _('Autre')
    
    class VerificationStatus(models.TextChoices):
        VERIFIED = 'verified', _('Vérifié - Invité officiel')
        UNVERIFIED = 'unverified', _('Non vérifié')
    
    # ========== RELATIONS ==========
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_('événement'),
        db_index=True,
    )
    
    # ========== INFORMATIONS RÉPONDANT ==========
    first_name = models.CharField(_('prénom'), max_length=100, db_index=True)
    last_name = models.CharField(_('nom'), max_length=100, db_index=True)
    email = models.EmailField(_('email'), db_index=True)
    phone = models.CharField(_('téléphone'), max_length=20, blank=True)
    
    # ========== RÉPONSE ==========
    will_attend = models.BooleanField(_('sera présent(e)'), default=True, db_index=True)
    number_of_guests = models.PositiveIntegerField(_('nombre de personnes'), default=1)
    
    # ========== ACCOMPAGNEMENT ==========
    is_accompanied = models.BooleanField(_('accompagné(e)'), default=False)
    companion_name = models.CharField(_('nom de l\'accompagnant'), max_length=200, blank=True)
    companion_first_name = models.CharField(_('prénom accompagnant'), max_length=100, blank=True)
    companion_last_name = models.CharField(_('nom accompagnant'), max_length=100, blank=True)
    
    # ========== BOISSONS ==========
    drink_choice = models.CharField(
        _('choix de boisson'),
        max_length=20,
        choices=DrinkChoice.choices,
        blank=True,
    )
    drink_other = models.CharField(_('autre boisson'), max_length=100, blank=True)
    companion_drink_choice = models.CharField(
        _('boisson accompagnant'),
        max_length=20,
        choices=DrinkChoice.choices,
        blank=True,
    )
    companion_drink_other = models.CharField(_('autre boisson accompagnant'), max_length=100, blank=True)
    
    # ========== VÉGÉTARIEN / NOTES ==========
    is_vegan = models.BooleanField(_('végétarien/végétalien'), default=False)
    special_notes = models.TextField(_('notes spéciales'), blank=True)
    
    # ========== VÉRIFICATION ==========
    verification_status = models.CharField(
        _('statut de vérification'),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
        db_index=True,
    )
    
    # ========== MÉTADONNÉES ==========
    submitted_at = models.DateTimeField(_('soumis le'), auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(_('adresse IP'), null=True, blank=True)
    
    # ========== RAPPELS ==========
    reminder_sent = models.BooleanField(_('rappel envoyé'), default=False)
    reminder_sent_at = models.DateTimeField(_('rappel envoyé le'), null=True, blank=True)
    
    # ========== TOKEN ==========
    invitation_token = models.UUIDField(
        _('token invitation'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    
    # ========== CHECK-IN / TABLES ==========
    checkin_time = models.DateTimeField(_('heure d\'arrivée'), null=True, blank=True, db_index=True)
    is_excess = models.BooleanField(_('excédent'), default=False)
    short_code = models.CharField(_('code court'), max_length=5, unique=True, null=True, blank=True, db_index=True)
    table = models.ForeignKey(
        'events.Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guests',
        verbose_name=_('table assignée'),
        db_index=True,
    )
    
    class Meta:
        verbose_name = _('réponse d\'invité')
        verbose_name_plural = _('réponses des invités')
        ordering = ['-submitted_at']
        # ✅ Garder unique_together
        unique_together = ['event', 'email']
        indexes = [
            models.Index(fields=['event', 'verification_status']),
            models.Index(fields=['event', 'will_attend']),
            models.Index(fields=['event', 'checkin_time']),
            models.Index(fields=['event', 'table']),
            models.Index(fields=['short_code']),
            models.Index(fields=['event', 'is_deleted']),
            # ✅ Index combiné pour les requêtes fréquentes
            models.Index(fields=['event', 'verification_status', 'will_attend']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.event.name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_companion_full_name(self):
        if self.companion_first_name and self.companion_last_name:
            return f"{self.companion_first_name} {self.companion_last_name}"
        return self.companion_name or ""

    @staticmethod
    def normalize_name(text):
        """Normalise un nom pour la comparaison (sans accents, minuscule)"""
        if not text:
            return ""
        text = text.lower().strip()
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        return text

    def generate_short_code(self):
        """Génère un code court unique de 5 caractères"""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(5))
            if not GuestResponse.objects.filter(event=self.event, short_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        """Sauvegarde avec génération automatique du code court"""
        if not self.short_code:
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)

    def verify_against_invited_list(self):
        """
        Vérifie si cette réponse correspond à un invité pré-enregistré.
        Si correspondance, copie la table de InvitedGuest vers GuestResponse.
        """
        normalized_first = self.normalize_name(self.first_name)
        normalized_last = self.normalize_name(self.last_name)
        
        # ✅ Optimisation : utiliser select_related pour charger les tables en une seule requête
        invited_guests = self.event.invited_guests.select_related('table').filter(is_deleted=False)
        
        # Vérification par nom
        for invited in invited_guests.iterator():
            if (self.normalize_name(invited.first_name) == normalized_first and
                self.normalize_name(invited.last_name) == normalized_last):
                self.verification_status = 'verified'
                if invited.table and not self.table:
                    self.table = invited.table
                self.save(update_fields=['verification_status', 'table'])
                logger.info(f"Réponse vérifiée: {self.get_full_name()} - Table: {self.table.id if self.table else 'Aucune'}")
                return True
        
        # ✅ Vérification par email (optimisée avec un filtre)
        if self.email:
            invited_by_email = invited_guests.filter(email__iexact=self.email).first()
            if invited_by_email:
                self.verification_status = 'verified'
                if invited_by_email.table and not self.table:
                    self.table = invited_by_email.table
                self.save(update_fields=['verification_status', 'table'])
                logger.info(f"Réponse vérifiée par email: {self.get_full_name()}")
                return True
        
        logger.warning(f"Réponse non vérifiée: {self.get_full_name()}")
        return False

    def send_confirmation_email(self):
        """Envoie l'email de confirmation (désactivé temporairement)"""
        return True

    def send_reminder(self):
        """Envoie un email de rappel (désactivé temporairement)"""
        if self.reminder_sent:
            return False
        self.reminder_sent = True
        self.reminder_sent_at = timezone.now()
        self.save(update_fields=['reminder_sent', 'reminder_sent_at'])
        return True

    def get_invitation_link(self, request=None):
        """Lien pour télécharger l'invitation PDF"""
        if request:
            return request.build_absolute_uri(
                reverse('guests:invitation_pdf', args=[str(self.invitation_token)])
            )
        return reverse('guests:invitation_pdf', args=[str(self.invitation_token)])

    # ============================================================
    # PROPRIÉTÉS
    # ============================================================
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'
    
    @property
    def drink_display(self):
        if self.drink_choice == 'other':
            return self.drink_other or "Autre"
        return self.get_drink_choice_display() or "Non spécifié"
    
    @property
    def companion_drink_display(self):
        if self.companion_drink_choice == 'other':
            return self.companion_drink_other or "Autre"
        return self.get_companion_drink_choice_display() or "Non spécifié"

    @property
    def has_checked_in(self):
        return self.checkin_time is not None

    @property
    def is_pending(self):
        return self.verification_status == 'unverified' and not self.will_attend