from rest_framework.response import Response
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


class WeekdayCommissionRuleViewSet(ModelViewSet):
    queryset = WeekdayCommissionRule.objects.all()
    serializer_class = WeekdayCommissionRuleSerializer


class SaleViewSet(ModelViewSet):
    queryset = (
        Sale.objects
        .select_related('customer', 'seller')
        .prefetch_related('items__product')
    )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return SaleWriteSerializer

        return SaleReadSerializer


class CommissionReportView(APIView):
    """Retorna as comissões agrupadas por vendedor em um período."""

    def get(self, request):
        """Valida as datas, executa a regra e serializa o resultado."""
        query_serializer = CommissionReportQuerySerializer(
            data=request.query_params,
        )
        query_serializer.is_valid(raise_exception=True)

        # A view coordena o HTTP, mas não calcula nenhuma comissão.
        report = CommissionService.build_report(
            start_date=query_serializer.validated_data['start_date'],
            end_date=query_serializer.validated_data['end_date'],
        )

        response_serializer = CommissionReportSerializer(report)
        return Response(response_serializer.data)
