from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.people.models import Customer, Seller
from apps.products.models import Product

from .models import Sale, SaleItem, WeekdayCommissionRule
from .services import CommissionService


class CommissionServiceTest(TestCase):
    """Testa as principais regras usadas no relatório de comissões."""

    def test_applies_weekday_minimum_and_maximum(self):
        """Aplica o piso e o teto configurados para o dia da venda."""
        customer = Customer.objects.create(
            name='Cliente Teste',
            email='cliente@example.com',
            phone='11999990000',
        )
        seller = Seller.objects.create(
            name='Vendedor Teste',
            email='vendedor@example.com',
            phone='11999991111',
        )
        low_percentage_product = Product.objects.create(
            code='CADERNO',
            description='Caderno',
            unit_price=Decimal('20.00'),
            commission_percentage=Decimal('2.00'),
        )
        high_percentage_product = Product.objects.create(
            code='MOCHILA',
            description='Mochila',
            unit_price=Decimal('10.00'),
            commission_percentage=Decimal('10.00'),
        )
        WeekdayCommissionRule.objects.create(
            weekday=WeekdayCommissionRule.Weekday.MONDAY,
            minimum_percentage=Decimal('3.00'),
            maximum_percentage=Decimal('5.00'),
        )

        # 31/08/2026 é uma segunda-feira, portanto usa a regra acima.
        sold_at = timezone.make_aware(datetime(2026, 8, 31, 10, 0))
        sale = Sale.objects.create(
            invoice_number='NF-TESTE',
            sold_at=sold_at,
            customer=customer,
            seller=seller,
        )
        SaleItem.objects.create(
            sale=sale,
            product=low_percentage_product,
            quantity=2,
            unit_price=Decimal('20.00'),
            commission_percentage=Decimal('2.00'),
        )
        SaleItem.objects.create(
            sale=sale,
            product=high_percentage_product,
            quantity=3,
            unit_price=Decimal('10.00'),
            commission_percentage=Decimal('10.00'),
        )

        report = CommissionService.build_report(
            start_date=date(2026, 8, 31),
            end_date=date(2026, 8, 31),
        )
        seller_result = report['sellers'][0]
        details_by_product = {
            item['product_name']: item
            for item in seller_result['items']
        }

        # Caderno: 2 x R$ 20,00 x 3% = R$ 1,20 (aplica o mínimo).
        self.assertEqual(
            details_by_product['Caderno']['commission_percentage'],
            Decimal('3.00'),
        )
        self.assertEqual(
            details_by_product['Caderno']['commission_total'],
            Decimal('1.20'),
        )

        # Mochila: 3 x R$ 10,00 x 5% = R$ 1,50 (aplica o máximo).
        self.assertEqual(
            details_by_product['Mochila']['commission_percentage'],
            Decimal('5.00'),
        )
        self.assertEqual(
            details_by_product['Mochila']['commission_total'],
            Decimal('1.50'),
        )
        self.assertEqual(seller_result['commission_total'], Decimal('2.70'))
        self.assertEqual(report['grand_total'], Decimal('2.70'))

    def test_keeps_product_percentage_without_weekday_rule(self):
        """Mantém o percentual do produto quando o dia não tem regra."""
        percentage = CommissionService._get_applied_percentage(
            product_percentage=Decimal('4.00'),
            rule=None,
        )

        self.assertEqual(percentage, Decimal('4.00'))
