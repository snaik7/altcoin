from django.shortcuts import render
from django.contrib.auth.models import  Group
from rest_framework import viewsets
from rest_framework import permissions
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
import requests
from rest_framework.views import APIView

from altcoin.address.models import Address
from requests.auth import HTTPBasicAuth
import json
from decimal import *
import traceback
import logging

from altcoin.address.serializers import AddressSerializer
from altcoin.errors import ServiceException, ValidationError
from altcoin.settings.local import db_uri
from altcoin.txn.models import Txn
from altcoin.txn.serializers import TxnSerializer
from altcoin.user.models import User
from altcoin.utils import service_auth, Util, btc_auth, ltc_auth, btc_srv, ltc_srv
from altcoin.settings.base import get_url, get_env_var
from bitcoinlib.db import DbInit, DbWallet, DbKey
from bitcoinlib.services.bitcoind import BitcoindClient
from bitcoinlib.transactions import Transaction

logger = logging.getLogger(__name__)


class SendView(APIView):
    def post(self,request):

        print('Started ' + self.__class__.__name__ + ' get method')
        try:
            data = JSONParser().parse(request)
            network = data.get('network')
            hex = data.get('hex')

            txn_data = {}
            txn_data['wallet_id'] = data.get('wallet_id')
            txn_data['type'] = data.get('txn_type')
            txn_data['destination'] = data.get('address_id')
            txn_data['destination_amount'] = data.get('amount')
            txn_data['message'] = data.get('message')
            txn_data['includes_fee'] = data.get('includes_fee')

            print(' txn with data' + str(data))

            if network and hex:

                if network == 'bitcoin':
                    txn_data['network'] = 'btc'
                    resp = btc_srv.sendrawtransaction(hex)
                    txn_data['network'] = 'ltc'
                elif network == 'litecoin':
                    resp = ltc_srv.sendrawtransaction(hex)
                print('\nreceived for sendrawtransaction  resp', resp.status_code, 'response %s' %(resp.text))
                
                if resp.status_code != 200:
                    Util.sendMessage(message=hex,destination='/queue/txn.failure')
                    raise ServiceException(get_env_var('exception.business.send.serviceexception'))
                else:

                    if resp.text:
                        print('saving in txn')
                        response_dict = json.loads(resp.text)
                        txn_data['txn_id'] = response_dict['result']
                        print('saving in txn with data' + str(txn_data))
                        Util.sendMessage(message=txn_data, destination='/queue/txn')
                        serializer = TxnSerializer(data=txn_data)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            return JsonResponse(serializer.errors, status=400)
                        return JsonResponse(serializer.data, status=201, safe=False)
                    else:
                        raise ServiceException(get_env_var('exception.business.send.serviceexception'))
            else:
                raise ValidationError(get_env_var('exception.validation.send.no_network_or_no_hex'))

        except Exception as e:
            track = traceback.format_exc()
            logger.exception(track)
            print("error" + str(track))
            raise e;




    def update_transaction(self,txid):
        try:
            session = DbInit(db_uri=db_uri).session
            session.query(DbKey).update({"latest_txid": txid})
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

	

