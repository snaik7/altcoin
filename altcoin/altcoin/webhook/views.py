import json
import traceback

import requests

from django.db import models

from altcoin.settings.base import get_env_var
from altcoin.utils import service_auth, ltc_srv
from altcoin.wallet.serializers import UserSerializer, GroupSerializer, WalletSerializer
from django.views.decorators.csrf import csrf_exempt
from altcoin.wallet.models import Wallet
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from altcoin.webhook.email import email_txn
from bitcoinlib.services.bitcoind import BitcoindClient
from bitcoinlib.services.services import Service
from bitcoinlib.services.litecoind import LitecoindClient
from bitcoinlib.wallets import HDWallet, wallet_create_or_open

from bitcoinlib.transactions import Transaction

from altcoin.webhook.models import Email


# Create your views here.

class WebhookLTCView(APIView):
    permission_classes = []
    def post(self, request):
        try:
            print('post')
            data = JSONParser().parse(request)
            print('data received ' + str(data))
            txn = data.get('hash')
            email = Email()
            email.email = 'santosh.naik@tissatech.com'
            email.username = 'Santosh'
            email.txn = txn
            print('data received ' + txn)
            email_txn(email,'txn_confirmation.html')
            return JsonResponse(data, safe=False)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;

    def get(self,request):
        try:
            print('get')
            txn_id = request.GET.get('txn_id')
            service_url = get_env_var('service.url') + '/txn/'+txn_id
            print(service_url + "service_url")
            resp = requests.get(service_url, auth=service_auth)
            if resp.status_code != 200:
                print(str(resp.status_code) + "error")
                response_dict = json.loads(resp.text)
            else:
                txn = ltc_srv.gettransaction(txn_id)
                print('text' + str(resp.text))
                response_dict = json.loads(resp.text)
                response_dict['status'] = txn['status']
                resp = requests.post(service_url, auth=service_auth,data=response_dict)
                if resp.status_code != 200:
                    print(str(resp.status_code) + "error")
                else:
                    print('txn_id updated' + str(resp.status_code) + " success")
            return  JsonResponse({}, safe=False)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;

