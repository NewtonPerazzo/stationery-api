from django.db import transaction

from .models import Sale, SaleItem


class SaleService:
    @staticmethod
    @transaction.atomic
    def create(validated_data):
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(**validated_data)
        SaleService._replace_items(sale, items_data)
        return sale

    @staticmethod
    @transaction.atomic
    def update(sale, validated_data):
        items_data = validated_data.pop('items', None)

        for field, value in validated_data.items():
            setattr(sale, field, value)

        sale.save()

        if items_data is not None:
            sale.items.all().delete()
            SaleService._replace_items(sale, items_data)

        return sale

    @staticmethod
    def _replace_items(sale, items_data):
        SaleItem.objects.bulk_create([
            SaleItem(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['product'].unit_price,
                commission_percentage=item['product'].commission_percentage,
            )
            for item in items_data
        ])
