# altcoin
Altcoin repo provide api  to receive and send bitcoin and litecoin

We have used bitcoinlib (https://pypi.org/project/bitcoinlib/) extensively for transactions. However, we have customized the library for our requirments. Read more about library.
https://bitcoinlib.readthedocs.io/en/latest/

There is consumer app for performing async activities in application. Message middleware used is Rabbit MQ. 


Install using pip
$ pip install -r requirements.txt

in case updated dependency, then perform freeze to update requirments.txt
pip freeze > requirements.txt

Migration

python manage.py makemigrations altcoin
python manage.py migrate

How to create user for app
Create User
python manage.py createsuperuser

Activate Virtual Env
source env/bin/activate

Rabbit MQ Quickstart 
Management Plugin enabled by default at http://localhost:15672

Bash completion has been installed to:
  /usr/local/etc/bash_completion.d

To have launchd start rabbitmq now and restart at login:
  brew services start rabbitmq
Or, if you don't want/need a background service you can just run:
  rabbitmq-server
  
RMQ server -  http://localhost:15672/#/queues

 
Uses fake SMTP server to send emails (only for test env). You can downlaod from http://nilhcem.com/FakeSMTP/download.html
SMTP Server run 
java -jar ~/Downloads/fakeSMTP-2.0.jar
