from django.db import models
import requests
import json

from rest_framework.response import Response

from altcoin.settings.base import get_env_var, get_coin_env_var, get_url
from altcoin.settings.local import db_uri

from altcoin.errors import ServiceException
from altcoin.authentication import ExpiringTokenAuthentication
from altcoin.utils import btc_srv, ltc_srv


# Create your models here.
from bitcoinlib.wallets import HDWallet


class Address(models.Model):
	address_id = models.TextField(primary_key=True)
	username = models.TextField()
	action = models.TextField()
	created = models.DateTimeField(auto_now_add=True)
	network_name = models.TextField(null=False, blank=False)
	hex = models.TextField()
	private_key = models.TextField()
	public_key = models.TextField()

class AddressImpl:
	'''
	@staticmethod
	def getNewNewAddress(request):
		try:
			raw_data = get_env_var('payload.newaddress')
			print(raw_data)
			coin_type = request.GET.get('type')
			username = request.GET.get('username')
			print(coin_type + str(username))
			if coin_type == 'LTC' or coin_type == 'BTC' :
				url = get_url(coin_type,'')
				print('url ', url)
				resp = requests.post(url, auth=auth, data=raw_data)
				if resp.status_code != 200:
					raise ServiceException(get_env_var('exception.business.newaddress.serviceexception'))
				else:
					response_dict = json.loads(resp.text)
					address_id = response_dict['result']
					raw_data = get_env_var('payload.walletpassphrase')
					resp = requests.post(url, auth=auth, data=raw_data)
					if resp.status_code != 200:
						print(resp.text)
						raise ServiceException(get_env_var('exception.business.newaddress.walletpassphrase.serviceexception'))
					else:
						raw_data = '{"jsonrpc": "1.0", "id":"curltest", "method": "dumpprivkey", "params":  ["'+ address_id+'"]}'
						print('raw_data' + raw_data)
						resp = requests.post(url, auth=auth, data=raw_data)
						print(resp.status_code)
						if resp.status_code != 200:
							print(resp.text)
							raise ServiceException(get_env_var('exception.business.newaddress.dumpkey.serviceexception'))
						else:
							response_dict = json.loads(resp.text)
							private_key = response_dict['result']
							address = Address(address_id = address_id, username = username, coin_type = coin_type, action = 'receive', private_key = private_key )
							address.save()
							print(resp.status_code)
							return resp
		except Exception as e:
			raise e
	'''
	'''
	@staticmethod
	def getNewAddress(request):
		try:

			coin_type = request.GET.get('type')
			username = request.GET.get('username')
			print(coin_type + str(username))
			if coin_type == 'BTC':
				address_id = btc_srv.getnewaddress()
				private_key = btc_srv.dumpprivkey(address_id)
			elif coin_type == 'LTC':
				address_id = ltc_srv.getnewaddress()
				ltc_srv.walletpassphrase()
				private_key = ltc_srv.dumpprivkey(address_id)

			address = Address(address_id=address_id, username=username, coin_type=coin_type,
							  action='receive', private_key=private_key)
			address.save()
			return address

		except Exception as e:
			raise ServiceException(get_env_var('exception.business.newaddress.dumpkey.serviceexception'))
	'''
	@staticmethod
	def getNewAddress(account_id,wallet_id):
		try:
			wallet = HDWallet(wallet_id, db_uri=db_uri)
			address = wallet.new_key(account_id=account_id)
			address = Address(address_id=address.address, network_name=address.network_name)
			return address

		except Exception as e:
			raise ServiceException(get_env_var('exception.business.newaddress.dumpkey.serviceexception'))