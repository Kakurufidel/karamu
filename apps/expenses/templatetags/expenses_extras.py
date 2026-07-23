from django import template
from django.utils.translation import gettext as _
from decimal import Decimal

register = template.Library()


@register.filter
def currency(value):
    """Formate un nombre en devise"""
    if value is None:
        return '0,00 €'
    try:
        return f'{Decimal(value):.2f} €'
    except:
        return str(value)


@register.filter
def percentage(value, total):
    """Calcule le pourcentage"""
    if not total:
        return 0
    try:
        return round((value / total) * 100, 1)
    except:
        return 0


@register.filter
def multiply(value, arg):
    """Multiplie deux valeurs"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except:
        return 0


@register.filter
def divide(value, arg):
    """Divise deux valeurs"""
    try:
        if arg:
            return Decimal(str(value)) / Decimal(str(arg))
        return 0
    except:
        return 0


@register.filter
def get_choice_label(choice_value):
    """Retourne le libellé d'un choix de boisson"""
    choices = {
        'coca': _('Coca-Cola'),
        'fanta': _('Fanta'),
        'sprite': _('Sprite'),
        'simba': _('Simba'),
        'amarula': _('Amarula'),
        'juice': _('Jus'),
        'water': _('Eau'),
        'beer': _('Bière'),
        'wine': _('Vin'),
        'champagne': _('Champagne'),
        'whisky': _('Whisky'),
        'other': _('Autre'),
    }
    return choices.get(choice_value, choice_value)


@register.simple_tag
def get_pack_count(event):
    """Retourne le nombre de packs configurés pour un événement"""
    from apps.expenses.models import BeveragePack
    return BeveragePack.objects.filter(event=event, is_active=True).count()


@register.filter
def is_empty(value):
    """Vérifie si une liste ou un dict est vide"""
    if value is None:
        return True
    if hasattr(value, '__len__'):
        return len(value) == 0
    return not bool(value)


@register.filter
def has_other_choices(estimation):
    """Vérifie s'il y a des boissons 'autres' non configurées"""
    if not estimation:
        return False
    details = estimation.get('details', [])
    return any(item.get('is_other', False) for item in details)


@register.filter
def get_active_packs(packs):
    """Filtre les packs actifs"""
    return [p for p in packs if p.is_active]


@register.filter
def get_inactive_packs(packs):
    """Filtre les packs inactifs"""
    return [p for p in packs if not p.is_active]


@register.simple_tag
def total_guests_with_drinks(event):
    """Nombre total d'invités ayant choisi une boisson"""
    from apps.guests.models import GuestResponse
    responses = GuestResponse.objects.filter(event=event, will_attend=True)
    total = 0
    for response in responses:
        total += 1  # L'invité
        if response.is_accompanied:
            total += (response.number_of_guests - 1)
    return total


# ============================================================
# NOUVEAUX FILTRES POUR LE MODULE D'ESTIMATION
# ============================================================

@register.filter
def get_suggested_units(drink_name):
    """
    Suggère les unités par conditionnement en fonction du nom de la boisson
    Utilisé dans le formulaire de configuration en masse
    """
    if not drink_name:
        return 1
    
    drink_lower = drink_name.lower()
    
    # Suggestions par type de boisson
    if 'biere' in drink_lower or 'bière' in drink_lower:
        return 12
    elif '33' in drink_lower or 'export' in drink_lower:
        return 12
    elif 'vin' in drink_lower:
        return 6
    elif 'coca' in drink_lower or 'coca-cola' in drink_lower:
        return 12
    elif 'fanta' in drink_lower:
        return 12
    elif 'sprite' in drink_lower:
        return 12
    elif 'whisky' in drink_lower:
        return 1
    elif 'champagne' in drink_lower:
        return 1
    elif 'amarula' in drink_lower:
        return 6
    elif 'simba' in drink_lower:
        return 12
    elif 'jus' in drink_lower:
        return 6
    elif 'eau' in drink_lower:
        return 6
    elif 'soft' in drink_lower:
        return 12
    elif 'bière' in drink_lower:
        return 12
    
    return 1


@register.filter
def currency_symbol(currency_code):
    """Retourne le symbole d'une devise"""
    symbols = {
        'CDF': 'FC',
        'USD': '$',
        'EUR': '€',
    }
    return symbols.get(currency_code, currency_code)


@register.filter
def format_price(price, currency_code='CDF'):
    """Formate un prix avec sa devise"""
    if price is None:
        return '-'
    try:
        symbol = currency_symbol(currency_code)
        return f'{Decimal(price):.2f} {symbol}'
    except:
        return str(price)


@register.filter
def get_existing_packaging(drink_name, event):
    """Récupère le conditionnement existant pour une boisson"""
    from apps.expenses.models import DrinkPackaging
    if not event or not drink_name:
        return None
    try:
        return DrinkPackaging.objects.filter(
            event=event,
            drink_name=drink_name,
            is_active=True
        ).first()
    except:
        return None


@register.filter
def get_packaging_type_display(packaging):
    """Retourne le libellé du type de conditionnement"""
    if not packaging:
        return '-'
    return packaging.get_packaging_type_display()


@register.simple_tag
def get_configured_drinks_count(event):
    """Nombre de boissons configurées avec conditionnement"""
    from apps.expenses.models import DrinkPackaging
    return DrinkPackaging.objects.filter(event=event, is_active=True).count()


@register.simple_tag
def get_unconfigured_drinks(event):
    """Liste des boissons non configurées"""
    from apps.expenses.models import DrinkPackaging
    if not event:
        return []
    drink_options = event.drink_options or []
    configured = DrinkPackaging.objects.filter(
        event=event, 
        is_active=True
    ).values_list('drink_name', flat=True)
    return [d for d in drink_options if d not in configured]