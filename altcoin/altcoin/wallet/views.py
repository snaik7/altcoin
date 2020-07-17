import traceback

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from altcoin.user.models import User
from altcoin.utils import Util

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from altcoin.wallet.serializers import WalletSerializer
from bitcoinlib.services.bitcoind import BitcoindClient
from bitcoinlib.services.services import Service
from bitcoinlib.services.litecoind import LitecoindClient
from bitcoinlib.wallets import HDWallet, wallet_create_or_open, wallets_list, wallets_list_user, wallet_delete, \
    rename_wallet, get_wallet
from altcoin.settings.local import db_uri
from bitcoinlib.transactions import Transaction
from bitcoinlib.wallets  import DbWallet
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger('app_logger')

# Create your views here.

class WalletListView(APIView):
    @method_decorator(cache_page(60 * 1))
    def get(self,request):
        try:
            network = request.GET.get('network')
            logger.info('Started -------- ' + self.__class__.__name__ + ' get method ')
            username = request.GET.get('username')
            print('Started ' + self.__class__.__name__ + ' get method %s' %(username))
            wallets_list = []
            if network == 'bitcoin':
                wallets_list = wallets_list_user(db_uri=db_uri,username=username,network=network)
            elif network == 'litecoin':
                wallets_list = wallets_list_user(db_uri=db_uri,username=username,network=network)

            return JsonResponse(wallets_list, safe=False)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;

class WalletView(APIView):
    def get(self,request,pk):
        try:
            network = request.GET.get('network')
            print('Started ' + self.__class__.__name__ + ' get method ')
            username = request.GET.get('username')
            print('Started ' + self.__class__.__name__ + ' get method %s' %(network))
            if network == 'bitcoin':
                wallets_list = get_wallet(wallet_id=pk,db_uri=db_uri)
            elif network == 'litecoin':
                wallets_list = get_wallet(db_uri=db_uri,username=username)

            return JsonResponse(wallets_list, safe=False)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;


    def post(self, request):
        try:
            print('Started ' + self.__class__.__name__ + ' post method ')
            data = JSONParser().parse(request)
            username = data.get('username')
            print('Wallet creation for username=', username)
            serializer = WalletSerializer(data=data)
            if serializer.is_valid():
                user = Util.get_user(username)
                if data.get('network') == 'bitcoin' :
                    w = wallet_create_or_open(data.get('wallet_name'), network = 'bitcoin', username=data.get('username'), account_id=user.user_id, db_uri=db_uri)
                elif data.get('network') == 'litecoin' :
                    w = wallet_create_or_open(data['wallet_name'], network='litecoin', username=data.get('username'), account_id=user.user_id, db_uri=db_uri)

                w.utxos_update()
                w.info(detail=3)
                print ('wallet ', w)
                print('w.get_key()' , w.get_key())
                print('w.get_key().address ' , w.get_key().address)
                return JsonResponse(serializer.data, status=201)
            else:
                response_dict = {
                    'status': 'error',
                    # the format of error message determined by you base exception class
                    'msg': serializer.errors
                }
                return JsonResponse(response_dict, status=400)

        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;


    def patch(self, request,pk):
        try:
            data = JSONParser().parse(request)
            wallet_name = data.get('wallet_name')
            network = data.get('network')
            print('Started ' + self.__class__.__name__ + ' patch method ')
            print('Started ' + self.__class__.__name__ + ' patch method network= %s, name= %s' % (network,wallet_name))
            if network == 'bitcoin':
                wallet = rename_wallet(wallet_id=pk,db_uri=db_uri, name=wallet_name)
            elif network == 'litecoin':
                wallet = rename_wallet(wallet_id=pk,db_uri=db_uri, name=wallet_name)

            return JsonResponse(wallet, safe=False)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;

    def delete(self, request,pk):
        try:
            print('Started ' + self.__class__.__name__ + ' delete method %s' % (request.data))
            wallet_delete(pk, db_uri=db_uri)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;
        return HttpResponse(status=204)



