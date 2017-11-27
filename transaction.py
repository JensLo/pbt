

import numpy as np

class TRANSACTIONTYPE:
    BUY       = 1
    SELL      = 2
    DEPOSIT   = 3
    WITHDRAWL = 4


class Transaction(object):
    """A class that handles the transaction of an asset, as used
    in the Position class.

    Parameters
    ----------
    asset : Asset
        The asset of the transaction
    quantity : int
        Whole number quantity of shares in the transaction
    dt : datetime
        The date/time of the transaction
    price : float
        The transaction price carried out
    order_id : int
        The unique order identifier
    commission : float, optional
        The trading commission
    """

    def __init__(self, asset, price, quantity, timestamp, commission, transactiontype, trans_ID):
        self.asset = asset
        self.price = (price) #Decimal
        self.quantity = (quantity)
        self.timestamp = timestamp
        self.commission = (commission)
        self.trans_ID = trans_ID
        self.type = self._type(transactiontype)

    def _type(self, transactiontype):
        return eval('TRANSACTIONTYPE.%s'%transactiontype.upper())


    def __repr__(self):
        """
        Provides a representation of the Transaction
        to allow full recreation of the object.
        """
        return "%s(asset=%s, quantity=%s, dt=%s, " \
            "price=%s, trans_id=%s, type=%s)" % (
                type(self).__name__, self.asset.name,
                self.quantity, self.timestamp,
                self.price, self.trans_ID, self.type
            )
