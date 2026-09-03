from rest_framework.viewsets import ModelViewSet

from .models import Sale, WeekdayCommissionRule
from .serializers import (
    SaleReadSerializer,
    SaleWriteSerializer,
    WeekdayCommissionRuleSerializer,
)


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
