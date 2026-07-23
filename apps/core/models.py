from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Classe de base avec les champs communs à tous les modèles
    Inclut le soft delete pour ne jamais supprimer définitivement les données
    """
    created_at = models.DateTimeField(
        _('créé le'),
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _('modifié le'),
        auto_now=True,
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name=_('créé par')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name=_('modifié par')
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        db_index=True
    )
    
    # ========== SOFT DELETE ==========
    deleted_at = models.DateTimeField(
        _('supprimé le'),
        null=True,
        blank=True,
        db_index=True
    )
    is_deleted = models.BooleanField(
        _('supprimé'),
        default=False,
        db_index=True
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        """Marque l'objet comme supprimé sans le supprimer de la base"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Restaure un objet marqué comme supprimé"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    @property
    def is_soft_deleted(self):
        """Vérifie si l'objet est marqué comme supprimé"""
        return self.is_deleted