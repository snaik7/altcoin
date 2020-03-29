from django.db import models

# Create your models here.
from altcoin.settings.local import db_uri
from bitcoinlib.db import DbInit, DbTransaction


class Txn(models.Model):


    txn_id = models.TextField(primary_key=True)
    wallet_id = models.TextField()
    type = models.TextField()
    status = models.TextField(default='processing')
    source = models.TextField(default='')
    source_amount = models.TextField(default='')
    source_currency = models.TextField(default='')
    destination = models.TextField()
    destination_amount = models.TextField()
    destination_currency = models.TextField(default='BTC')
    message = models.TextField()
    includes_fee = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)



    def txn_list_wallet(db_uri=None, wallet_id=None):
        """
        List txn from database

        :param db_uri: URI of the database
        :type db_uri: str

        :return dict: Dictionary of txn defined in database
        """

        session = DbInit(db_uri=db_uri).session
        txn = session.query(DbTransaction).filter_by(wallet_id=wallet_id).order_by(DbTransaction.id).all()
        txnlst = []
        for t in txn:
            txnlst.append({
                'id': t.id,
                'hash': t.hash,
                'network': t.network_name,
                'fee': t.fee,
                'confirmations': t.confirmations,
                'date': t.date,
            })
        session.close()
        return txnlst