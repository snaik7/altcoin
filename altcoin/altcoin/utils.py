import os
import time
import traceback

from requests.auth import HTTPBasicAuth

from altcoin.errors import ValidationError


from altcoin.settings import base
from altcoin.settings.base import get_coin_env_var, get_env_var
from altcoin.settings.local import db_uri
from altcoin.user.models import User
from bitcoinlib.db import DbInit, DbNetwork
from bitcoinlib.services.bitcoind import BitcoindClient
from bitcoinlib.services.litecoind import LitecoindClient



import base64
import qrcode
import io
import pika

ltc_auth=HTTPBasicAuth(get_coin_env_var('LTC','user'), get_coin_env_var('LTC','password'))
btc_auth=HTTPBasicAuth(get_coin_env_var('BTC','user'), get_coin_env_var('BTC','password'))
service_auth=HTTPBasicAuth(get_env_var('service.user'), get_env_var('service.password'))
btc_srv = BitcoindClient()
ltc_srv = LitecoindClient()

user = os.getenv('ACTIVEMQ_USER') or 'guest'
password = os.getenv('ACTIVEMQ_PASSWORD') or 'guest'
host = os.getenv('ACTIVEMQ_HOST') or 'localhost'
#port = int(os.getenv('ACTIVEMQ_PORT') or 61613)
port = int(os.getenv('ACTIVEMQ_PORT') or 15672)

class Util:



    @staticmethod
    def sendMessage(message, destination):
        print('connect')
        connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        channel = connection.channel()
        channel.queue_declare(queue=destination,durable=True)
        channel.basic_publish(exchange='',
                              routing_key=destination,
                              body=message)
        print('message sent')
        connection.close()


    @staticmethod
    def format_10Decimal(val):
        return '{: .10f}'.format(val)

    def get_user(username):
        user = User.objects.filter(username=username)
        if user.count() > 0:
            user = user[0]
            print('username ', username, 'user_id', user.user_id)
        else:
            raise ValidationError('user does not exist in system')
        return user

    #https://github.com/jitendrapurbey/qr_api/blob/master/api/views.py
    def generate_qr_code(data, size=10, border=0):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=size, border=border)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()
        return img

    def generate_qr(url_text):
        generated_code = Util.generate_qr_code(data=url_text, size=10, border=1)
        print('generated_code',generated_code)
        bio = io.BytesIO()
        img_save = generated_code.save(bio)
        png_qr = bio.getvalue()
        base64qr = base64.b64encode(png_qr)
        img_name = base64qr.decode("utf-8")
        context_dict = dict()
        context_dict['file_type'] = "png"
        context_dict['image_base64'] = img_name
        return context_dict

    def get_network(self):
        session = DbInit(db_uri=db_uri).session
        network = session.query(DbNetwork).all()
        network_lst = []
        for n in network:
            print('network', n.name)
            network_lst.append(n.name)
        return network_lst


