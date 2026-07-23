from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.core.models import BaseModel

class DrinkPackaging(BaseModel):
    """
    Conditionnement d'une boisson pour un événement
    Un casier/pack contient X pièces/bouteilles
    """
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='drink_packagings',
        verbose_name=_('événement'),
        db_index=True,
    )
    drink_name = models.CharField(
        _('nom de la boisson'),
        max_length=100,
        db_index=True,
        help_text=_('Ex: 33export, Vin rouge, Coca-Cola')
    )
    pieces_per_case = models.PositiveIntegerField(
        _('pièces par casier'),
        default=12,
        help_text=_('Nombre de bouteilles/pièces par casier/pack (ex: 12)')
    )
    price_per_case = models.DecimalField(
        _('prix par casier'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Prix d\'un casier complet')
    )
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('conditionnement de boisson')
        verbose_name_plural = _('conditionnements de boissons')
        ordering = ['drink_name']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'drink_name'],
                condition=models.Q(is_active=True),
                name='unique_active_drink_packaging'
            )
        ]
        indexes = [
            models.Index(fields=['event', 'is_active']),
            models.Index(fields=['event', 'drink_name']),
        ]

    def __str__(self):
        return f"{self.drink_name} - {self.pieces_per_case} pièces/casier"

    def unit_price(self):
        """Prix unitaire par pièce/bouteille"""
        if self.pieces_per_case > 0:
            return self.price_per_case / self.pieces_per_case
        return Decimal('0')
    
    def get_cases_needed(self, pieces_needed):
        """Calcule le nombre de casiers nécessaires"""
        if pieces_needed <= 0:
            return 0
        return (pieces_needed + self.pieces_per_case - 1) // self.pieces_per_case
    
    def get_total_cost(self, pieces_needed):
        """Calcule le coût total"""
        if pieces_needed <= 0:
            return Decimal('0')
        cases_needed = self.get_cases_needed(pieces_needed)
        return cases_needed * self.price_per_case
    
    @property
    def display_name(self):
        return f"{self.drink_name} ({self.pieces_per_case} pièces/casier)"


# ALIAS pour compatibilité
BeveragePack = DrinkPackaging

class EventForecast(BaseModel):
    """Prévisions de l'organisateur pour son événement"""
    event = models.OneToOneField(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='forecast',
        verbose_name=_('événement'),
    )
    total_guests_expected = models.PositiveIntegerField(
        _('total invités prévus'),
        default=0,
        help_text=_('Nombre total d\'invités prévus (basé sur l\'import Excel)')
    )
    attendance_rate = models.PositiveIntegerField(
        _('taux de présence (%)'),
        default=75,
        help_text=_('Pourcentage estimé de personnes qui viendront')
    )
    number_of_services = models.PositiveIntegerField(
        _('nombre de tournées'),
        default=1,
        help_text=_('1 tournée = 1 boisson par personne')
    )
    currency = models.CharField(
        _('devise'),
        max_length=3,
        choices=[('CDF', 'Franc Congolais'), ('USD', 'Dollar Américain')],
        default='CDF'
    )
    drink_forecast = models.JSONField(
        _('prévisions par boisson'),
        default=list,
        help_text=_('Liste des prévisions par boisson')
    )
    # Exemple de drink_forecast:
    # [
    #   {"name": "33export", "percentage": 40, "pieces_per_case": 12, "price_per_case": 25000},
    #   {"name": "Vin", "percentage": 30, "pieces_per_case": 6, "price_per_case": 35000}
    # ]
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('prévision')
        verbose_name_plural = _('prévisions')

    def __str__(self):
        return f"Prévisions - {self.event.name}"

    def calculate_forecast(self):
        """
        Calcule les besoins en fonction des prévisions
        Retourne les données enrichies avec les calculs
        """
        if not self.drink_forecast:
            return []
        
        total_guests = self.total_guests_expected
        attendance = total_guests * (self.attendance_rate / 100)
        total_with_services = attendance * self.number_of_services
        
        results = []
        for item in self.drink_forecast:
            percentage = item.get('percentage', 0)
            people = (percentage / 100) * total_with_services
            pieces_per_case = item.get('pieces_per_case', 12)
            price_per_case = item.get('price_per_case', 0)
            
            cases = (people + pieces_per_case - 1) // pieces_per_case
            cost = cases * price_per_case
            
            results.append({
                'name': item.get('name', ''),
                'percentage': percentage,
                'people': int(people),
                'pieces_per_case': pieces_per_case,
                'cases': int(cases),
                'price_per_case': price_per_case,
                'cost': cost,
            })
        
        return results
    
    def get_total_cost(self):
        """Retourne le coût total estimé"""
        forecast = self.calculate_forecast()
        return sum(item['cost'] for item in forecast)
    
