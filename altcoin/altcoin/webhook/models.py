from django.db import models

# Create your models here.

class Email(models.Model):

    username = models.TextField()
    email = models.TextField()
    txn = models.TextField()
