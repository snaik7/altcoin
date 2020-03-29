"""altcoin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path


from rest_framework.authtoken import views as djnagoviews
from altcoin.user.views import CustomObtainAuthToken

urlpatterns = [
    path('admin/', admin.site.urls),
#    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
#   url(r'^api-token-auth/', djnagoviews.obtain_auth_token),

    path('', include('altcoin.wallet.urls')),
    path('', include('altcoin.address.urls')),
    path('', include('altcoin.unspent.urls')),
    path('', include('altcoin.fee.urls')),
    path('', include('altcoin.send.urls')),
    path('', include('altcoin.user.urls')),
    path('', include('altcoin.txn.urls')),
    path('', include('altcoin.webhook.urls')),
#    path('account/', include('django.contrib.auth.urls')),
]


