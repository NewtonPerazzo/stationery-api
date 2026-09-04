from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import Sale, SaleItem, WeekdayCommissionRule
from .repositories import CommissionRepository


class SaleService:
    """Coordena a persistência de vendas e de seus itens."""

    @staticmethod
    @transaction.atomic
    def create(validated_data: dict[str, Any]) -> Sale:
        """Cria uma venda completa dentro de uma única transação."""
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(**validated_data)
        SaleService._replace_items(sale, items_data)
        return sale

    @staticmethod
    @transaction.atomic
    def update(sale: Sale, validated_data: dict[str, Any]) -> Sale:
        """Atualiza os dados e substitui os itens quando forem enviados."""
        items_data = validated_data.pop('items', None)

        for field, value in validated_data.items():
            setattr(sale, field, value)

        sale.save()

        # Quando "items" não vem na requisição, mantemos os itens atuais.
        # Quando ele vem, entendemos que representa a nova lista completa da venda.
        if items_data is not None:
            # Remove somente os SaleItems relacionados à venda.
            # A venda e os produtos cadastrados não são excluídos.
            sale.items.all().delete()

            # Cria os novos itens e registra neles o preço e a comissão atuais
            # dos produtos, preservando esses valores como histórico da venda.
            SaleService._replace_items(sale, items_data)

        return sale

    @staticmethod
    def _replace_items(
        sale: Sale,
        items_data: list[dict[str, Any]],
    ) -> None:
        """Cria os itens recebidos para a venda informada."""

        # O preço e a comissão são copiados do produto para o SaleItem.
        # Assim, mudanças futuras no produto não alteram vendas antigas.
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


class CommissionService:
    """Calcula comissões por vendedor para um período informado."""

    MONEY_PRECISION = Decimal('0.01')
    PERCENT_DIVISOR = Decimal('100')

    @classmethod
    def build_report(
        cls,
        start_date: date,
        end_date: date,
        search: str = '',
        ordering: str = 'seller_name',
    ) -> dict[str, Any]:
        """Retorna totais por vendedor e o total geral do período."""
        current_timezone = timezone.get_current_timezone()

        # O início considera 00:00 do primeiro dia no fuso do projeto.
        start_at = timezone.make_aware(
            datetime.combine(start_date, time.min),
            current_timezone,
        )

        # O fim é o início do dia seguinte e será usado de forma exclusiva.
        end_at = timezone.make_aware(
            datetime.combine(end_date + timedelta(days=1), time.min),
            current_timezone,
        )

        # O dicionário permite localizar a regra usando weekday() sem consultas
        # adicionais para cada venda.
        rules_by_weekday = {
            rule.weekday: rule
            for rule in WeekdayCommissionRule.objects.all()
        }

        # Todos os vendedores começam em zero para também aparecerem quando
        # não tiverem vendas no período.
        sellers = {
            seller['id']: {
                'seller_id': seller['id'],
                'seller_name': seller['name'],
                'commission_total': Decimal('0.00'),
                # Durante o cálculo, o dicionário permite acumular rapidamente
                # as vendas do mesmo produto, mesmo que estejam em notas distintas.
                'items_by_product': {},
            }
            for seller in CommissionRepository.list_sellers()
        }

        sales = CommissionRepository.list_sales_between(start_at, end_at)

        for sale in sales:
            # Converte a data armazenada para o fuso local antes de descobrir
            # o dia da semana da venda.
            weekday = timezone.localtime(sale.sold_at).weekday()
            rule = rules_by_weekday.get(weekday)

            for item in sale.items.all():
                percentage = cls._get_applied_percentage(
                    item.commission_percentage,
                    rule,
                )
                commission = cls._calculate_item_commission(item, percentage)
                sellers[sale.seller_id]['commission_total'] += commission

                # O detalhe agrupa o produto dentro do período consultado.
                # O valor vendido usa o preço histórico gravado no SaleItem.
                item_total = item.quantity * item.unit_price
                product_detail = sellers[sale.seller_id][
                    'items_by_product'
                ].setdefault(
                    (item.product_id, percentage),
                    {
                        'product_id': item.product_id,
                        'product_name': item.product.description,
                        'quantity': 0,
                        'total_amount': Decimal('0.00'),
                        'commission_total': Decimal('0.00'),
                        'commission_percentage': percentage,
                    },
                )
                product_detail['quantity'] += item.quantity
                product_detail['total_amount'] += item_total
                product_detail['commission_total'] += commission

        # A estrutura temporária de busca vira a lista pública devolvida pela API.
        # Ordenar por produto mantém a expansão previsível para o usuário.
        for seller in sellers.values():
            seller['items'] = sorted(
                seller.pop('items_by_product').values(),
                key=lambda item: item['product_name'].casefold(),
            )

        seller_results = list(sellers.values())

        # A busca é aplicada no backend depois do cálculo e antes do total geral.
        normalized_search = search.strip().casefold()
        if normalized_search:
            seller_results = [
                seller
                for seller in seller_results
                if normalized_search in seller['seller_name'].casefold()
            ]

        # Primeiro ordena por nome para desempates previsíveis.
        seller_results.sort(key=lambda seller: seller['seller_name'].casefold())

        if ordering in ('commission_total', '-commission_total'):
            seller_results.sort(
                key=lambda seller: seller['commission_total'],
                reverse=ordering.startswith('-'),
            )

        grand_total = sum(
            (seller['commission_total'] for seller in seller_results),
            start=Decimal('0.00'),
        )

        return {
            'start_date': start_date,
            'end_date': end_date,
            'sellers': seller_results,
            'grand_total': grand_total,
        }

    @staticmethod
    def _get_applied_percentage(
        product_percentage: Decimal,
        rule: WeekdayCommissionRule | None,
    ) -> Decimal:
        """Aplica os limites do dia ou mantém a comissão original."""
        if rule is None:
            return product_percentage

        # max aplica o piso; min aplica o teto configurado para o dia.
        return min(
            max(product_percentage, rule.minimum_percentage),
            rule.maximum_percentage,
        )

    @classmethod
    def _calculate_item_commission(
        cls,
        item: SaleItem,
        percentage: Decimal,
    ) -> Decimal:
        """Calcula e arredonda a comissão monetária de um item."""
        commission = (
            item.quantity
            * item.unit_price
            * percentage
            / cls.PERCENT_DIVISOR
        )

        # Valores monetários são arredondados para centavos por item antes
        # da soma da venda e do vendedor.
        return commission.quantize(
            cls.MONEY_PRECISION,
            rounding=ROUND_HALF_UP,
        )
