from django.contrib import admin

from .models import Sale, SaleItem, WeekdayCommissionRule


@admin.register(WeekdayCommissionRule)
class WeekdayCommissionRuleAdmin(admin.ModelAdmin):
    list_display = (
        'weekday_name',
        'minimum_percentage',
        'maximum_percentage',
    )
    ordering = ('weekday',)

    @admin.display(description='Dia da semana', ordering='weekday')
    def weekday_name(self, rule):
        return rule.get_weekday_display()


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    autocomplete_fields = ('product',)
    extra = 1
    min_num = 1
    validate_min = True


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'sold_at', 'customer', 'seller')
    search_fields = (
        'invoice_number',
        'customer__name',
        'seller__name',
    )
    list_filter = ('sold_at', 'seller')
    autocomplete_fields = ('customer', 'seller')
    list_select_related = ('customer', 'seller')
    date_hierarchy = 'sold_at'
    ordering = ('-sold_at',)
    inlines = (SaleItemInline,)
