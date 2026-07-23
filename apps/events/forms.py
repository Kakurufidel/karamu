from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Event, Table
from apps.guests.models import GuestResponse



class EventForm(forms.ModelForm):
    """
    Formulaire pour la création et modification d'un événement
    """
    
    drink_options_text = forms.CharField(
        label=_('Options de boissons'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Vin, Biere, Soft, Jus, Amarula...')
        }),
        help_text=_('Separez les boissons par des virgules')
    )
    
    event_color = forms.CharField(
        label=_('Couleur de l\'invitation'),
        required=False,
        initial='#8B5CF6',
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-input'
        })
    )
    
    class Meta:
        model = Event
        fields = [
            'name',
            'event_type',
            'event_type_other',
            'description',
            'date',
            'time',
            'location',
            'google_maps_link',
            'dress_code',
            'sender_email',
            'event_photo',
            'event_color',
            'groom_name',
            'bride_name',
            'celebrant_name',
            'celebrant_title',
            'invitation_message',
            'allow_other_drinks', 
            'has_tables',      
            'is_published',       
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _("Nom de l'evenement")
            }),
            'event_type': forms.Select(attrs={
                'class': 'form-input'
            }),
            'event_type_other': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Precisez le type')
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-input',
                'placeholder': _("Description de l'evenement")
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-input'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Adresse du lieu')
            }),
            'google_maps_link': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://maps.google.com/...'
            }),
            'dress_code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Code vestimentaire (optionnel)')
            }),
            'sender_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'noreply@example.com'
            }),
            'event_photo': forms.ClearableFileInput(attrs={
                'class': 'form-input'
            }),
            'groom_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _("Nom de l'epoux (ex: Daniel Galleg)")
            }),
            'bride_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _("Nom de l'epouse (ex: Cahaya Dewi)")
            }),
            'celebrant_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Nom du celebrant (ex: John Doe)')
            }),
            'celebrant_title': forms.Select(attrs={
                'class': 'form-input'
            }),
            'invitation_message': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-input',
                'placeholder': _('Message personnalise pour l\'invitation...')
            }),
            'allow_other_drinks': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'has_tables': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        labels = {
            'name': _('Nom de l\'evenement'),
            'event_type': _('Type d\'evenement'),
            'event_type_other': _('Autre type'),
            'description': _('Description'),
            'date': _('Date'),
            'time': _('Heure'),
            'location': _('Lieu'),
            'google_maps_link': _('Lien Google Maps'),
            'dress_code': _('Code vestimentaire'),
            'sender_email': _('Email expediteur'),
            'event_photo': _('Photo de l\'evenement'),
            'event_color': _('Couleur de l\'invitation'),
            'groom_name': _('Nom de l\'epoux'),
            'bride_name': _('Nom de l\'epouse'),
            'celebrant_name': _('Nom du celebrant'),
            'celebrant_title': _('Titre du celebrant'),
            'invitation_message': _('Message d\'invitation'),
            'allow_other_drinks': _('Autoriser "Autre" boisson'),
            'has_tables': _('Gestion des tables'),
            'is_published': _('Publier l\'evenement'),
        }
        help_texts = {
            'drink_options_text': _('Separez les boissons par des virgules'),
            'event_color': _('Choisissez la couleur de fond de l\'invitation'),
            'allow_other_drinks': _('Permettre aux invites de saisir une boisson personnalisee'),
            'has_tables': _('Activer la gestion des tables pour cet evenement'),
            'is_published': _('Les invites pourront voir l\'evenement une fois publie'),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Initialiser les champs avec les valeurs existantes
        if self.instance and self.instance.pk:
            if self.instance.drink_options:
                self.initial['drink_options_text'] = ', '.join(self.instance.drink_options)
            if self.instance.event_color:
                self.initial['event_color'] = self.instance.event_color
            if self.instance.groom_name:
                self.initial['groom_name'] = self.instance.groom_name
            if self.instance.bride_name:
                self.initial['bride_name'] = self.instance.bride_name
            if self.instance.celebrant_name:
                self.initial['celebrant_name'] = self.instance.celebrant_name
            if self.instance.celebrant_title:
                self.initial['celebrant_title'] = self.instance.celebrant_title
            if self.instance.invitation_message:
                self.initial['invitation_message'] = self.instance.invitation_message
            if self.instance.allow_other_drinks is not None:
                self.initial['allow_other_drinks'] = self.instance.allow_other_drinks
            if self.instance.has_tables is not None:
                self.initial['has_tables'] = self.instance.has_tables
            if self.instance.is_published is not None:
                self.initial['is_published'] = self.instance.is_published
        
        # Si c'est un nouvel evenement, utiliser l'email de l'utilisateur
        if user and not self.instance.pk:
            self.initial['sender_email'] = user.email
            self.initial['allow_other_drinks'] = True
            self.initial['has_tables'] = False
            self.initial['is_published'] = False
        
        # Rendre les champs optionnels par defaut
        optional_fields = [
            'event_type_other', 'description', 'google_maps_link',
            'dress_code', 'sender_email', 'event_photo', 'event_color',
            'groom_name', 'bride_name', 'celebrant_name', 'celebrant_title',
            'invitation_message'
        ]
        for field in optional_fields:
            self.fields[field].required = False
        
        # Ajouter les choices pour celebrant_title
        self.fields['celebrant_title'].choices = [
            ('', _('Selectionnez un titre')),
            ('Roi', _('Roi')),
            ('Reine', _('Reine')),
            ('Prince', _('Prince')),
            ('Princesse', _('Princesse')),
            ('Monsieur', _('Monsieur')),
            ('Madame', _('Madame')),
        ]

    def clean_event_type_other(self):
        event_type = self.cleaned_data.get('event_type')
        event_type_other = self.cleaned_data.get('event_type_other', '').strip()
        
        if event_type == 'other' and not event_type_other:
            raise ValidationError(_('Veuillez preciser le type d\'evenement.'))
        
        return event_type_other

    def clean(self):
        cleaned_data = super().clean()
        event_type = cleaned_data.get('event_type')
        
        # Validation des champs specifiques selon le type
        if event_type == 'wedding':
            groom = cleaned_data.get('groom_name')
            bride = cleaned_data.get('bride_name')
            if not groom:
                self.add_error('groom_name', _('Le nom de l\'epoux est requis pour un mariage.'))
            if not bride:
                self.add_error('bride_name', _('Le nom de l\'epouse est requis pour un mariage.'))
                
        elif event_type == 'wedding_anniversary':
            groom = cleaned_data.get('groom_name')
            bride = cleaned_data.get('bride_name')
            if not groom and not bride:
                self.add_error('groom_name', _('Au moins un des noms du couple est requis.'))
                
        elif event_type == 'birthday':
            celebrant = cleaned_data.get('celebrant_name')
            if not celebrant:
                self.add_error('celebrant_name', _('Le nom du celebrant est requis pour un anniversaire.'))
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Sauvegarder les boissons
        drink_text = self.cleaned_data.get('drink_options_text', '')
        if drink_text:
            instance.drink_options = [d.strip() for d in drink_text.split(',') if d.strip()]
        else:
            instance.drink_options = []
        
        # Sauvegarder la couleur
        instance.event_color = self.cleaned_data.get('event_color', '#8B5CF6')
        
        # Sauvegarder les champs booleens
        instance.allow_other_drinks = self.cleaned_data.get('allow_other_drinks', True)
        instance.has_tables = self.cleaned_data.get('has_tables', False)
        instance.is_published = self.cleaned_data.get('is_published', False)
        
        if commit:
            instance.save()
        
        return instance


# ============================================================
# FORMULAIRE TABLE
# ============================================================

class TableForm(forms.ModelForm):
    """
    Formulaire pour la création et modification d'une table
    Le numéro est automatique (ID), on ne le gère pas ici
    """
    
    class Meta:
        model = Table
        fields = ['name', 'capacity']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Ex: Table d\'honneur')
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 50,
                'placeholder': _('8')
            }),
        }
        labels = {
            'name': _('Nom de la table'),
            'capacity': _('Capacité'),
        }
        help_texts = {
            'name': _('Nom personnalisé pour identifier la table (ex: Table d\'honneur)'),
            'capacity': _('Nombre maximum de personnes par table'),
        }

    def clean_capacity(self):
        """Vérifie que la capacité est valide"""
        capacity = self.cleaned_data.get('capacity')
        
        if capacity is not None and capacity <= 0:
            raise ValidationError(_('La capacité doit être supérieure à 0.'))
        
        if capacity is not None and capacity > 50:
            raise ValidationError(_('La capacité ne peut pas dépasser 50 personnes.'))
        
        return capacity
class AssignTableForm(forms.Form):
    """Formulaire pour assigner un invité à une table"""
    
    guest_id = forms.ChoiceField(
        label=_('Invité'),
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )
    table_id = forms.ChoiceField(
        label=_('Nouvelle table'),
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        if event:
            # Récupérer les invités ayant confirmé leur présence
            guests = GuestResponse.objects.filter(
                event=event,
                will_attend=True,
                is_deleted=False
            ).select_related('table').order_by('last_name', 'first_name')
            
            guest_choices = [('', _('Sélectionnez un invité'))]
            for g in guests:
                table_info = f"table: {g.table.number if g.table else 'non assignee'}"
                label = f"{g.get_full_name()} ({table_info})"
                guest_choices.append((g.id, label))
            self.fields['guest_id'].choices = guest_choices
            
            # ✅ Récupérer les tables disponibles - utiliser 'id' pour le tri
            tables = Table.objects.filter(
                event=event,
                is_deleted=False
            ).order_by('id')  # ✅ Utiliser 'id' au lieu de '_number'
            
            table_choices = [('', _('Sélectionnez une table'))]
            for t in tables:
                current_count = t.current_guests_count
                status = "pleine" if t.is_full else f"{current_count}/{t.capacity}"
                # ✅ t.number est une propriété (lecture seule) - OK
                label = f"Table {t.number} - {t.name} ({status})"
                table_choices.append((t.id, label))
            self.fields['table_id'].choices = table_choices
    
    def clean(self):
        cleaned_data = super().clean()
        guest_id = cleaned_data.get('guest_id')
        table_id = cleaned_data.get('table_id')
        
        if not guest_id:
            self.add_error('guest_id', _('Veuillez sélectionner un invité.'))
        
        if not table_id:
            self.add_error('table_id', _('Veuillez sélectionner une table.'))
        
        return cleaned_data