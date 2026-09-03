from rest_framework.routers import SimpleRouter

from .views import CustomerViewSet, SellerViewSet


router = SimpleRouter()
router.register('customers', CustomerViewSet, basename='customer')
router.register('sellers', SellerViewSet, basename='seller')

urlpatterns = router.urls
