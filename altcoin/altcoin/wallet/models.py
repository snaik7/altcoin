import json
import time

import requests
from django.db import models


# Create your models here.
from altcoin.settings.base import get_env_var
from altcoin.settings.local import db_uri
from altcoin.utils import service_auth, Util
from bitcoinlib.db import DbInit, DbNetwork


class Wallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)
    wallet_name = models.TextField()
    username = models.TextField()
    coin_type = models.TextField(default='btc')
    created = models.DateTimeField(auto_now_add=True)



