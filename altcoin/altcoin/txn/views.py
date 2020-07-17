import json
import traceback
from datetime import datetime

import requests
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from altcoin.errors import ValidationError, ServiceException
from altcoin.settings.local import db_uri, get_env_var
from altcoin.txn.models import Txn
from altcoin.txn.serializers import TxnSerializer
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from bitcoinlib.keys import Key, binascii
from bitcoinlib.services.bitcoind import BitcoindClient
from bitcoinlib.services.services import Service
from bitcoinlib.services.litecoind import LitecoindClient
from bitcoinlib.wallets import HDWallet, wallet_create_or_open, WalletError

from bitcoinlib.transactions import Transaction


# Create your views here.

class TxnView(APIView):
    @method_decorator(cache_page(60 * 1))
    def get(self, request, wallet_id):
        """
        Retrieve, update or delete a code snippet.
        """
        try:
            print('enter txn')
            txn = Txn.txn_list_wallet(db_uri=db_uri,wallet_id=wallet_id)

            print('Started ' + self.__class__.__name__ + ' get method')

            network = request.GET.get('network')

            print('Started ', self.__class__.__name__,
                  '  wallet_id=%s, network=%s ' % (str(wallet_id),
                                                              network))
            address_list = []
            if wallet_id and network:
                wallet = HDWallet(wallet_id, db_uri=db_uri)
                wallet_address_list = wallet.addresslist()
                if network == 'bitcoin':
                    address_list = '|'.join([str(a) for a in wallet_address_list])
                    block_service_url = get_env_var(
                        'blockchain.service.url') + '/multiaddr?active=' + address_list
                    print('service_url for get balance', block_service_url)
                    resp = requests.get(block_service_url)
                    print('\nreceived for blcokchain multiaddr resp', resp.status_code)
                    address_list = json.loads(resp.text)
                    address_list = self.getBitcoinTxn(address_list)
                    return JsonResponse(address_list, safe=False)
                elif network == 'litecoin':
                    address_list = ';'.join([str(a) for a in wallet_address_list])
                    blockcypher_service_url = get_env_var(
                        'blockcypher.service.url') + '/v1/ltc/main/addrs/' + address_list + '/full?token='+ get_env_var(
                        'blockcypher.service.token')
                    print('service_url for unspent balance', blockcypher_service_url)
                    resp = requests.get(blockcypher_service_url)
                    print('\nreceived for blockcypher balance resp', resp.status_code)
                    address_list = json.loads(resp.text)
                    address_list = self.getLitecoinTxn(address_list)
                    print('address_list----------',address_list)
                    return JsonResponse(address_list, safe=False)
            else:
                raise ValidationError(get_env_var('exception.validation.txn.no_wallet_or_no_network'))
        except WalletError as e:
            track = traceback.format_exc()
            print(track)
            raise e
        except ServiceException as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(e)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(get_env_var('exception.business.txn.serviceexception'))

            return JsonResponse(txn, safe=False)

        except Txn.DoesNotExist:
            return HttpResponse(status=404)




    def getBitcoinTxn(self,list):

        try:
            txn_list = []
            if len(list) > 0:
                address_list = list.get('txs')
                #flatten the list
                print('\naddress_list ', address_list)
                for adr_list in address_list:
                    for in_txn in adr_list.get('inputs'):
                        print(' in_txn ', in_txn)
                        print(' in_txn spent  ', in_txn.get('prev_out').get('spent'))
                        if bool(in_txn.get('prev_out').get('spent')) == True:
                            print(' in true')
                            add_row = {}
                            add_row['txid'] = adr_list.get('hash')
                            add_row['value'] = in_txn.get('prev_out').get('value')
                            add_row['address'] = in_txn.get('prev_out').get('addr')
                            add_row['action'] = 'send'
                            add_row['time'] = datetime.fromtimestamp(adr_list.get('time'))
                            txn_list.append(add_row)
                        else:
                            add_row = {}
                            add_row['txid'] = adr_list.get('hash')
                            add_row['value'] = in_txn.get('prev_out').get('value')
                            add_row['address'] = in_txn.get('prev_out').get('addr')
                            add_row['action'] = 'receive'
                            add_row['time'] = datetime.fromtimestamp(adr_list.get('time'))
                            txn_list.append(add_row)

                    for out in adr_list.get('out'):
                        add_row = {}
                        add_row['txid'] = adr_list.get('hash')
                        add_row['value'] = out.get('value')
                        add_row['address'] = out.get('addr')
                        add_row['action'] = 'receive'
                        add_row['time'] = datetime.fromtimestamp(adr_list.get('time'))
                        txn_list.append(add_row)


            return txn_list

        except Exception as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(e)

    def getLitecoinTxn(self,list):

        try:
            txn_list = []

            for list in list:

                if len(list) > 0:
                    address_list = list.get('txs')
                    #flatten the list
                    print('\naddress_list ', address_list)
                    for adr_list in address_list if address_list else []:
                        for in_txn in adr_list.get('inputs'):

                            print(' in_txn ', in_txn)
                            print(' in_txn addresses  ', in_txn.get('addresses'))
                            for  address in in_txn.get('addresses')  if in_txn.get('addresses')  else []:
                                print(' in true')
                                add_row = {}
                                add_row['txid'] = adr_list.get('hash')
                                add_row['value'] = in_txn.get('output_value')
                                add_row['address'] = address
                                add_row['action'] = 'send'
                                add_row['time'] = adr_list.get('received')
                                txn_list.append(add_row)

                        for out in adr_list.get('outputs'):
                            add_row = {}
                            add_row['txid'] = adr_list.get('hash')
                            add_row['value'] = out.get('value')
                            add_row['address'] = out.get('addresses')[0] if out.get('addresses') else ''
                            add_row['action'] = 'receive'
                            add_row['time'] = adr_list.get('received')
                            txn_list.append(add_row)


            return txn_list

        except Exception as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(e)

