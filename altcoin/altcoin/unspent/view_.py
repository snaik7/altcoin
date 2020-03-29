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
from bitcoinlib.wallets import HDWallet


class UnspentView(APIView):

    '''
    def get(self, request):
        """
        Retrieve, update or delete a code snippet.
        """
        try:
            coin_type = request.GET.get('type')
            username = request.GET.get('username')
            if  username and coin_type :
                service_url = get_env_var('service.url')+'/address/?action=receive&type='+coin_type+'&username='+username
                print(service_url +"service_url" )
                resp = requests.get(service_url,auth=service_auth)
                if resp.status_code != 200:
                    print(str(resp.status_code) +"error" )
                    response_dict = json.loads(resp.text)
                    return JsonResponse(response_dict, safe=False)
                else:
                    print('text'+str(resp.text))
                    response_list = json.loads(resp.text)
                    address_list = []
                    for dict in response_list:
                        print("key: ", dict['address_id'], "val: ", dict['action'])
                        address_list.append(dict['address_id'])
                        print(address_list)
                    raw_data = '{"id":"0", "method":"listunspent", "params":[0,9999999, '+ str(address_list)+',true]}'
                    raw_data = raw_data.replace('\'','\"')
                    print(raw_data)
                    url = get_url(coin_type,'unspent')
                    #url = 'https://17ccc7fe-3c2b-4083-9e2f-f2fcde0bba8e.mock.pstmn.io/unspent'
                    resp = requests.post(url, auth=auth, data=raw_data)
                    print(resp.status_code)
                    if resp.status_code != 200:
                        print(resp.text)
                        response_dict = json.loads(resp.text)
                        raise ServiceException(get_env_var('exception.business.unspent.serviceexception'))
                    else:
                        response_dict = json.loads(resp.text)
                        sum = self.unspent_amount(response_dict)
                        response_dict.append({"toal_unspent" : sum})
                        return JsonResponse(response_dict, safe=False)
            else:
                raise ValidationError(get_env_var('exception.validation.unspent.no_user_or_no_coin_type'))
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            raise e
'''
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

                address_list = '|'.join([str(a) for a in wallet_address_list])
                block_service_url = get_env_var(
                    'blockchain.service.url') + '/multiaddr?active=' + address_list
                print('service_url for get balance', block_service_url)
                resp = requests.get(block_service_url)
                print('\nreceived for blcokchain multiaddr resp', resp.status_code)
                address_list = json.loads(resp.text)
                address_list =  self.getunspent(wallet_address_list,address_list,withsum)
                return JsonResponse(address_list, safe=False)
            else:
                raise ValidationError(get_env_var('exception.validation.unspent.no_wallet_or_no_network'))
        except ServiceException as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(e)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(get_env_var('exception.business.unspent.serviceexception'))




    def getunspent(self,wallet_address_list,list,withsum):

        try:
            if len(list) > 0:
                address_list = list['txs']
                #flatten the list
                flattent_address_list = []
                for wl in wallet_address_list:
                    for adr_list in address_list:
                        for in_txn in adr_list.get('inputs'):
                            if (in_txn.get('prev_out').get('addr') == wl):
                                for out in adr_list.get('out'):
                                    add_row = {}
                                    add_row['txid'] = adr_list.get('hash')
                                    add_row['vout'] = out.get('n')
                                    add_row['address'] = out.get('addr')
                                    flattent_address_list.append(add_row)
                if withsum:
                    flattent_address_list.append({"toal_unspent": list.get('wallet').get('final_balance')})

                return flattent_address_list

        except Exception as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(e)


