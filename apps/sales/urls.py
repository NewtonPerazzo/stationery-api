from rest_framework.routers import SimpleRouter

from .views import SaleViewSet, WeekdayCommissionRuleViewSet


router = SimpleRouter()
router.register('sales', SaleViewSet, basename='sale')
router.register(
    'commission-rules',
    WeekdayCommissionRuleViewSet,
    basename='commission-rule',
)

urlpatterns = router.urls
