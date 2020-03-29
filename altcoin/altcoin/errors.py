#from  altcoin.errors import ValidationError, AuthenticationError, ObjectNotFound, ResourceNotExist
import traceback
import logging
import altcoin.settings.base
from django.http import HttpResponse, JsonResponse
import traceback


# define Python user-defined exceptions
from altcoin.settings import base


class ValidationError(Exception):
	"""Raised when the input value is invalid"""
	pass

class AuthenticationError(Exception):
	"""Raised when the authentication failed"""
	pass

class ObjectNotFound(Exception):
	"""Raised when the object not found"""
	pass

class ResourceNotExist(Exception):
	"""Raised when the resource not found"""
	pass

class ServiceException(Exception):
	"""Raised when the service exception"""
	pass

# categorize your exceptions
ERRORS_400 = (ValidationError, )
ERRORS_401 = (AuthenticationError, )
ERRORS_404 = (ObjectNotFound, ResourceNotExist, )

class ExceptionHandleMiddleware(object):
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		return self.get_response(request)

	def process_exception(self, request, e):
		# set status_code by category of the exception you caught
		if isinstance(e, ERRORS_400):
			print('enter validation')
			status_code = 400
		elif isinstance(e, ERRORS_401):
			status_code = 401
		elif isinstance(e, ERRORS_404):
			status_code = 404
		else:
			# if the exception not belone to any one you expected,
			# or you just want the response to be 500
			status_code = 500
			# you can do something like write an error log or send report mail here
			logging.error(e)
			
		response_dict = {
			'status': 'error',
			# the format of error message determined by you base exception class
			'msg': str(e)
		}

		if base.DEBUG :
			# you can even get the traceback infomation when you are in debug mode
			#response_dict['traceback'] = traceback.format_exc()
			track = traceback.format_exc()
			print('-------track start--------')
			print(track)
			print('-------track end--------')

		return JsonResponse(response_dict,status=status_code)
