from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Sale, WeekdayCommissionRule
from .serializers import (
    CommissionReportQuerySerializer,
    CommissionReportSerializer,
    SaleReadSerializer,
    SaleWriteSerializer,
    WeekdayCommissionRuleSerializer,
)
from .services import CommissionService


item_total = ExpressionWrapper(
    F('items__quantity') * F('items__unit_price'),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


class WeekdayCommissionRuleViewSet(ModelViewSet):
    queryset = WeekdayCommissionRule.objects.all()
    serializer_class = WeekdayCommissionRuleSerializer


class SaleViewSet(ModelViewSet):
    queryset = (
        Sale.objects
        .annotate(
            total_amount=Coalesce(
                Sum(item_total),
                Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
        .select_related('customer', 'seller')
        .prefetch_related('items__product')
    )
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = (
        'invoice_number',
        'customer__name',
        'seller__name',
    )
    ordering_fields = ('invoice_number', 'total_amount')
    ordering = ('invoice_number',)

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action in ('create', 'update', 'partial_update'):
            return SaleWriteSerializer

        return SaleReadSerializer


class CommissionReportView(APIView):
    """Retorna as comissões agrupadas por vendedor em um período."""

    def get(self, request: Request) -> Response:
        """Valida as datas, executa a regra e serializa o resultado."""
        query_serializer = CommissionReportQuerySerializer(
            data=request.query_params,
        )
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        # A view coordena o HTTP, mas não calcula nenhuma comissão.
        report = CommissionService.build_report(
            start_date=filters['start_date'],
            end_date=filters['end_date'],
            search=filters['search'],
            ordering=filters['ordering'],
        )

        response_serializer = CommissionReportSerializer(report)
        return Response(response_serializer.data)
