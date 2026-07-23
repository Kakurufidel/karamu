import uuid
import secrets
import string
from datetime import datetime, timedelta
from urllib.parse import quote

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from apps.core.models import BaseModel


# ============================================================
# MODÈLE ÉVÉNEMENT
# ============================================================

class Event(BaseModel):
    """
    Modèle principal d'événement avec tokens pour RSVP et co-organisateurs
    """
    
    class EventType(models.TextChoices):
        WEDDING = 'wedding', _('Mariage')
        BIRTHDAY = 'birthday', _('Anniversaire')
        WEDDING_ANNIVERSARY = 'wedding_anniversary', _('Anniversaire de mariage')
        CORPORATE = 'corporate', _('Corporate')
        GRADUATION = 'graduation', _('Remise de diplôme')
        OTHER = 'other', _('Autre')
    
    # ========== ORGANISATEUR PRINCIPAL ==========
    main_organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_events',
        verbose_name=_('organisateur principal'),
        db_index=True,
    )
    
    # ========== INFORMATIONS ÉVÉNEMENT ==========
    name = models.CharField(_('nom'), max_length=200, db_index=True)
    event_type = models.CharField(
        _('type d\'événement'),
        max_length=30,
        choices=EventType.choices,
        db_index=True,
    )
    event_type_other = models.CharField(
        _('autre type'),
        max_length=100,
        blank=True,
    )
    description = models.TextField(_('description'), blank=True)
    
    # ========== DATE ET LIEU ==========
    date = models.DateField(_('date'), null=True, blank=True, db_index=True)
    time = models.TimeField(_('heure'), null=True, blank=True)
    location = models.CharField(_('lieu'), max_length=500)
    google_maps_link = models.URLField(_('lien Google Maps'), blank=True)
    
    # ========== OPTIONS ÉVÉNEMENT ==========
    dress_code = models.CharField(_('code vestimentaire'), max_length=200, blank=True)
    drink_options = models.JSONField(_('options de boissons'), default=list)
    reminder_message = models.TextField(_('message de rappel'), blank=True)
    sender_email = models.EmailField(_('email expéditeur'), default='noreply@kbfeven.com')
    
    # ========== MESSAGE D'INVITATION ==========
    invitation_message = models.TextField(
        _('message d\'invitation'),
        blank=True,
        help_text=_('Message personnalisé pour l\'invitation (ex: "Nous avons le plaisir de vous inviter à notre mariage...")')
    )
    
    # ========== GESTION DES BOISSONS ==========
    allow_other_drinks = models.BooleanField(
        _('autoriser "Autre" boisson'),
        default=True,
        help_text=_('Permettre aux invités de saisir une boisson personnalisée dans le formulaire RSVP')
    )
    
    # ========== GESTION DES TABLES ==========
    has_tables = models.BooleanField(
        _('nécessite des tables'),
        default=False,
        help_text=_('Cocher si cet événement nécessite une gestion des tables')
    )
    
    # ========== CHAMPS SPÉCIFIQUES SELON LE TYPE ==========
    # Mariage et Anniversaire de mariage
    groom_name = models.CharField(
        _('nom de l\'époux'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Nom complet de l\'époux (ex: Daniel Galleg)')
    )
    bride_name = models.CharField(
        _('nom de l\'épouse'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Nom complet de l\'épouse (ex: Cahaya Dewi)')
    )
    
    # Anniversaire
    celebrant_name = models.CharField(
        _('nom du célébrant'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Nom de la personne célébrée (ex: John Doe)')
    )
    celebrant_title = models.CharField(
        _('titre du célébrant'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Roi, Reine, Prince, Princesse, etc.')
    )
    
    # ========== TOKENS ET SLUG ==========
    rsvp_token = models.CharField(_('token RSVP'), max_length=36, unique=True, blank=True, db_index=True)
    coorganizer_token = models.CharField(_('token co-organisateur'), max_length=36, unique=True, blank=True, db_index=True)
    slug = models.SlugField(_('slug'), unique=True, max_length=200, blank=True, db_index=True)
    
    # ========== STATUT ==========
    is_published = models.BooleanField(_('publié'), default=False, db_index=True)
    
    # ========== PAIEMENT ET LIMITES ==========
    is_paid = models.BooleanField(_('payé'), default=False)
    max_guests_allowed = models.PositiveIntegerField(_('nombre max d\'invités'), default=400)
    max_collaborators_allowed = models.PositiveIntegerField(_('nombre max de co-organisateurs'), default=5)
    
    # ========== CODE COURT POUR CO-ORGANISATEUR ==========
    coorganizer_short_code = models.CharField(
        _('code court co-organisateur'),
        max_length=6,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )
    
    # ========== DESIGN ==========
    event_photo = models.ImageField(
        _('photo de l\'événement'),
        upload_to='event_photos/%Y/%m/%d/',
        blank=True,
        null=True,
    )
    event_color = models.CharField(
        _('couleur de l\'invitation'),
        max_length=20,
        default='#8B5CF6',
        help_text=_('Code couleur hexadécimal (ex: #8B5CF6)')
    )
    
    # ============================================================
    # MÉTADONNÉES
    # ============================================================
    
    class Meta:
        verbose_name = _('événement')
        verbose_name_plural = _('événements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['main_organizer', 'event_type']),
            models.Index(fields=['main_organizer', 'is_active']),
            models.Index(fields=['main_organizer', 'is_published']),
            models.Index(fields=['date', 'event_type']),
            models.Index(fields=['slug']),
            models.Index(fields=['rsvp_token']),
            models.Index(fields=['coorganizer_token']),
        ]
    
    def __str__(self):
        return self.name
    
    # ============================================================
    # MÉTHODES DE GÉNÉRATION
    # ============================================================
    
    def generate_uuid_token(self):
        return uuid.uuid4().hex[:12]
    
    def generate_coorganizer_short_code(self):
        """Génère un code court unique de 6 caractères"""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(6))
            if not Event.objects.filter(coorganizer_short_code=code).exists():
                return code
    
    # ============================================================
    # MÉTHODES DE SAUVEGARDE
    # ============================================================
    
    def save(self, *args, **kwargs):
        # Générer les tokens
        if not self.rsvp_token:
            self.rsvp_token = self.generate_uuid_token()
        if not self.coorganizer_token:
            self.coorganizer_token = self.generate_uuid_token()
        if not self.coorganizer_short_code:
            self.coorganizer_short_code = self.generate_coorganizer_short_code()
        
        # Générer le slug
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Si pas de tables, nettoyer les tables existantes
        if not self.has_tables and self.pk:
            self.tables.all().delete()
        
        super().save(*args, **kwargs)
    
    # ============================================================
    # PROPRIÉTÉS ET MÉTHODES
    # ============================================================
    
    @property
    def display_names(self):
        """Retourne les noms affichables selon le type d'événement"""
        if self.event_type in [self.EventType.WEDDING, self.EventType.WEDDING_ANNIVERSARY]:
            if self.groom_name and self.bride_name:
                return f"{self.bride_name} & {self.groom_name}"
            elif self.groom_name:
                return self.groom_name
            elif self.bride_name:
                return self.bride_name
        elif self.event_type == self.EventType.BIRTHDAY:
            if self.celebrant_name:
                if self.celebrant_title:
                    return f"{self.celebrant_title} {self.celebrant_name}"
                return self.celebrant_name
        return ""
    
    @property
    def display_title(self):
        """Titre de l'invitation selon le type d'événement"""
        titles = {
            self.EventType.WEDDING: _("Mariage"),
            self.EventType.WEDDING_ANNIVERSARY: _("Anniversaire de mariage"),
            self.EventType.BIRTHDAY: _("Anniversaire"),
            self.EventType.CORPORATE: _("Événement corporate"),
            self.EventType.GRADUATION: _("Remise de diplôme"),
            self.EventType.OTHER: _("Événement"),
        }
        return titles.get(self.event_type, _("Événement"))
    
    @property
    def invitation_text(self):
        """Retourne le message d'invitation ou un message par défaut selon le type"""
        if self.invitation_message:
            return self.invitation_message
        
        default_messages = {
            self.EventType.WEDDING: _("Nous avons le plaisir de vous inviter à notre mariage."),
            self.EventType.WEDDING_ANNIVERSARY: _("Nous célébrons notre anniversaire de mariage et serions ravis de votre présence."),
            self.EventType.BIRTHDAY: _("Nous fêtons un anniversaire et comptons sur votre présence."),
            self.EventType.CORPORATE: _("Nous vous invitons à notre événement corporate."),
            self.EventType.GRADUATION: _("Nous célébrons l'obtention d'un diplôme et vous invitons à partager ce moment."),
            self.EventType.OTHER: _("Vous êtes invité à notre événement."),
        }
        return default_messages.get(self.event_type, _("Vous êtes invité à notre événement."))
    
    @property
    def has_specific_names(self):
        """Vérifie si l'événement a des noms spécifiques (mariage, anniversaire)"""
        return bool(self.groom_name or self.bride_name or self.celebrant_name)
    
    def get_rsvp_url(self):
        return f'/events/{self.slug}/rsvp/{self.rsvp_token}/'

    def get_coorganizer_url(self):
        return f'/events/{self.slug}/join/{self.coorganizer_token}/'
    
    def get_google_calendar_link(self):
        if not self.date:
            return ""
        start_date = self.date.strftime("%Y%m%d")
        if self.time:
            start_date += f"T{self.time.strftime('%H%M%S')}"
        else:
            start_date += "T000000"
        end_date = self.date.strftime("%Y%m%d")
        if self.time:
            end_time = (datetime.combine(self.date, self.time) + timedelta(hours=2)).time()
            end_date += f"T{end_time.strftime('%H%M%S')}"
        else:
            end_date += "T020000"
        params = {
            'action': 'TEMPLATE',
            'text': f"Événement: {self.name}",
            'dates': f"{start_date}/{end_date}",
            'details': self.description or "",
            'location': self.location,
            'trp': 'false',
        }
        query_string = '&'.join([f'{k}={quote(str(v))}' for k, v in params.items()])
        return f"https://calendar.google.com/calendar/render?{query_string}"
    
    # ============================================================
    # STATISTIQUES
    # ============================================================
    
    def total_invited_guests(self):
        return self.invited_guests.filter(is_deleted=False).count()
    
    def total_responses(self):
        return self.responses.filter(is_deleted=False).count()
    
    def verified_responses(self):
        return self.responses.filter(is_deleted=False, verification_status='verified').count()
    
    def unverified_responses(self):
        return self.responses.filter(is_deleted=False, verification_status='unverified').count()
    
    def attendance_rate(self):
        verified = self.verified_responses()
        if verified == 0:
            return 0
        attending = self.responses.filter(
            is_deleted=False,
            verification_status='verified',
            will_attend=True
        ).count()
        return round((attending / verified) * 100, 1)
    
    def will_attend_count(self):
        return self.responses.filter(
            is_deleted=False,
            verification_status='verified',
            will_attend=True
        ).count()
    
    def total_expected_guests(self):
        total = 0
        for response in self.responses.filter(
            is_deleted=False,
            verification_status='verified',
            will_attend=True
        ):
            total += response.number_of_guests
        return total
    
    def has_tables_configured(self):
        """Vérifie si des tables existent pour cet événement"""
        return self.tables.filter(is_deleted=False).exists() if self.has_tables else False
    
    def get_drink_choices_with_other(self):
        """Retourne les choix de boissons avec ou sans l'option 'Autre'"""
        choices = [(drink, drink) for drink in self.drink_options]
        if self.allow_other_drinks:
            choices.append(('other', _('Autre')))
        return choices


# ============================================================
# MODÈLE CO-ORGANISATEUR
# ============================================================

class EventCollaborator(BaseModel):
    """
    Modèle pour les co-organisateurs d'un événement
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('En attente')
        ACCEPTED = 'accepted', _('Accepté')
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='collaborators',
        verbose_name=_('événement'),
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('utilisateur'),
        db_index=True,
    )
    invitation_token = models.CharField(
        _('token d\'invitation'),
        max_length=50,
        unique=True,
        db_index=True,
    )
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    can_scan = models.BooleanField(_('peut scanner'), default=False)

    invited_at = models.DateTimeField(_('invité le'), auto_now_add=True)
    accepted_at = models.DateTimeField(_('accepté le'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('co-organisateur')
        verbose_name_plural = _('co-organisateurs')
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.invitation_token:
            self.invitation_token = secrets.token_urlsafe(32)[:50]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.event.name}"
    
    def accept(self):
        """Accepte l'invitation"""
        self.status = self.Status.ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at'])


# ============================================================
# MODÈLE TABLE (SIMPLIFIÉ - SANS NUMBER)
# ============================================================

class Table(BaseModel):
    """
    Table pour un événement
    Le numéro de la table est son ID (auto-incrémenté)
    """
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='tables',
        verbose_name=_('événement'),
        db_index=True,
    )
    name = models.CharField(
        _('nom de la table'),
        max_length=100,
        blank=False,
        help_text=_('Nom de la table (ex: Table d\'honneur, Table 1, etc.)')
    )
    capacity = models.PositiveIntegerField(
        _('capacité'),
        default=8,
        help_text=_('Nombre maximum de personnes par table')
    )

    class Meta:
        verbose_name = _('table')
        verbose_name_plural = _('tables')
        ordering = ['id']
        indexes = [
            models.Index(fields=['event', 'id']),
        ]

    def __str__(self):
        return f"Table {self.id} - {self.name}"

    @property
    def number(self):
        """Retourne l'ID comme numéro de table"""
        return self.id

    @property
    def current_guests_count(self):
        """Nombre d'invités assignés à cette table"""
        from apps.guests.models import GuestResponse
        return GuestResponse.objects.filter(
            table=self,
            is_deleted=False,
            will_attend=True
        ).count()

    @property
    def is_full(self):
        """Vérifie si la table est pleine"""
        return self.current_guests_count >= self.capacity

    @property
    def display_name(self):
        """Nom affichable avec le numéro"""
        if self.name:
            return f"Table {self.id} - {self.name}"
        return f"Table {self.id}"
    
    def available_spots(self):
        """Nombre de places disponibles"""
        return max(0, self.capacity - self.current_guests_count)