from rest_framework import serializers

from .models import Customer, Seller


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            'id',
            'name',
            'email',
            'phone',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = (
            'id',
            'name',
            'email',
            'phone',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
