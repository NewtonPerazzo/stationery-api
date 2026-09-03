from decimal import Decimal

from rest_framework import serializers

from apps.people.models import Customer, Seller
from apps.people.serializers import CustomerSerializer, SellerSerializer
from apps.products.models import Product
from apps.products.serializers import ProductSerializer

from .models import Sale, SaleItem, WeekdayCommissionRule
from .services import SaleService


class WeekdayCommissionRuleSerializer(serializers.ModelSerializer):
    weekday_name = serializers.CharField(
        source='get_weekday_display',
        read_only=True,
    )

    class Meta:
        model = WeekdayCommissionRule
        fields = (
            'id',
            'weekday',
            'weekday_name',
            'minimum_percentage',
            'maximum_percentage',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'weekday_name', 'created_at', 'updated_at')

    def validate(self, attrs):
        minimum = attrs.get(
            'minimum_percentage',
            getattr(self.instance, 'minimum_percentage', None),
        )
        maximum = attrs.get(
            'maximum_percentage',
            getattr(self.instance, 'maximum_percentage', None),
        )

        if minimum is not None and maximum is not None and minimum > maximum:
            raise serializers.ValidationError({
                'maximum_percentage': (
                    'O percentual máximo deve ser maior ou igual ao mínimo.'
                ),
            })

        return attrs


class SaleItemReadSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = SaleItem
        fields = (
            'id',
            'product',
            'quantity',
            'unit_price',
            'commission_percentage',
            'total_amount',
        )

    def get_total_amount(self, item):
        return f'{item.quantity * item.unit_price:.2f}'


class SaleReadSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    seller = SellerSerializer(read_only=True)
    items = SaleItemReadSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = (
            'id',
            'invoice_number',
            'sold_at',
            'customer',
            'seller',
            'items',
            'total_amount',
            'created_at',
            'updated_at',
        )

    def get_total_amount(self, sale):
        total = sum(
            (item.quantity * item.unit_price for item in sale.items.all()),
            start=Decimal('0.00'),
        )
        return f'{total:.2f}'


class SaleItemInputSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source='product',
        queryset=Product.objects.all(),
    )
    quantity = serializers.IntegerField(min_value=1)


class SaleWriteSerializer(serializers.ModelSerializer):
    customer_id = serializers.PrimaryKeyRelatedField(
        source='customer',
        queryset=Customer.objects.all(),
    )
    seller_id = serializers.PrimaryKeyRelatedField(
        source='seller',
        queryset=Seller.objects.all(),
    )
    items = SaleItemInputSerializer(many=True, allow_empty=False)

    class Meta:
        model = Sale
        fields = (
            'id',
            'invoice_number',
            'sold_at',
            'customer_id',
            'seller_id',
            'items',
        )
        read_only_fields = ('id',)

    def validate_items(self, items):
        product_ids = [item['product'].pk for item in items]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                'Cada produto pode aparecer apenas uma vez na venda.'
            )

        return items

    def create(self, validated_data):
        return SaleService.create(validated_data)

    def update(self, instance, validated_data):
        return SaleService.update(instance, validated_data)


class CommissionReportQuerySerializer(serializers.Serializer):
    """Valida os parâmetros recebidos pela query string."""

    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, attrs):
        """Garante que o intervalo esteja em ordem cronológica."""
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError({
                'end_date': 'A data final deve ser igual ou posterior à inicial.',
            })

        return attrs


class SellerCommissionSerializer(serializers.Serializer):
    """Representa o total calculado para um vendedor."""

    seller_id = serializers.IntegerField()
    seller_name = serializers.CharField()
    commission_total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class CommissionReportSerializer(serializers.Serializer):
    """Define o contrato JSON retornado pelo relatório."""

    start_date = serializers.DateField()
    end_date = serializers.DateField()
    sellers = SellerCommissionSerializer(many=True)
    grand_total = serializers.DecimalField(
        max_digits=16,
        decimal_places=2,
    )
