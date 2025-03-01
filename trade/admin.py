from django.contrib import admin

from trade.models import Item, Tax, Discount, Order, Currency, PreOrder

admin.AdminSite.site_header = "ООО 'Рога и копыта'"
admin.AdminSite.index_title = "Управление товаром / оплатами"

# Register your models here.
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Класс админки"""
    list_display = ('name', 'pk', 'description', 'price', )
    list_display_link = ('name', 'pk', 'description', 'price', )
    search_fields = ('name', 'description', )

@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'tax_base', )
    list_display_link = ('pk', 'name', 'tax_base', )
    search_fields = ('name', 'tax_base', )

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'discount_base', )
    list_display_link = ('pk', 'name', 'discount_base', )
    search_fields = ('name', 'discount_base', )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'item', 'quantity', )
    list_display_link = ('pk', 'item', 'quantity', )

@admin.register(PreOrder)
class PreOrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'session_tag', 'item', 'quantity', )
    list_display_link = ('pk', 'session_tag', 'item', 'quantity', )

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('pk', 'code', 'name', 'related_currency', 'country', 'amount', )
    list_display_link = ('pk', 'code', 'name', 'related_currency', 'country', 'amount', )