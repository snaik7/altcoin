import base64

import requests
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from altcoin.address.models import Address, AddressImpl
from altcoin.address.serializers import AddressSerializer
import json
from altcoin.errors import ValidationError, AuthenticationError
from altcoin.settings.base import get_env_var
from rest_framework.views import APIView
from altcoin.utils import Util

from altcoin.settings.local import db_uri
from bitcoinlib import keys
from bitcoinlib.wallets import HDWallet
from altcoin.address.serializers import QRSerializer
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class NewAddressView(APIView):

    def get(self,request,account_id, wallet_id):
        try:
            logger.debug('Started ', self.__class__.__name__, ' get method')
            amount = request.GET.get('amount')
            qr = request.GET.get('qr')
            print('Started ', self.__class__.__name__, ' wallet_id=%s,  account_id=%s, qr=%s, amount=%s ' % (str(wallet_id), str(account_id), bool(qr), str(amount)))
            if account_id and wallet_id:
                addressimpl = AddressImpl()
                address = addressimpl.getNewAddress(account_id,wallet_id)
                if address :
                    response_dict = {'address_id' : address.address_id, 'status' : 'success' }
                    if qr :
                        text = address.network_name+':'+address.address_id+' amoount:' + str(amount)
                        output = Util.generate_qr(text)
                        print('received for  response generate_qr %s' % (output))
                        image = QRSerializer(output).data
                        response_dict['file_type'] = image['file_type']
                        response_dict['image_base64'] = image['image_base64']

                return JsonResponse(response_dict, safe=False)
            else:
                raise ValidationError(get_env_var('exception.validation.address.no_account_or_no_wallet'))
        except AuthenticationError as e:
            raise e
        except Exception as e:
            raise e

class AddressView(APIView):
    @method_decorator(cache_page(60 * 1))
    def get(self,request):

        print('Started ' + self.__class__.__name__ + ' get method')
        try:

            wallet_id = request.GET.get('wallet_id')
            just_address = request.GET.get('just_address')
            print('Started ',self.__class__.__name__ ,'  wallet_id=%s, just_address=%s ' %(str(wallet_id),
                  bool(str(just_address))))

            if wallet_id :
                wallet = HDWallet(wallet_id, db_uri=db_uri)
                keys = wallet.keys(include_private=True)
                keys = [x.__dict__ for x in keys]
                address_list = []
                if bool(just_address) == True:
                    for key in keys:
                        address_list.append(key['address'])
                else:
                    for key in keys:
                        address_list.append(
                            {'address_id': key['address'], 'private_key': key['private'], 'public_key': key['public']})
                return JsonResponse(address_list, safe=False)
            else:
                raise ValidationError(get_env_var('exception.validation.address.no_wallet'))
        except Exception as e:
            raise e




