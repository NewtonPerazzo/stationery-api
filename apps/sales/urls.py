from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    CommissionReportView,
    SaleViewSet,
    WeekdayCommissionRuleViewSet,
)


router = SimpleRouter()
router.register('sales', SaleViewSet, basename='sale')
router.register(
    'commission-rules',
    WeekdayCommissionRuleViewSet,
    basename='commission-rule',
)

urlpatterns = [
    path(
        'commissions/',
        CommissionReportView.as_view(),
        name='commission-report',
    ),
    *router.urls,
]
