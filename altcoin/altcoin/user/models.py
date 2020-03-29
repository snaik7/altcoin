from django.db import models
from django.contrib.auth.models import AbstractUser, User
from rest_framework.authtoken.models import Token


# Create your models here.

# Create your models here.

class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    username = models.TextField(unique=True)
    password = models.TextField()
    first_name = models.TextField()
    last_name = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)

class Address(models.Model):
    user_id = models.IntegerField(primary_key=True,default=1)
    street_name = models.TextField()
    city = models.TextField()
    state = models.TextField()
    country = models.TextField()
    zip_code = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)


