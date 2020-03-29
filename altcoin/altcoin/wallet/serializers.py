from django.db import models
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from altcoin.wallet.models import Wallet

# Create your models here.

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']
    
'''
class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['username', 'wallet_id','wallet_name','created']
'''

class WalletSerializer(serializers.ModelSerializer):
    '''
    username = serializers.CharField()
    wallet_id = serializers.CharField()
    wallet_name = serializers.CharField()
    '''
    class Meta:
        db_table = 'wallet'
        model = Wallet
        fields = ['wallet_id', 'wallet_name','username','created']


