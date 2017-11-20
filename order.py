import time
import pandas as pd


class ORDERTYPE:
    BUY_MARKET  = 1
    BUY_LIMIT   = 2
    SELL_MARKET = 3
    SELL_LIMIT  = 4
    STOP_LOSS   = 5
    TAKE_PROFIT = 6
    
class ORDERSTATUS:
    OPEN     = 1
    PARTIAL  = 2
    CANCELED = 3
    CLOSED   = 4

class Order(object):
    """Represents sending an order from a trading algo entity
    to a brokerage to execute.

    A commission can be added here to override the commission
    model, if known. An order_id can be added if required,
    otherwise it will be randomly assigned.

    Parameters
    ----------
    dt : datetime
        The datetime that the order was created.
    asset : Asset
        The asset to transact with the order.
    quantity : int
        The quantity of the asset to transact.
        A negative quantity means a short.
    commission : float, optional
        If commission is known it can be added.
    order_id : str, optional
        The order ID of the order, if known.
    """

    def __init__(asset, order_type, units, price, timestamp, condition=None):
        self.order_type   = order_type
        self.asset        = asset
        self.status       = ORDERSTATUS.OPEN
        self.units        = (units)
        self.price        = (price)
        self.filled       = 0.0
        self.condition    = condition
        self.timestamp    = None
        self.ID           = None
        self.created_timestamp = pd.to_datetime(time.time(), unit='s')


    def update(self, ID, timestamp):
        self.ID = ID
        if timestamp > 1e10:
            unit = 'ms'
        else:
            unit='s'
        self.timestamp = pd.to_datetime(timestamp, unit=unit)

    def transact(self, transaction):
        self.filled += transaction.units
        if self.filled > 0.0:
            if self.filled == self.units:
                self.status = ORDERSTATUS.CLOSED
            else:
                self.status = ORDERSTATUS.PARTIAL

    def cancel(self):
        self.status = ORDERSTATUS.CANCELED



