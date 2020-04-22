import pika
import time


connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='wallet',durable=True)


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    time.sleep(4000)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='wallet', on_message_callback=callback, auto_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
