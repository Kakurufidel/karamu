from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DrinkPackaging


class DrinkPackagingForm(forms.ModelForm):
    """Formulaire pour créer/modifier un conditionnement de boisson"""
    
    class Meta:
        model = DrinkPackaging
        fields = ['drink_name', 'pieces_per_case', 'price_per_case', 'is_active']
        widgets = {
            'drink_name': forms.Select(attrs={
                'class': 'form-input',
            }),
            'pieces_per_case': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'placeholder': '12'
            }),
            'price_per_case': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0,
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        labels = {
            'drink_name': _('Boisson'),
            'pieces_per_case': _('Pièces par casier'),
            'price_per_case': _('Prix par casier'),
            'is_active': _('Actif'),
        }
        help_texts = {
            'pieces_per_case': _('Nombre de bouteilles/pièces dans un casier (ex: 12)'),
            'price_per_case': _('Prix d\'un casier complet'),
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        if self.event:
            drink_options = self.event.drink_options or []
            choices = [('', _('-- Sélectionnez --'))]
            for drink in drink_options:
                if drink:
                    choices.append((drink, drink))
            self.fields['drink_name'].choices = choices


class EstimationSettingsForm(forms.Form):
    """Formulaire pour les paramètres d'estimation"""
    
    currency = forms.ChoiceField(
        label=_('Devise'),
        choices=[('CDF', 'Franc Congolais (CDF)'), ('USD', 'Dollar Américain (USD)')],
        initial='CDF',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    margin_percentage = forms.IntegerField(
        label=_('Marge (%)'),
        required=False,
        min_value=0,
        max_value=100,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'min': 0,
            'max': 100,
            'placeholder': '0'
        })
    )
    
    include_pending = forms.BooleanField(
        label=_('Inclure les en attente'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    
    pending_rate = forms.IntegerField(
        label=_('Taux présence (%)'),
        required=False,
        min_value=0,
        max_value=100,
        initial=75,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'min': 0,
            'max': 100,
            'placeholder': '75'
        })
    )
    
    number_of_services = forms.IntegerField(
        label=_('Tournées'),
        required=False,
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'min': 1,
            'max': 10,
            'placeholder': '1'
        })
    )