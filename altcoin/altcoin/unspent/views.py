from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
import requests
from altcoin.address.models import Address
from altcoin.settings.base import get_env_var, get_coin_env_var, get_url
import json
import traceback
from rest_framework.views import APIView
from altcoin.errors import ServiceException, ValidationError
from altcoin.authentication import ExpiringTokenAuthentication
from altcoin.settings.local import db_uri
from altcoin.utils import btc_srv, ltc_srv, service_auth
from bitcoinlib.wallets import HDWallet, WalletError


class UnspentView(APIView):

    def get(self, request):

        print('Started ' + self.__class__.__name__ + ' get method')
        try:
            network = request.GET.get('network')
            wallet_id = request.GET.get('wallet_id')
            withsum = request.GET.get('withsum')
            withsum = bool(withsum)
            print('Started ', self.__class__.__name__, '  wallet_id=%s, withsum=%s, network=%s ' % (str(wallet_id),
                                                                                             bool(str(withsum)),network))
            address_list = []
            if  wallet_id and network :
                wallet = HDWallet(wallet_id, db_uri=db_uri)
                wallet_address_list = wallet.addresslist()
                print('Wallet=%s, with unspent value=%s' %(wallet_id,str(wallet.balance())))
                print('wallet_address_list',str(wallet_address_list))
                if len(wallet_address_list) > 0:
                    if network == 'bitcoin':
                        address_list = '|'.join([str(a) for a in wallet_address_list])
                        block_service_url = get_env_var(
                            'blockchain.service.url') + '/multiaddr?active=' + address_list
                        print('service_url for get balance', block_service_url)
                        resp = requests.get(block_service_url)
                        print('\nreceived for blcokchain multiaddr resp', resp.status_code)
                        address_list = json.loads(resp.text)
                        address_list = self.getunspent(wallet_address_list, address_list, withsum,network)
                    elif network == 'litecoin':
                        address_list = ';'.join([str(a) for a in wallet_address_list])
                        blockcypher_service_url = get_env_var(
                            'blockcypher.service.url') + '/v1/ltc/main/addrs/' + address_list+ '/full'
                        print('service_url for unspent balance', blockcypher_service_url)
                        resp = requests.get(blockcypher_service_url)
                        print('\nreceived for blockcypher balance resp', resp.status_code)
                        address_list = json.loads(resp.text)
                        address_list = self.getunspent(wallet_address_list, address_list, withsum,network)


                    return JsonResponse(address_list, safe=False)
                else:
                    address_list = self.getunspent([], address_list, withsum)
                    return JsonResponse(address_list, safe=False)

            else:
                raise ValidationError(get_env_var('exception.validation.unspent.no_wallet_or_no_network'))
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
            raise ServiceException(get_env_var('exception.business.unspent.serviceexception'))




    def getunspent(self,wallet_address_list,list,withsum,network):
        try:
            if network == 'litecoin':
                flattent_address_list = []
                final_balance = 0
                for list in list:
                    if len(list) > 0:
                        address_list = list.get('txs')
                        #flatten the list

                        for wl in wallet_address_list:
                            for adr_list in address_list if address_list else [] :
                                print('adr_list',adr_list)
                                for address in adr_list.get('addresses'):
                                    print('address', address , 'wl', wl )
                                    if ( address and address == wl):
                                        print('match -------------------------------')
                                        count = 0
                                        for out in adr_list.get('outputs'):
                                            print('match ----------------------------' + str(out))
                                            add_row = {}
                                            add_row['txid'] = adr_list.get('hash')
                                            add_row['vout'] = count
                                            add_row['address'] =  out.get('addresses')[0] if out.get('addresses') else ''
                                            print('add_row-----------', add_row)
                                            count = count + 1
                                            flattent_address_list.append(add_row)
                                            print('\nflattent_address_list-----------',flattent_address_list)

                    if withsum :
                        final_balance = final_balance + (list.get('final_balance') if list.get('final_balance') else 0)

                if withsum:
                    flattent_address_list.append({"toal_unspent": final_balance})

            elif network == 'bitcoin':
                if len(list) > 0:
                    address_list = list['txs']
                    # flatten the list
                    flattent_address_list = []
                    for wl in wallet_address_list:
                        for adr_list in address_list:
                            for in_txn in adr_list.get('inputs'):
                                #if (in_txn.get('prev_out') and in_txn.get('prev_out').get('addr') == wl):
                                for out in adr_list.get('out'):
                                    if (out and out.get('addr') == wl):
                                        add_row = {}
                                        add_row['txid'] = adr_list.get('hash')
                                        add_row['vout'] = out.get('n')
                                        add_row['address'] = out.get('addr')
                                        flattent_address_list.append(add_row)

                if withsum and list.get('wallet') :
                    flattent_address_list.append({"toal_unspent": list.get('wallet').get('final_balance')})

            return flattent_address_list

        except Exception as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(e)


