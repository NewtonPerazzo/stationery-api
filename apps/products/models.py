from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('description',)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name='product_unit_price_non_negative',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(commission_percentage__gte=0)
                    & models.Q(commission_percentage__lte=10)
                ),
                name='product_commission_between_0_and_10',
            ),
        ]

    def __str__(self):
        return f'{self.code} - {self.description}'
