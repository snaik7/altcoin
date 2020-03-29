from django.shortcuts import render
from django.contrib.auth.models import Group
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
from bitcoinlib.services.bitcoind import BitcoindClient

from bitcoinlib.wallets import HDWallet, get_wallet

logger = logging.getLogger(__name__)


class SignSendView(APIView):
    def post(self, request):
        """
        Retrieve, update or delete a code snippet.
        """
        print("enter sign and send")
        try:
            data = JSONParser().parse(request)
            wallet_id = data.get('wallet_id')
            username = data.get('username')
            hex = data.get('hex')
            coin_type = data.get('type')

            txn_data = {}
            txn_data['username'] = data.get('username')
            txn_data['type'] = data.get('txn_type')
            txn_data['status'] = data.get('status')
            txn_data['source'] = data.get('source')
            txn_data['source_amount'] = data.get('source_amount')
            txn_data['source_currency'] = data.get('source_currency')
            txn_data['destination'] = data.get('destination')
            txn_data['destination_amount'] = data.get('destination_amount')
            txn_data['destination_currency'] = data.get('destination_currency')
            txn_data['message'] = data.get('message')
            txn_data['includes_fee'] = data.get('includes_fee')

            print(' txn with data' + str(data))

            if username and coin_type and hex:
                print(username + "username")
                service_url = get_env_var('service.url') + '/key/?wallet_id=' + str(wallet_id) + '&type=' + coin_type
                print(service_url + "service_url")
                resp = requests.get(service_url, auth=service_auth)
                if resp.status_code != 200:
                    print('address response', resp.text)
                    raise ServiceException(get_env_var('exception.business.sign.serviceexception'))
                else:
                    print('address response', resp.text)
                    response_list = json.loads(resp.text)
                    sign_dict_str = self.sign_txn(hex, response_list)
                    print('sign request ' + sign_dict_str)
                    url = get_url(coin_type, "signtxn")
                    # url = 'https://66f49c90-24e2-4d2b-891d-5746233c8ae7.mock.pstmn.io/sign'
                    if coin_type == 'BTC':
                        resp = requests.post(url, auth=btc_auth, data=sign_dict_str)
                    elif coin_type == 'LTC':
                        resp = requests.post(url, auth=ltc_auth, data=sign_dict_str)

                    print(resp.status_code)
                    if resp.status_code != 200:
                        print('sign response ' + resp.text)
                        raise ServiceException(get_env_var('exception.business.sign.serviceexception'))
                    else:
                        print('sign response ' + resp.text)
                        send_dict = json.loads(resp.text)
                        send_dict_str = self.send_txn(hex, send_dict)
                        url = get_url(coin_type, 'sendtxn')

                        # url = 'https://66f49c90-24e2-4d2b-891d-5746233c8ae7.mock.pstmn.io/send'
                        if coin_type == 'BTC':
                            resp = requests.post(url, auth=btc_auth, data=send_dict_str)
                        elif coin_type == 'LTC':
                            resp = requests.post(url, auth=ltc_auth, data=send_dict_str)

                        print(resp.status_code)
                        if resp.status_code != 200:
                            print('send error response ' + resp.text + ' with status code' + str(resp.status_code))
                            Util.sendMessage('send', '/queue/test')
                            raise ServiceException(get_env_var('exception.business.send.serviceexception'))
                        else:
                            print('send suucess response ' + resp.text + ' with status code' + str(resp.status_code))
                            Util.sendMessage('send', '/queue/test')
                            if resp.text:
                                print('saving in txn')
                                txn_data['txn_id'] = resp.text
                                serializer = TxnSerializer(data=txn_data)
                                if serializer.is_valid():
                                    serializer.save()
                                else:
                                    print('data invalid')
                                    return JsonResponse(serializer.errors, status=400)
                                return JsonResponse(serializer.data, status=201, safe=False)
                            else:
                                raise ServiceException(get_env_var('exception.business.send.serviceexception'))

            else:
                raise ValidationError(get_env_var('exception.validation.sign.no_user_or_no_coin_type_or_no_hex'))
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;

    def sign_txn(self, hex, response_list):
        adr_list = response_list
        '''
        for dict in response_list:
            print("key: ", dict['private_key'], "address: ", dict['address_id'])
            adr_list.append(dict['private_key'])
        '''
        print('adr_list')
        print(adr_list)
        send_dict = {"id": 0, "method": "signrawtransactionwithkey"}
        sendtxn_list = []
        # hex_list = []
        # hex_list.append(hex)
        sendtxn_list.append(hex)
        sendtxn_list.append(adr_list)
        send_dict['params'] = sendtxn_list
        send_dict_str = str(send_dict)
        send_dict_str = send_dict_str.replace('\'', '\"')
        return send_dict_str

    def send_txn(self, hex, send_dict):
        hex_list = []
        hex_list.append(hex)
        send_dict['params'] = hex_list
        send_dict_str = str(send_dict)
        send_dict_str = send_dict_str.replace('\'', '\"')
        return send_dict_str


class SignView(APIView):
    def post(self, request):
        print("enter sign and send")
        try:
            data = JSONParser().parse(request)
            username = data.get("username")
            hex = data.get("hex")
            coin_type = data.get("type")
            if username and coin_type and hex:
                print(username + "username")
                service_url = get_env_var(
                    'service.url') + '/address/?action=receive&username=' + username + '&type=' + coin_type
                print(service_url + "service_url")
                resp = requests.get(service_url, auth=service_auth)
                if resp.status_code != 200:
                    print('address response', resp.text)
                    raise ServiceException(get_env_var('exception.business.sign.serviceexception'))
                else:
                    print('address response', resp.text)
                    response_list = json.loads(resp.text)
                    signsend = SignSendView()
                    sign_dict_str = signsend.sign_txn(hex, response_list)
                    print('sign request ' + sign_dict_str)
                    url = get_url(coin_type, "signtxn")
                    # url = 'https://66f49c90-24e2-4d2b-891d-5746233c8ae7.mock.pstmn.io/sign'

                    if coin_type == 'BTC':
                        resp = requests.post(url, auth=btc_auth, data=sign_dict_str)
                    elif coin_type == 'LTC':
                        resp = requests.post(url, auth=ltc_auth, data=sign_dict_str)
                    print(resp.status_code)
                    if resp.status_code != 200:
                        print('sign response ' + resp.text)
                        raise ServiceException(get_env_var('exception.business.sign.serviceexception'))
                    else:
                        print('sign response ' + resp.text)
                        response_dict = json.loads(resp.text)
                        return JsonResponse(response_dict, safe=False)

            else:
                raise ValidationError(get_env_var('exception.validation.sign.no_user_or_no_coin_type_or_no_hex'))
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(resp.status_code))
            raise e;


class SendView(APIView):
    def post(self, request):

        print('Started ' + self.__class__.__name__ + ' get method')
        try:
            data = JSONParser().parse(request)
            network = data.get('network')
            hex = data.get('hex')

            txn_data = {}

            txn_data['type'] = data.get('txn_type')
            txn_data['destination'] = data.get('address_id')
            txn_data['destination_amount'] = data.get('amount')
            txn_data['message'] = data.get('message')
            txn_data['includes_fee'] = data.get('includes_fee')

            print(' txn with data' + str(data))

            if network and hex:

                if network == 'bitcoin':
                    resp = btc_srv.sendrawtransaction(hex)
                elif network == 'litecoin':
                    resp = ltc_srv.sendrawtransaction(hex)
                print('\nreceived for sendrawtransaction  resp', resp.status_code, 'response %s' % (resp.text))

                if resp.status_code != 200:
                    Util.sendMessage('send', '/queue/test')
                    raise ServiceException(get_env_var('exception.business.send.serviceexception'))
                else:
                    Util.sendMessage('send', '/queue/test')
                    if resp.text:
                        print('saving in txn')
                        response_dict = json.loads(resp.text)
                        txn_data['txn_id'] = response_dict['result']
                        print('saving in txn with data' + str(txn_data))
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


class WalletSendView(APIView):
    def post(self, request):
        print("enter wallet send")
        try:
            data = JSONParser().parse(request)
            wallet_id = data.get('wallet_id')
            address = data.get('address')
            amount = data.get('amount')
            print('wallet_id ' + str(wallet_id))
            print('address ' + str(address))
            '''
            print('wallet starts')
            srv = BitcoindClient()
            print(srv.getutxos('1CRkjhJgWC6tPNdfqnXRgYDPniSScHenuP'))
            print('bitcoin fee created')
            '''

            wallet = HDWallet(wallet_id, db_uri=db_uri)
            print(' wallet.username ', wallet.key_for_path('m/44\'/0\'/1\'/0/0'))

            user = User.objects.filter(username=wallet.username)
            print('user', user)
            if user.count() > 0:
                user = user[0]
                print('wallets  ', wallet, ' user_id ', user.user_id)

                from_wallet_key = wallet.key(wallet.name)
                print('from wallet key', from_wallet_key.key_id)
                print('to wallet key as same ', wallet.key(address))

                # print('performing txn update  update db')
                # wallet.transactions_update(account_id=user.user_id,key_id=from_wallet.key_id)

                utx = wallet.utxos_update(account_id=user.user_id)
                wallet.info()
                wallet.get_key()
                print('key change', wallet.get_key_change())
                utxos = wallet.utxos(account_id=user.user_id)
                res = wallet.send_to(address, amount)
                print("Send transaction result:")
                if res.hash:
                    print("Successfully send, tx id:", res.hash)
                else:
                    print("TX not send, result:", res.errors)

                return JsonResponse(res.as_dict(), safe=False)

        except Exception as e:
            track = traceback.format_exc()
            logger.exception(track)
            raise e;







