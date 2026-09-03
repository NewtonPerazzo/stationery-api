from rest_framework.viewsets import ModelViewSet

from .models import Customer, Seller
from .serializers import CustomerSerializer, SellerSerializer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class SellerViewSet(ModelViewSet):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
