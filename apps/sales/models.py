from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class WeekdayCommissionRule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Segunda-feira'
        TUESDAY = 1, 'Terça-feira'
        WEDNESDAY = 2, 'Quarta-feira'
        THURSDAY = 3, 'Quinta-feira'
        FRIDAY = 4, 'Sexta-feira'
        SATURDAY = 5, 'Sábado'
        SUNDAY = 6, 'Domingo'

    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices, unique=True)
    minimum_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('10.00')),
        ],
    )
    maximum_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('10.00')),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('weekday',)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(minimum_percentage__gte=0)
                    & models.Q(minimum_percentage__lte=10)
                ),
                name='weekday_min_commission_between_0_and_10',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(maximum_percentage__gte=0)
                    & models.Q(maximum_percentage__lte=10)
                ),
                name='weekday_max_commission_between_0_and_10',
            ),
            models.CheckConstraint(
                condition=models.Q(minimum_percentage__lte=models.F('maximum_percentage')),
                name='weekday_min_commission_lte_max',
            ),
        ]

    def __str__(self) -> str:
        return self.get_weekday_display()


class Sale(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True)
    sold_at = models.DateTimeField()
    customer = models.ForeignKey(
        'people.Customer',
        on_delete=models.PROTECT,
        related_name='sales',
    )
    seller = models.ForeignKey(
        'people.Seller',
        on_delete=models.PROTECT,
        related_name='sales',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-sold_at',)

    def __str__(self) -> str:
        return self.invoice_number


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='sale_items',
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('10.00')),
        ],
    )

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('sale', 'product'),
                name='unique_product_per_sale',
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='sale_item_quantity_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name='sale_item_unit_price_non_negative',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(commission_percentage__gte=0)
                    & models.Q(commission_percentage__lte=10)
                ),
                name='sale_item_commission_between_0_and_10',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.sale.invoice_number} - {self.product}'
