from django.db import models
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from altcoin.txn.models import Txn


# Create your models here.

class TxnSerializer(serializers.ModelSerializer):

    class Meta:
        db_table = 'txn'
        model = Txn
        fields = ['txn_id', 'wallet_id', 'type','status','source','source_amount', 'source_currency','destination','destination_amount','destination_currency','message','includes_fee','created','updated']

