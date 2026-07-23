# from django.contrib import admin
# from django.utils.translation import gettext_lazy as _
# from .models import DrinkPackaging


# @admin.register(DrinkPackaging)
# class DrinkPackagingAdmin(admin.ModelAdmin):
#     list_display = ['drink_name', 'event', 'packaging_type', 'units_per_packaging', 'price_per_packaging', 'is_active']
#     list_filter = ['event', 'packaging_type', 'is_active']
#     search_fields = ['drink_name', 'event__name']
#     readonly_fields = ['created_at', 'updated_at']
#     ordering = ['event', 'drink_name']
    
#     fieldsets = (
#         (_('Informations'), {
#             'fields': ('event', 'drink_name', 'is_active')
#         }),
#         (_('Conditionnement'), {
#             'fields': ('packaging_type', 'units_per_packaging', 'price_per_packaging')
#         }),
#         (_('Métadonnées'), {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related('event')