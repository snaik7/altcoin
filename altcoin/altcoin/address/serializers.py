from django.db import models
from django.contrib.auth.models import User, Group
from altcoin.address.models import Address
from rest_framework import serializers

# Create your models here.

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        db_table = 'address'
        model = Address
        fields = ['address_id', 'username','action','created','coin_type','private_key', 'public_key', 'hex']

class QRSerializer(serializers.Serializer):
    """
    This serializer is the output of create qr code
    """
    file_type = serializers.CharField(max_length=5)
    image_base64 = serializers.CharField(max_length=300)

		
