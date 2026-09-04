from datetime import datetime

from django.db.models import QuerySet

from apps.people.models import Seller

from .models import Sale


class CommissionRepository:
    """Centraliza as consultas usadas pelo relatório de comissões."""

    @staticmethod
    def list_sellers() -> QuerySet:
        """Retorna todos os vendedores na ordem exibida pelo relatório."""
        return Seller.objects.order_by('name').values('id', 'name')

    @staticmethod
    def list_sales_between(
        start_at: datetime,
        end_at: datetime,
    ) -> QuerySet[Sale]:
        """Busca vendas no intervalo [início, fim), com dados relacionados."""
        return (
            Sale.objects
            # O fim exclusivo inclui todo o último dia sem depender de 23:59:59.
            .filter(sold_at__gte=start_at, sold_at__lt=end_at)
            .select_related('seller')
            # Carrega itens e produtos antecipadamente para evitar uma nova
            # consulta ao banco para cada produto detalhado no relatório.
            .prefetch_related('items__product')
            .order_by('sold_at')
        )
