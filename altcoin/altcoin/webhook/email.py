from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse



def email_txn(email,template):
    print('*********************** email send template sratrted ***********************' )
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    context = {
        'username': email.username,
        'email': email.email,
        'txn': email.txn

    }

    # render email text
    email_message = render_to_string(template, context)


    msg = EmailMultiAlternatives(
        # title:
        "Transaction Confirmation for {title}".format(title="Altcoin"),
        # message:
        email_message,
        # from:
        "admin@altcoin.com",
        # to:
        [email.email]
    )
    msg.attach_alternative(email_message, "text/html")
    msg.send()