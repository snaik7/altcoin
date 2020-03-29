import json
import time
import traceback

import pika
import requests
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.authtoken import views
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from altcoin.errors import ServiceException
from altcoin.errors import ValidationError
from altcoin.settings.base import get_env_var
from altcoin.user.models import Token as UserToken, User
from altcoin.authentication import token_expire_handler
# Create your views here.
from altcoin.utils import service_auth, Util, host



class  CustomObtainAuthToken(views.ObtainAuthToken):
    permission_classes = []
    def post(self, request, *args, **kwargs):

        print('Started ' + self.__class__.__name__ + ' post method %s' %(request.data))
        try:

            serializer = self.serializer_class(data=request.data,
                                               context={'request': request})

            if serializer.is_valid():
                user = serializer.validated_data['user']
                print('Started ' + self.__class__.__name__ + ' post user=' + str(user))
                if not user:
                    raise ServiceException(get_env_var('exception.business.auth.serviceexception'))
                else:
                    token, created = Token.objects.get_or_create(user=user)
                    is_expired, token = token_expire_handler(token)

                return Response({'username': user.username, 'user_id': user.user_id, 'token': token.key})
            else:
                response_dict = {
                    'status': 'error',
                    # the format of error message determined by you base exception class
                    'msg': serializer.errors
                }
                return JsonResponse(response_dict, status=400)

        except Exception as e:
            raise e

class UserView(APIView):
    permission_classes = []

    def post(self, request):
        data = JSONParser().parse(request)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        try:

            if username and password and email:
                user = User.objects.create_user(username=username,
                                                email=email,
                                                password=password)
                if user:
                    user_dict = {}
                    user_dict['username'] = username
                    user = str(user_dict)
                    user = user.replace('\'', '\"')
                    #Util.sendMessage(message=user,listner=WalletListener(Util.get_stomp_connection()),destination= '/queue/wallet')
                    Util.sendMessage(message=user, destination='wallet')


                else:
                    raise ValidationError(get_env_var('exception.business.user.create'))

            else:
                raise ValidationError(get_env_var('exception.validation.user.create'))
            return JsonResponse(data=data, safe=False, status=201)
        except Exception as e:
            track = traceback.format_exc()
            print(track)
            print("error" + str(e))
            raise e

    def reset(request):
        token = request.GET.get('token')
        email = request.GET.get('email')

        service_url = get_env_var(
            'service.url') + '/user/password_reset/validate_token/'
        print('service_url for validate token', service_url)
        raw_data = '{ "token" : "'+token+'" }'
        headers = {'content-type': 'application/json'}
        resp = requests.post(service_url, auth=service_auth, data=raw_data, headers=headers)
        print('received for get address resp', resp.status_code, ' and response %s' % (resp.text))
        resp = json.loads(resp.text)
        context = resp
        context['token'] = token
        context['email'] = email
        print('context', context)


        return render(request, 'change_password.html', context)






