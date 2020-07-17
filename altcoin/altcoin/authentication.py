import logging

from django.contrib.auth.backends import BaseBackend
import traceback


from datetime import datetime, timedelta, timezone

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.parsers import JSONParser

from altcoin.errors import ServiceException, AuthenticationError
from altcoin.settings.base import get_env_var
from altcoin.user.models import User

import logging
from altcoin.settings import base

from rest_framework.authtoken.models import Token

from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from altcoin.basicauth import decode

logger = logging.getLogger(__name__)


def create(self, username):
    user = User(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.save()


# this return left time
def expires_in(token):
    time_elapsed = timezone.now() - token.created
    left_time = timedelta(seconds=base.TOKEN_EXPIRED_AFTER_SECONDS) - time_elapsed
    return left_time


# token checker if token expired or not
def is_token_expired(token):
    return expires_in(token) < timedelta(seconds=0)


# if token is expired new token will be established
# If token is expired then it will be removed
# and new one with different key will be created
def token_expire_handler(token):
    is_expired = is_token_expired(token)
    if is_expired:
        token.delete()
        token = Token.objects.create(user=token.user)
    return is_expired, token


#    def process_request(self, request):
#https://medium.com/@yerkebulan199/django-rest-framework-drf-token-authentication-with-expires-in-a05c1d2b7e05
class ExpiringTokenAuthentication(TokenAuthentication):

    def authenticate(self, request):
        try:

            print('Started ' + self.__class__.__name__ + ' authenticate method')
            key = request.headers.get('Authorization')
            print('Started ', self.__class__.__name__, '  key=%s' % (key))

            if key == None:
                return None

            auth_key = key.split(' ')
            auth = None

            if len(auth_key) > 1:
                auth = auth_key[0]
                key = auth_key[1]
            else:
                return None

            user = None

            if auth == 'Basic':
                print('Basic Auth ')
                username_password = decode(key)
                username = username_password[0]
                password = username_password[1]
                print('Authentication=',auth , 'key=', key, 'username=', username )
                user = User.objects.filter(username=username)
                if user.count() > 0:
                    user = user[0]
                    print('Authentication', auth, 'key', key, 'username', username, 'user_id', user.user_id)
                    if  user.check_password(password):
                        print('user exist from user' + str(user.user_id))
                        token = Token.objects.filter(user_id=user.user_id)
                        if token.count() > 0:
                            token = token[0]
                            print('token  key ' + token.key)
                            if not is_token_expired(token):  # The implementation will be described further
                                print('Basic Auth Authentication Success')
                                return (token.user, token.key)
                            else:
                                print('Basic Auth Authentication with token key failure with token expired')
                                #is_expired, token = token_expire_handler(token)
                                #return (token.user, token.key)
                                raise AuthenticationError(get_env_var('exception.business.auth.expire.serviceexception'))
                        else:
                            print('Basic Auth Authentication with no  auth token')
                            token = Token.objects.create(user=user)
                            return (token.user, token.key)

                    else:
                        print('Not authenticated User with password for ' + user.username)
                        raise AuthenticationError(get_env_var('exception.business.auth.serviceexception'))
                else:
                    print('No user eist with count zero')
                    raise AuthenticationError(get_env_var('exception.business.auth.expire.serviceexception'))


            else:
                print('Authentication', auth, 'key', key)
                token = Token.objects.filter(key = key)
                if token.count() > 0:
                    print('Token  Authentication')
                    token = token[0]
                    # token_expire_handler will check, if the token is expired it will generate new one
                    if not is_token_expired(token):  # The implementation will be described further
                        print('Token Auth Authentication Success')
                        return (token.user, token)
                    else:
                        print('Token Auth Authentication failure with token expired')
                        return None
                        raise AuthenticationError(get_env_var('exception.business.auth.expire.serviceexception'))
                else:
                    print('Token Authentication with no  auth token')
                    raise AuthenticationError(get_env_var('exception.business.auth.expire.serviceexception'))


        except User.DoesNotExist or Token.DoesNotExist or Exception as e:
            track = traceback.format_exc()
            print('-------track start--------')
            print(track)
            print('-------track end--------')
            return None
            raise e

        print('Authentication Success')
        return user

    @staticmethod
    def get_user(request):
        print('getuser progress ')
        exp_token  = ExpiringTokenAuthentication()
        result = exp_token.authenticate(request)
        if result:
            print('user received' , str(result [0]))
            return str(result[0])
        else:
            None

