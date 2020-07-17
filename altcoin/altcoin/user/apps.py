from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'altcoin.user'

    def ready(self):
        import altcoin.user.signals
