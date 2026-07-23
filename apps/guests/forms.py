from django import forms
from django.utils.translation import gettext_lazy as _
from .models import GuestResponse, InvitedGuest


class StrictSelect(forms.Select):
    """Select qui n'accepte que les valeurs valides, mais qui permet 'other'"""
    pass


class RSVPForm(forms.ModelForm):
    """Formulaire public pour répondre à une invitation"""
    
    # ===== CHAMPS PERSONNALISÉS =====
    # Au lieu d'utiliser le champ du modèle, on utilise un champ qui accepte tout
    drink_choice = forms.ChoiceField(
        choices=[],  # Sera rempli dans __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    companion_drink_choice = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = GuestResponse
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'will_attend', 'number_of_guests',
            'is_accompanied',
            'drink_other',  # drink_choice est géré manuellement
            'companion_drink_other',
            'is_vegan', 'special_notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre nom'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'votre@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+243 XX XXX XXX'
            }),
            'will_attend': forms.RadioSelect(
                choices=[(True, 'Oui, je serai présent(e)'), (False, 'Non, je ne pourrai pas venir')]
            ),
            'number_of_guests': forms.NumberInput(attrs={
                'class': 'form-input w-20',
                'min': 1,
                'max': 20
            }),
            'drink_other': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Whisky, Jus...'
            }),
            'companion_drink_other': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Whisky, Jus...'
            }),
            'is_accompanied': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'is_vegan': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'special_notes': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 2,
                'placeholder': 'Allergies, besoins...'
            }),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Email',
            'phone': 'Téléphone',
            'will_attend': 'Souhaitez-vous participer ?',
            'number_of_guests': 'Nombre de personnes',
            'drink_other': 'Précisez votre boisson',
            'companion_drink_other': 'Précisez la boisson',
            'is_accompanied': 'Je serai accompagné(e)',
            'is_vegan': 'Option végétarienne/végétalienne',
            'special_notes': 'Notes spéciales',
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        # Rendre les champs optionnels
        self.fields['phone'].required = False
        self.fields['drink_other'].required = False
        self.fields['companion_drink_other'].required = False
        self.fields['is_accompanied'].required = False
        self.fields['is_vegan'].required = False
        self.fields['special_notes'].required = False
        
        # Personnaliser les choix de boissons
        if self.event and self.event.drink_options:
            choices = [('', 'Sélectionnez')]
            choices.extend([(d, d) for d in self.event.drink_options])
            choices.append(('other', 'Autre'))
            self.fields['drink_choice'].choices = choices
            self.fields['companion_drink_choice'].choices = choices
        
        # Si l'instance existe déjà, pré-remplir les champs
        if self.instance and self.instance.pk:
            if self.instance.drink_choice:
                self.fields['drink_choice'].initial = self.instance.drink_choice
                if self.instance.drink_choice == 'other' and self.instance.drink_other:
                    self.fields['drink_other'].initial = self.instance.drink_other
            if self.instance.companion_drink_choice:
                self.fields['companion_drink_choice'].initial = self.instance.companion_drink_choice
                if self.instance.companion_drink_choice == 'other' and self.instance.companion_drink_other:
                    self.fields['companion_drink_other'].initial = self.instance.companion_drink_other
    
    def clean_drink_choice(self):
        """Accepter n'importe quelle valeur, la valider plus tard"""
        return self.cleaned_data.get('drink_choice')
    
    def clean_companion_drink_choice(self):
        """Accepter n'importe quelle valeur, la valider plus tard"""
        return self.cleaned_data.get('companion_drink_choice')
    
    def clean(self):
        """Validation principale"""
        cleaned_data = super().clean()
        will_attend = cleaned_data.get('will_attend')
        
        if will_attend:
            # === Gestion de la boisson ===
            drink = cleaned_data.get('drink_choice')
            drink_other = cleaned_data.get('drink_other', '')
            available_choices = [choice[0] for choice in self.fields['drink_choice'].choices]
            
            # Si la boisson est vide
            if not drink or drink == '':
                self.add_error('drink_choice', 'Veuillez choisir une boisson')
            # Si la boisson n'est pas dans la liste, on la traite comme "Autre"
            elif drink not in available_choices:
                cleaned_data['drink_other'] = drink
                cleaned_data['drink_choice'] = 'other'
            # Si "Autre" est sélectionné
            elif drink == 'other':
                if not drink_other:
                    self.add_error('drink_other', 'Veuillez préciser votre boisson')
            
            # === Nombre de personnes ===
            number = cleaned_data.get('number_of_guests')
            if not number or number < 1:
                self.add_error('number_of_guests', 'Veuillez indiquer le nombre de personnes')
            
            # === Boisson de l'accompagnant ===
            if cleaned_data.get('is_accompanied'):
                companion_drink = cleaned_data.get('companion_drink_choice')
                companion_drink_other = cleaned_data.get('companion_drink_other', '')
                available_companion_choices = [choice[0] for choice in self.fields['companion_drink_choice'].choices]
                
                if not companion_drink or companion_drink == '':
                    self.add_error('companion_drink_choice', 'Veuillez choisir une boisson pour l\'accompagnant')
                elif companion_drink not in available_companion_choices:
                    cleaned_data['companion_drink_other'] = companion_drink
                    cleaned_data['companion_drink_choice'] = 'other'
                elif companion_drink == 'other':
                    if not companion_drink_other:
                        self.add_error('companion_drink_other', 'Veuillez préciser la boisson de l\'accompagnant')
        
        # Vérifier l'email en double
        email = cleaned_data.get('email')
        if email and self.event and self.event.pk:
            qs = GuestResponse.objects.filter(event=self.event, email=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('email', 'Cet email a déjà répondu à cette invitation')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.event = self.event
        
        # Gestion des boissons
        drink = self.cleaned_data.get('drink_choice')
        if drink == 'other':
            instance.drink_choice = 'other'
            instance.drink_other = self.cleaned_data.get('drink_other', '')
        elif drink and drink != '':
            # Vérifier si c'est une valeur valide
            available_choices = [choice[0] for choice in self.fields['drink_choice'].choices]
            if drink in available_choices and drink != 'other':
                instance.drink_choice = drink
                instance.drink_other = ''
            else:
                # Si ce n'est pas valide, on le met dans other
                instance.drink_choice = 'other'
                instance.drink_other = drink
        else:
            instance.drink_choice = ''
            instance.drink_other = ''
        
        # Gestion de la boisson de l'accompagnant
        companion_drink = self.cleaned_data.get('companion_drink_choice')
        if companion_drink == 'other':
            instance.companion_drink_choice = 'other'
            instance.companion_drink_other = self.cleaned_data.get('companion_drink_other', '')
        elif companion_drink and companion_drink != '':
            available_companion_choices = [choice[0] for choice in self.fields['companion_drink_choice'].choices]
            if companion_drink in available_companion_choices and companion_drink != 'other':
                instance.companion_drink_choice = companion_drink
                instance.companion_drink_other = ''
            else:
                instance.companion_drink_choice = 'other'
                instance.companion_drink_other = companion_drink
        else:
            instance.companion_drink_choice = ''
            instance.companion_drink_other = ''
        
        if commit:
            instance.save()
            instance.verify_against_invited_list()
            instance.send_confirmation_email()
        
        return instance


class InvitedGuestForm(forms.ModelForm):
    """Formulaire pour ajouter manuellement un invité pré-enregistré"""
    
    class Meta:
        model = InvitedGuest
        fields = ['first_name', 'last_name', 'middle_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postnom (optionnel)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+243 XXX XXX XXX'
            }),
        }


class GuestBulkImportForm(forms.Form):
    """Formulaire pour importer un fichier Excel d'invités"""
    excel_file = forms.FileField(
        label=_('Fichier Excel'),
        help_text=_('Format attendu: Prénom, Nom, Postnom (optionnel), Email, Téléphone, Table (optionnel)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx, .xls, .csv'
        })
    )