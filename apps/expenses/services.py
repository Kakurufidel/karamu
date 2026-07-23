import unicodedata
from decimal import Decimal
from collections import defaultdict
from django.utils.translation import gettext as _
from apps.guests.models import GuestResponse, InvitedGuest
from .models import DrinkPackaging


class EstimationService:
    """
    Service de calcul de l'estimation des besoins en boissons
    """
    
    def __init__(self, event, margin_percentage=0, include_pending=True, pending_rate=75, number_of_services=1):
        self.event = event
        self.margin_percentage = margin_percentage or 0
        self.include_pending = include_pending
        self.pending_rate = pending_rate / 100
        self.number_of_services = max(1, number_of_services or 1)
        self._normalized_cache = {}

    def normalize_drink_name(self, name):
        if not name:
            return ""
        cache_key = name.lower()
        if cache_key in self._normalized_cache:
            return self._normalized_cache[cache_key]
        
        normalized = unicodedata.normalize('NFKD', name.lower())
        normalized = normalized.encode('ASCII', 'ignore').decode('utf-8')
        normalized = ' '.join(normalized.split())
        
        self._normalized_cache[cache_key] = normalized
        return normalized

    def get_drink_choices(self):
        responses = GuestResponse.objects.filter(
            event=self.event,
            will_attend=True
        ).values(
            'drink_choice', 'drink_other',
            'is_accompanied', 'number_of_guests',
            'companion_drink_choice', 'companion_drink_other'
        )

        choices = defaultdict(int)

        for response in responses.iterator():
            # Boisson de l'invité
            if response['drink_choice'] and response['drink_choice'] != 'other':
                drink_name = self.get_drink_display_name(response['drink_choice'])
                choices[drink_name] += 1
            elif response['drink_choice'] == 'other' and response['drink_other']:
                drink_name = response['drink_other'].strip()
                if drink_name:
                    choices[drink_name] += 1
            
            # Boisson des accompagnants
            if response['is_accompanied']:
                companion_count = response['number_of_guests'] - 1
                if companion_count > 0:
                    if response['companion_drink_choice'] and response['companion_drink_choice'] != 'other':
                        drink_name = self.get_drink_display_name(response['companion_drink_choice'])
                        choices[drink_name] += companion_count
                    elif response['companion_drink_choice'] == 'other' and response['companion_drink_other']:
                        drink_name = response['companion_drink_other'].strip()
                        if drink_name:
                            choices[drink_name] += companion_count

        return dict(choices)
    
    def get_drink_display_name(self, choice_key):
        choices = {
            'vin': 'Vin',
            'biere': 'Bière',
            'soft': 'Soft',
            'jus': 'Jus',
            'eau': 'Eau',
            'coca': 'Coca-Cola',
            'fanta': 'Fanta',
            'sprite': 'Sprite',
            'simba': 'Simba',
            'amarula': 'Amarula',
            'champagne': 'Champagne',
            'whisky': 'Whisky',
        }
        return choices.get(choice_key, choice_key)

    def get_pending_estimation(self, existing_choices):
        if not self.include_pending:
            return {}

        responded_emails = set(
            GuestResponse.objects.filter(event=self.event).values_list('email', flat=True)
        )

        pending_count = 0
        for guest in InvitedGuest.objects.filter(event=self.event).iterator():
            has_responded = False
            if guest.email and guest.email in responded_emails:
                has_responded = True
            else:
                guest_name = f"{guest.first_name} {guest.last_name}"
                guest_normalized = self.normalize_drink_name(guest_name)
                for response in GuestResponse.objects.filter(event=self.event):
                    response_name = f"{response.first_name} {response.last_name}"
                    if self.normalize_drink_name(response_name) == guest_normalized:
                        has_responded = True
                        break
            
            if not has_responded:
                pending_count += 1

        if pending_count == 0 or not existing_choices:
            return {}

        estimated_attendees = int(pending_count * self.pending_rate)
        if estimated_attendees == 0:
            return {}

        total_existing = sum(existing_choices.values())
        if total_existing == 0:
            return {}

        pending_choices = {}
        for drink, count in existing_choices.items():
            proportion = count / total_existing
            estimated = int(estimated_attendees * proportion)
            if estimated > 0:
                pending_choices[drink] = estimated

        return pending_choices

    def calculate_needs(self):
        # 1. Récupérer les choix existants
        existing_choices = self.get_drink_choices()

        # 2. Estimer les choix des invités en attente
        pending_choices = self.get_pending_estimation(existing_choices)

        # 3. Agréger tous les choix
        all_choices = defaultdict(int)
        for drink, count in existing_choices.items():
            all_choices[drink] += count
        for drink, count in pending_choices.items():
            all_choices[drink] += count

        # 4. Appliquer la marge d'erreur
        if self.margin_percentage > 0:
            for drink in list(all_choices.keys()):
                all_choices[drink] = int(all_choices[drink] * (1 + self.margin_percentage / 100))

        # 5. Multiplier par le nombre de tournées
        if self.number_of_services > 1:
            for drink in list(all_choices.keys()):
                all_choices[drink] = all_choices[drink] * self.number_of_services

        # 6. Récupérer les conditionnements configurés
        packagings = DrinkPackaging.objects.filter(event=self.event, is_active=True)

        result = []
        total_cost = Decimal('0')
        total_cases = 0
        total_pieces = 0
        packaging_names = set()

        for packaging in packagings:
            drink_name = packaging.drink_name
            needed_pieces = all_choices.get(drink_name, 0)
            packaging_names.add(drink_name)
            
            total_pieces += needed_pieces

            if needed_pieces > 0:
                cases_needed = packaging.get_cases_needed(needed_pieces)
                cost = packaging.get_total_cost(needed_pieces)
                total_cost += cost
                total_cases += cases_needed
            else:
                cases_needed = 0
                cost = Decimal('0')

            result.append({
                'drink_name': drink_name,
                'needed_pieces': needed_pieces,
                'pieces_per_case': packaging.pieces_per_case,
                'cases_needed': cases_needed,
                'price_per_case': packaging.price_per_case,
                'unit_price': packaging.unit_price(),
                'cost': cost,
                'is_active': packaging.is_active,
            })

        # 7. Gérer les boissons non configurées
        other_drinks = set(all_choices.keys()) - packaging_names
        for drink_name in other_drinks:
            needed_pieces = all_choices.get(drink_name, 0)
            if needed_pieces > 0:
                result.append({
                    'drink_name': drink_name,
                    'needed_pieces': needed_pieces,
                    'pieces_per_case': '?',
                    'cases_needed': '?',
                    'price_per_case': None,
                    'unit_price': None,
                    'cost': Decimal('0'),
                    'is_active': False,
                    'is_other': True,
                })

        return {
            'details': result,
            'total_cost': total_cost,
            'total_cases': total_cases,
            'total_pieces': total_pieces,
            'existing_choices': dict(existing_choices),
            'pending_choices': dict(pending_choices),
            'margin_percentage': self.margin_percentage,
            'pending_rate': int(self.pending_rate * 100),
            'number_of_services': self.number_of_services,
        }

    def get_chart_data(self):
        choices = self.get_drink_choices()
        if not choices:
            return {'labels': [], 'data': [], 'colors': []}

        sorted_choices = sorted(choices.items(), key=lambda x: x[1], reverse=True)

        colors = [
            '#8B5CF6', '#06B6D4', '#F59E0B', '#10B981',
            '#EF4444', '#EC4899', '#6366F1', '#14B8A6',
            '#F97316', '#8B5CF6', '#22D3EE', '#34D399',
        ]

        return {
            'labels': [item[0] for item in sorted_choices[:12]],
            'data': [item[1] for item in sorted_choices[:12]],
            'colors': colors[:len(sorted_choices)]
        }

    def get_stats(self):
        total_invited = self.event.invited_guests.count()
        total_responses = GuestResponse.objects.filter(event=self.event).count()
        attending = GuestResponse.objects.filter(event=self.event, will_attend=True).count()
        not_attending = GuestResponse.objects.filter(event=self.event, will_attend=False).count()
        
        return {
            'total_invited': total_invited,
            'total_responses': total_responses,
            'attending': attending,
            'not_attending': not_attending,
            'pending': total_invited - total_responses,
            'response_rate': round((total_responses / total_invited * 100), 1) if total_invited > 0 else 0,
        }