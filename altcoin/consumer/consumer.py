import json
import os
import sys

import pika
import time

import requests



from requests.auth import HTTPBasicAuth



connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='wallet',durable=True)

channel.queue_declare(queue='txn',durable=True)

with open(os.environ.get('MYSITE_CONFIG')) as f:
    configs = json.loads(f.read())


def get_env_var(setting, configs=configs):
    try:
        val = configs[setting]
        if val == 'True':
            val = True
        elif val == 'False':
            val = False
        return val
    except KeyError:
        error_msg = "ImproperlyConfigured: Set {0} environment      variable".format(setting)
        raise Exception(error_msg)


service_auth=HTTPBasicAuth(get_env_var('service.user'), get_env_var('service.password'))

def callback_wallet(ch, method, properties, message):
    print(" [x] Received %r" % message)
    # comment this out if you dont want to print all msgs to console
    print(message)
    if message:
        message = str(message.decode())
        print('received an message "%s"' % str(message))
        message = message.replace('\'', '\"')
        message_dict = json.loads(message)

        username = message_dict.get('username')

        print('network', str(get_env_var('network')))

        for network in eval(get_env_var('network')):
            service_url = get_env_var(
                'service.url') + '/wallet/'
            print('service_url for wallet creation ', service_url)
            data_dict = {}
            data_dict['username'] = username
            data_dict['network'] = network
            data_dict['wallet_name'] = username + '_' + network
            data_dict_str = str(data_dict)
            data_dict_str = data_dict_str.replace('\'', '\"')
            print('request', data_dict_str)
            headers_dict = {}
            headers_dict['auth'] = 'false'
            resp = requests.post(service_url, auth=service_auth, data=data_dict_str, headers=headers_dict)
            print('received for wallet creation resp', resp.status_code, ' and response %s' % (resp.text))

def callback_txn(ch, method, properties, message):
    # comment this out if you dont want to print all msgs to console
    print(message)
    if message :
        message = str(message.decode())
        print('received an message "%s"' % str(message))

        message = message.replace('\'', '\"')
        message_dict = json.loads(message)

        network = message_dict.get('network')
        txn_id = message_dict.get('txn_id')


        if message:
            blockcypher_service_url = get_env_var(
                'blockcypher.service.url') + '/v1/'+network+'/main/hooks?token='+get_env_var(
                'blockcypher.service.token')
            print('service_url for blockcypher_service_url web hook ', blockcypher_service_url)


            data_dict = {}
            data_dict['event'] = 'confirmed-tx'
            data_dict['hash'] = txn_id
            data_dict['url'] = get_env_var('txn.confirmed.webhook.url')
            data_dict_str = str(data_dict)
            data_dict_str = data_dict_str.replace('\'', '\"')
            print('request', data_dict_str)
            resp = requests.post(blockcypher_service_url,data=data_dict_str )
            print('received for webhook creation resp', resp.status_code, ' and response %s' % (resp.text))


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='wallet', on_message_callback=callback_wallet, auto_ack=True)
channel.basic_consume(queue='txn', on_message_callback=callback_txn, auto_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()









