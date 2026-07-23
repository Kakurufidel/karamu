from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ExpensesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.expenses'
    verbose_name = _('Gestion des dépenses')

    def ready(self):
        """Import des signaux si nécessaire"""
        # import apps.expenses.signals
        pass