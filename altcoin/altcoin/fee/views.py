from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
import requests
from altcoin.address.models import Address
from requests.auth import HTTPBasicAuth
import json
import traceback
from rest_framework.views import APIView
from altcoin.authentication import ExpiringTokenAuthentication
from altcoin.settings.base import get_env_var, get_coin_env_var, get_url
from altcoin.settings.local import db_uri
from altcoin.utils import service_auth, btc_srv, ltc_srv
from altcoin.errors import ValidationError, ServiceException
from altcoin.utils import ltc_auth, Util, btc_auth
from bitcoinlib.keys import Key, binascii
from bitcoinlib.transactions import Output, Transaction
from bitcoinlib.wallets import HDWallet


class FeeView(APIView):

    def post(self, request):
        print('Started ' + self.__class__.__name__ + ' get method')
        try:

            data = JSONParser().parse(request)
            network = data.get('network')
            output_address = data.get('address_id')
            wallet_id = data.get('wallet_id')
            send_amount = int(data.get('amount'))


            print('Started ', self.__class__.__name__, '  wallet_id=%s, withsum=%s, network=%s ' % (str(wallet_id),
                                                                                                      (str(
                                                                                                        output_address)),
                                                                                                      network))

            wallet = HDWallet(wallet_id, db_uri=db_uri)
            change_address = wallet.get_key_change()
            change_address = change_address.address
            print('change_address ', change_address)

            if wallet_id:
                service_url = get_env_var('service.url') + '/unspent/?wallet_id=' + str(wallet_id) + '&network=' + network
                print('service_url for  unspent', service_url)
                resp = requests.get(service_url, auth=service_auth)
                print('received status code for unspent resp', resp.status_code, ' and response %s' % (resp.text))
                if resp.status_code != 200:
                    raise ServiceException(get_env_var('exception.business.fee.serviceexception'))
                else:
                    wallet_address_list = json.loads(resp.text)

                service_url = get_env_var(
                    'service.url') + '/address/?wallet_id=' + str(wallet_id)
                print('service_url for  address', service_url)
                resp = requests.get(service_url, auth=service_auth)
                print('received status code for address resp', resp.status_code )
                if resp.status_code != 200:
                    private_input_address_list = json.loads(resp.text)
                    return JsonResponse(private_input_address_list, safe=False)
                else:
                    private_input_address_list = json.loads(resp.text)
                    blocks = 2
                    fee_per_kb = 0
                    if network == 'bitcoin':
                        fee_per_kb = btc_srv.estimatefee(blocks)
                    elif network == 'litecoin':
                        fee_per_kb = ltc_srv.estimatefee(blocks)

                    print('Fee per kb %s' %(str(fee_per_kb)))

                    t = self.create_transaction(wallet_address_list, private_input_address_list, output_address,
                                                change_address, send_amount, fee_per_kb,network)

                    return JsonResponse(t.as_dict(), safe=False)



            else:
                raise ValidationError(get_env_var('exception.validation.fee.no_coin_type'))
        except ServiceException as e:
            track = traceback.format_exc()
            print(track)
            raise ServiceException(e)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            return HttpResponse(status=404)

    def create_transaction(self, wallet_address_list, private_input_address_list, output_address, change_address, send_amount,
                           fee_per_kb,network):
        try:

            print('Create and sign  Transaction with Multiple INPUTS using keys from Wallet class ')
            charge_back_amount = 0
            print('Dummy transaction with Outputs ')
            transaction_outputs = [Output(send_amount, address=output_address, network=network),
                                   Output(charge_back_amount, address=change_address, network=network)
                                   ]
            print('transaction_outputs', transaction_outputs)
            print('created dummy txn for fee calc')
            t = Transaction(outputs=transaction_outputs, network=network, fee_per_kb=fee_per_kb)
            print('Fee with o/p  ', t.calculate_fee())
            fee = t.calculate_fee()
            charge_back_amount = send_amount - fee
            '''
            if charge_back_amount < 0:
                raise ServiceException('Insufficient fund to continue transaction')
            '''
            print('created real txn for fee calc')
            transaction_outputs = [Output(send_amount, address=output_address, network=network),
                                   Output(charge_back_amount, address=change_address, network=network)
                                   ]
            print('transaction_outputs', transaction_outputs)
            transaction_inputs = []
            for input in wallet_address_list:
                transaction_inputs.append(
                    (input['txid'], int(input['vout']), self.json_get(private_input_address_list, input['address'])))
            print('transaction_inputs', transaction_inputs)
            t.fee = t.calculate_fee()
            print('Fee with ip/ op ', t.fee)

            for ti in transaction_inputs:
                ki = Key(ti[2], network=network)
                t.add_input(prev_hash=ti[0], output_n=ti[1], keys=ki.public())
            icount = 0
            for ti in transaction_inputs:
                ki = Key(ti[2], network=network)
                t.sign(ki.private_byte, icount)
                icount += 1

            print('\nRaw Signed Transaction %s' % binascii.hexlify(t.raw()))
            print('\nVerified %s' % t.verify())

            print('------------info-----------')
            t.info()
            print('------------end-----------')
        except Exception as e:
            raise e

        return t;



    def json_get(self, private_input_address_list, address):
        for dict in private_input_address_list:
            if 'address_id' in dict and dict.get('address_id') == address:
                return dict['private_key']

    def fund_raw(self, hex, response_dict, change_address):

        print("{:.8f}".format(response_dict.get("result").get("feerate")))
        fundraw_dict = {"id": 0, "method": "fundrawtransaction"}
        fee_dict = {}
        fee_dict['feeRate'] = "{:.8f}".format(response_dict.get("result").get("feerate"))
        fee_dict['changeAddress'] = change_address
        fundraw_list = []
        fundraw_list.append(hex.get("result"))
        fundraw_list.append(fee_dict)
        fundraw_dict['params'] = fundraw_list
        print(fundraw_dict)
        return fundraw_dict;
        '''
        fundraw_dict_str = str(fundraw_dict)
        print('before fundraw_dict_str =>' + fundraw_dict_str)
        fundraw_dict_str = fundraw_dict_str.replace('\'', '\"')
        print('fundraw_dict_str =>' + fundraw_dict_str)
        return fundraw_dict_str
        '''

    def createraw(self, response_list,address_list):
        print('response_list - >',response_list)
        txn_dict = {}
        receiver_address_dict = {}
        sender_address_dict = {}
        txn_list = []
        adr_list = [None] * 2
        for dict in response_list:

            print("key: ", dict['txid'], "val: ", dict['vout'])
            txn_dict['txid'] = dict['txid']
            txn_dict['vout'] = dict['vout']
            print(txn_dict)
            txn_list.append(txn_dict)

        receiver_dict = address_list['receiver']
        for dict in receiver_dict:
            receiver_address_dict[dict['address_id']] = float(dict['amount'])
            adr_list[0]=receiver_address_dict
        sender_dict = address_list['sender']
        for dict in sender_dict:
            sender_address_dict[dict['address_id']] = float(dict['amount'])
            adr_list[1]=sender_address_dict

        print('adr_list ', adr_list)
        print('txn list')
        print(txn_list)
        print('adr list')
        print(adr_list)
        print("rawtxn_list")
        rawtxn_list = []
        rawtxn_list.append(txn_list)
        rawtxn_list.append(adr_list)
        print(rawtxn_list)
        createraw_dict = {"id": 0, "method": "createrawtransaction"}
        createraw_dict['params'] = rawtxn_list
        createraw_dict_str = str(createraw_dict)
        print('before createraw_dict =>' + createraw_dict_str)
        createraw_dict_str = createraw_dict_str.replace('\'', '\"')
        print('createraw_dict =>' + createraw_dict_str)
        return createraw_dict_str



'''   
    def post(self,request,pk):
        print('Started ' + self.__class__.__name__ + ' get method')
        try:

            data = JSONParser().parse(request)
            coin_type = data.get('type')
            output_address = data.get('address_id')
            wallet_id = data.get('wallet_id')
            send_amount = data.get('amount')

            print('Started ', self.__class__.__name__, '  wallet_id=%s, withsum=%s, coin_type=%s ' % (str(wallet_id),
                                                                                             (str(output_address)),coin_type))


            wallet = HDWallet(wallet_id, db_uri=db_uri)
            change_address = wallet.get_key_change()
            print('change_address ', change_address)

            print('change_address -------> ' + str(change_address))
            if wallet_id:
                url = get_env_var('service.url')+'/unspent/?wallet_id='+str(wallet_id)+'&type='+coin_type
                print('------------------------'+ url +"  ------------  url" )
                resp = requests.get(url,auth=service_auth)
                if resp.status_code != 200:
                    print(resp.text)
                    raise ServiceException(get_env_var('exception.business.fee.serviceexception'))
                else:
                    response_list = json.loads(resp.text)
                print('response list' + str(response_list))

                service_url = get_env_var(
                    'service.url') + '/address/?wallet_id=' + str(wallet_id)
                print(service_url + "service_url")
                resp = requests.get(service_url, auth=service_auth)
                if resp.status_code != 200:
                    print(str(resp.status_code) + "error")
                    private_input_address_list = json.loads(resp.text)
                    return JsonResponse(private_input_address_list, safe=False)
                else:
                    #print('text' + str(resp.text))
                    private_input_address_list = json.loads(resp.text)

                    # address_list = str(address_list).replace('\'', '\"')

                    print('private_address_list ', private_input_address_list)
                    blocks = 2
                    fee_per_kb = 0
                    if coin_type == 'BTC':
                        fee_per_kb = btc_srv.estimatefee(blocks)
                    elif coin_type == 'LTC':
                        fee_per_kb = ltc_srv.estimatefee(blocks)

                    print('fee per kb -----------> ' + str(fee_per_kb))

                    t = self.create_transaction(response_list, private_input_address_list, output_address, change_address, send_amount,fee_per_kb)



                    return JsonResponse(t.as_dict(), safe=False)

                createraw_dict_str = self.createraw(response_list, address_list)
                url = get_url(coin_type,'createraw')
                print("   create  url" + url)
                #url = 'https://bbc4c13c-28a9-4406-925e-87384365d172.mock.pstmn.io/rawtransaction'
                print('createraw resquest', createraw_dict_str)
                print(url + " url")

                if coin_type == 'BTC':
                    resp = requests.post(url, auth=btc_auth, data=createraw_dict_str)
                elif coin_type == 'LTC':
                    resp = requests.post(url, auth=ltc_auth, data=createraw_dict_str)
                print('error code '+ str(resp.status_code) )
                if resp.status_code != 200:
                    print('error')
                    print('createraw response',resp.text)
                    raise ServiceException(get_env_var('exception.business.fee.serviceexception'))
                else:
                    print('success ')
                    print('createraw response', resp.text)
                    hex = json.loads(resp.text)
                    blocks = 2
                    url = get_url(coin_type,'')
                    raw_data = '{"jsonrpc": "1.0", "id":"curltest", "method": "estimatesmartfee", "params":  { "conf_target": '+ str(blocks)+'}}'
                    print('estimatesmartfee request',raw_data)
                    if coin_type == 'BTC':
                        resp = requests.post(url, auth=btc_auth, data=raw_data)
                    elif coin_type == 'LTC':
                        resp = requests.post(url, auth=ltc_auth, data=raw_data)
                    if resp.status_code != 200:
                        print('estimatesmartfee response',resp.text)
                        raise ServiceException(get_env_var('exception.business.fee.serviceexception'))
                    else:
                        print('estimatesmartfee response',resp.text)
                        response_dict = json.loads(resp.text)

                        if coin_type == 'BTC':
                            fee = btc_srv.estimatefee(blocks)
                        elif coin_type == 'LTC':
                            fee = ltc_srv.estimatefee(blocks)

                        print('fee ----> ' + str(fee))
                        fundraw_dict_str = self.fund_raw(hex, response_dict, change_address)
                        url = get_url(coin_type,'fundraw')
                        #url = 'https://13a3da66-9f25-499e-a7e3-1f5bd7292f24.mock.pstmn.io/fundraw'
                        print('fundraw request', fundraw_dict_str)
                        return JsonResponse(fundraw_dict_str, safe=False)

                        if coin_type == 'BTC':
                            resp = requests.post(url, auth=btc_auth, data=fundraw_dict_str)
                        elif coin_type == 'LTC':
                            resp = requests.post(url, auth=ltc_auth, data=fundraw_dict_str)
                        print(resp.status_code)
                        if resp.status_code != 200:
                            print('fundraw response', resp.text)
                            raise ServiceException(get_env_var('exception.business.fee.serviceexception'))
                        else:
                            print('fundraw response', resp.text)
                            response_dict = json.loads(resp.text)
                            fee = response_dict['fee']
                            response_dict['fee'] = Util.format_10Decimal(fee)
                            print(response_dict,'JsonResponse')
                            return JsonResponse(response_dict, safe=False)
                         

            else:
                raise ValidationError(get_env_var('exception.validation.fee.no_coin_type'))

        except Exception as e:
            track = traceback.format_exc()
            print(track)
            return HttpResponse(status=404)
'''


