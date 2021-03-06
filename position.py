
import numpy as np

    
class POSITIONTYPE:
    LONG     = 1
    SHORT    = 2


class PositionException(object):
    pass


class Position(object):
    """A class that keeps track of the position in an asset
    as registered at a particular Broker, in a Portfolio.

    Includes the whole number of shares, the current trade
    price and the position book cost (VWAP per share).

    Parameters
    ----------
    asset : Asset
        The asset of the position
    quantity : int, optional
        Whole number quantity of shares in the position
    book_cost_ps : float, optional
        Volume weighted average price per share of
        the position (the book cost per share)
    current_trade_price : float, optional
        The most recently known trade price of the asset
        on the exchange, as known to the Position
    current_trade_date : datetime, optional
        The most recently known trade date of the asset
        on the exchange, as known to the Position
    """

    def __init__(
        self, asset, quantity=0, book_cost_ps=0.0,
        current_trade_price=0.0, current_trade_date=None
    ):
        """
        Initialise the Position object and calculate the
        position direction (long or short), represented
        by a +1 or -1.
        """
        self.asset = asset
        self.quantity = quantity
        self.type = self._type()
        self.book_cost_ps = book_cost_ps
        self.current_trade_price = current_trade_price
        self.current_trade_date = current_trade_date
        self.book_cost = self.book_cost_ps * self.quantity

    def __repr__(self):
        """
        Provides a representation of the Position object to allow
        full recreation of the object.
        """
        return "%s(asset=%s, quantity=%s, book_cost_ps=%s, " \
            "current_trade_price=%s)" % (
                self.__class__.__name__, self.asset, self.quantity,
                self.book_cost_ps, self.current_trade_price
            )

    def _type(self):
        return POSITIONTYPE.LONG if np.copysign(1, self.quantity) else OSITIONTYPE.SHORT

    def update_book_cost_for_commission(self, asset, commission):
        """
        Handles the adjustment to the position book cost due to
        trading commissions.
        """
        if self.asset != asset:
            raise PositionException(
                'Failed to adjust book cost for Position on asset '
                '%s due to attempt being made to adjust asset %s.' % {
                    self.asset, asset
                }
            )

        # If there's no commission, then there's nothing to do
        if commission is None or commission == 0.0:
            return None

        # If the quantity is zero (position is no longer held)
        # then the book cost is also zero, so does not need adjusting
        if self.quantity == 0:
            return None

        # For simplicity the commission costs are 'shared'
        # across all shares in a position
        position_cost = self.book_cost_ps * self.quantity
        final_cost = position_cost + commission
        self.book_cost_ps = final_cost / self.quantity
        self.book_cost = self.book_cost_ps * self.quantity

    def update(self, transaction):
        """
        Calculates the adjustments to the Position that occur
        once new shares in an asset are bought and sold.
        """
        if self.asset != transaction.asset:
            raise PositionException(
                'Failed to update Position with asset %s when '
                'carrying out transaction of shares in asset %s. ' % (
                    self.asset, transaction.asset
                )
            )

        # Sum the position and transaction quantities then
        # adjust book cost depending upon transaction type
        total_quantity = self.quantity + transaction.quantity
        if total_quantity == 0:
            self.book_cost_ps = 0.0
            self.book_cost = 0.0
        else:
            if self.type == transaction.type:
                # Increasing a long or short position
                position_cost = self.book_cost_ps * self.quantity
                transaction_cost = transaction.quantity * transaction.price
                total_cost = position_cost + transaction_cost
                self.book_cost_ps = total_cost / total_quantity
            else:
                # Closing a position out or covering a short position
                if abs(transaction.quantity) > abs(self.quantity):
                    # Transaction quantity exceeds position quantity
                    # so a long position is closed and short position
                    # is open, or a short position has been covered
                    # and we've now gone long
                    self.book_cost_ps = transaction.price

        # Update the current trade information
        if (
            self.current_trade_date is None or
            transaction.timestamp > self.current_trade_date
        ):
            self.current_trade_price = transaction.price
            self.current_trade_date = transaction.timestamp

        # Update to the new quantity of shares
        self.quantity = total_quantity

        # Handle the commission cost to adjust book cost
        # per share and total book cost
        self.update_book_cost_for_commission(
            self.asset, transaction.commission
        )

        # Adjust the total book cost and position type
        self.book_cost = self.book_cost_ps * self.quantity
        self.type = self._type()

    @property
    def market_value(self):
        """
        Return the market value of the position based on the
        current trade price provided.
        """
        return self.current_trade_price * self.quantity

    @property
    def unr_gain(self):
        """
        Calculate the unrealised absolute gain in currency
        of the position based solely on the market value.
        """
        return self.market_value - self.book_cost

    @property
    def unr_perc_gain(self):
        """
        Calculate the unrealised percentage gain of the
        position based solely on the market value.
        """
        direction = 1 if self.type == POSITIONTYPE.LONG else -1
        if self.book_cost == 0.0:
            return 0.0
        return (direction * self.unr_gain / self.book_cost) * 100.0
