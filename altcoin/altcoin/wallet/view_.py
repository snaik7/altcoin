import traceback

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
from bitcoinlib.wallets import HDWallet, wallet_create_or_open, wallets_list, wallets_list_user, wallet_delete
from altcoin.settings.local import db_uri
from bitcoinlib.transactions import Transaction
from bitcoinlib.wallets import DbWallet


# Create your views here.

class WalletView(APIView):
    def get(self, request):
        username = request.GET.get('username')

        wallets_list = wallets_list_user(db_uri=db_uri, username=username)
        print('wallets ', wallets_list_user)
        return JsonResponse(wallets_list, safe=False)

    def post(self, request):
        try:

            data = JSONParser().parse(request)
            print('username ', data['username'])
            user = Util.get_user(data['username'])
            serializer = WalletSerializer(data=data)
            if serializer.is_valid():
                print('username ', data['username'])
                if data['type'] == 'BTC':
                    w = wallet_create_or_open(data['wallet_name'], network='bitcoin', username=data['username'],
                                              account_id=user.user_id, db_uri=db_uri)
                    w.utxos_update()
                    w.info(detail=3)
                elif data['type'] == 'LTC':
                    w = wallet_create_or_open(data['wallet_name'], network='litecoin', username=data['username'],
                                              account_id=user.user_id, db_uri=db_uri)
                    w.utxos_update()
                    w.info(detail=3)
                print('wallet ', w)
                print('w.get_key()', w.get_key())
                print('w.get_key().address ', w.get_key().address)
                return JsonResponse(serializer.data, status=201)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;
            return HttpResponse(status=404)
        return JsonResponse(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            wallet_delete(pk, db_uri=db_uri)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e;
            return HttpResponse(status=404)
        return HttpResponse(status=204)


class WalletTest(APIView):
    def get(self, request):
        try:

            srv = Service(providers=['blockchair'])
            print(srv.estimatefee(5))
            print('fee created')

            print('wallet starts')
            srv = LitecoindClient()
            print(srv.estimatefee(5))
            print('litecoin fee created')

            print('new adress', srv.getnewaddress())

            # tx = srv.getutxos('LbLCMRq2oiNgxxesrg7SoCBAMsAAMTqmB9')

            print('wallet starts')
            srv = BitcoindClient()
            print(srv.estimatefee(5))
            print('bitcoin fee created')

            print('bitcoin new adress', srv.getnewaddress())

            print('wallet created in local')
            db_uri = 'postgresql://postgres:postgres@localhost:5432/altcoin'
            w = wallet_create_or_open('wallet_mysql3', db_uri=db_uri)
            print('wallet created in remote')
            # w = HDWallet.create('Walletmsql1',)
            print('wallet created')
        except Exception:
            track = traceback.format_exc()
            print('-------track start--------')
            print(track)
            print('-------track end--------')

            return HttpResponse(status=404)
        return JsonResponse('', status=400, safe=False)









