
import datetime
from collections import namedtuple
import locale
import math
import sys

import pandas as pd

from .position_handler import PositionHandler
from .utils.console import (
    string_colour, GREEN, RED, CYAN, WHITE
)
from .transaction import TRANSACTIONTYPE

PortfolioEvent = namedtuple(
    'PortfolioEvent', 'date, type, description, debit, credit, balance'
)


class PortfolioException(Exception):
    pass


class Portfolio(object):
    """A class representing a portfolio. It contains a cash
    account with the ability to subscribe and withdraw funds.
    It also contains a list of positions in assets, encapsulated
    by a PositionHandler instance.

    Parameters
    ----------
    start_dt : datetime
        Portfolio creation datetime.
    starting_cash : float, optional
        Starting cash of the portfolio. Defaults to 100,000 USD.
    currency: str, optional
        The portfolio denomination currency.
    portfolio_id: str, optional
        An identifier for the portfolio.
    name: str, optional
        The human-readable name of the portfolio.
    """

    def __init__(
        self, start_dt, starting_cash=0.0, portfolio_id=None,
        name=None
    ):
        """
        Initialise the Portfolio object with a PositionHandler,
        an event history, along with cash balance. Make sure
        the portfolio denomination currency is also set.
        """
        self.pos_handler = PositionHandler()
        self.history = []
        self.start_dt = start_dt
        self.cur_dt = start_dt
        self.starting_cash = starting_cash
        self.portfolio_id = portfolio_id
        self.name = name
        self.total_cash = starting_cash

    def deposit(self, transaction):
        """
        Credit funds to the portfolio.
        """
        if transaction.dt < self.cur_dt:
            raise PortfolioException(
                'Subscription datetime (%s) is earlier than '
                'current portfolio datetime (%s). Cannot '
                'subscribe funds.' % (dt, self.cur_dt)
            )
        if transaction.quantity < 0:
            raise PortfolioException(
                'Cannot credit negative amount: '
                '%s to the portfolio.' %
                self._currency_format(amount)
            )
        self.transact_asset(transaction)


    def withdraw(self, transaction):
        """
        Withdraw funds from the portfolio if there is enough
        cash to allow it.
        """
        # Check that amount is positive and that there is
        # enough in the portfolio to withdraw the funds
        if transaction.dt < self.cur_dt:
            raise PortfolioException(
                'Withdrawal datetime (%s) is earlier than '
                'current portfolio datetime (%s). Cannot '
                'withdraw funds.' % (dt, self.cur_dt)
            )
        if transaction.quantity < 0:
            raise PortfolioException(
                'Cannot debit negative amount: '
                '%0.2f from the portfolio.' % amount
            )
        self.transact_asset(transaction)

    def transact_asset(self, transaction):
        """
        Adjusts positions to account for a transaction.
        """
        tn = transaction
        if tn.timestamp < self.cur_dt:
            raise PortfolioException(
                'Transaction datetime (%s) is earlier than '
                'current portfolio datetime (%s). Cannot '
                'transact assets.' % (tn.timestamp, self.cur_dt)
            )
        self.pos_handler.transact_position(tn)
        direction = 1 if tn.type in (TRANSACTIONTYPE.BUY or TRANSACTIONTYPE.WITHDRAW) else -1
        tn_share_cost = direction * tn.price * tn.quantity
        tn_total_cost = tn_share_cost + tn.commission

        
        self.total_cash -= tn_total_cost

        if tn.type in (TRANSACTIONTYPE.DEPOSIT, TRANSACTIONTYPE.WITHDRAW):
            # Form Portfolio history details
            direction = "DEPOSIT" if tn.type == RANSACTIONTYPE.DEPOSIT else "WIDTHDRAW"
            description = "%s %s %s %0.2f %s" % (
                direction, tn.quantity, tn.asset.name.upper(),
                tn.price, datetime.datetime.strftime(tn.timestamp, "%d/%m/%Y")
            )
            pe = PortfolioEvent(
                date=dt, type=direction,
                description=description,
                debit=round(amount, 2), credit=0.0,
                balance=round(self.total_cash, 2)
        )
        else:
            # Form Portfolio history details
            direction = "LONG" if tn.type > 0 else "SHORT"
            description = "%s %s %s %0.2f %s" % (
                direction, tn.quantity, tn.asset.name.upper(),
                tn.price, datetime.datetime.strftime(tn.timestamp, "%d/%m/%Y")
            )
            pe = PortfolioEvent(
                date=tn.timestamp, type='asset_transaction',
                description=description,
                debit=round(tn_total_cost, 2), credit=0.0,
                balance=round(self.total_cash, 2)
            )
        self.history.append(pe)
        self.cur_dt = transaction.timestamp


    def update_market_value_of_asset(
        self, asset, current_trade_price, current_trade_date
    ):
        """
        Update the market value of the asset to the current
        trade price and date.
        """
        if asset not in self.pos_handler.positions:
            return
        else:
            if current_trade_price < 0.0:
                raise PortfolioException(
                    'Current trade price of %s is negative for '
                    'asset %s. Cannot update position.' % (
                        current_trade_price, asset
                    )
                )
            if current_trade_date < self.cur_dt:
                raise PortfolioException(
                    'Current trade date of %s is earlier than '
                    'current date %s of asset %s. Cannot update '
                    'position.' % (
                        current_trade_date, self.cur_dt, asset
                    )
                )
            self.pos_handler.update_position(
                asset,
                current_trade_price=current_trade_price,
                current_trade_date=current_trade_date
            )

    @property
    def total_value(self):
        return self.total_cash + self.pos_handler.total_market_value
        

    def history_to_df(self):
        """
        Creates a Pandas DataFrame of the Portfolio history.
        """
        df = pd.DataFrame.from_records(
            self.history, columns=[
                "date", "type", "description",
                "debit", "credit", "balance"
            ]
        )
        df.set_index(keys=["date"], inplace=True)
        return df

    def holdings_to_dict(self):
        """
        Output the portfolio holdings information as a dictionary
        with Assets as keys and sub-dictionaries as values.
        """
        holdings = {}
        for asset, pos in self.pos_handler.positions.items():
            holdings[asset] = {
                "quantity": pos.quantity,
                "book_cost": pos.book_cost,
                "market_value": pos.market_value,
                "gain": pos.unr_gain,
                "perc_gain": pos.unr_perc_gain
            }
        return holdings

    def portfolio_to_dict(self):
        """
        Output the portfolio holdings information as a dictionary
        with Assets as keys and sub-dictionaries as values, with
        the inclusion of total cash and total value.
        """
        port_dict = self.holdings_to_dict()
        port_dict["total_cash"] = self.total_cash
        port_dict["total_value"] = self.total_value
        return port_dict

    def holdings_to_console(self):
        """
        Output the portfolio holdings information to the console.
        """
        def print_row_divider(repeats, symbol="=", cap="*"):
            """
            Prints a row divider for the table.
            """
            sys.stdout.write(
                "%s%s%s\n" % (cap, symbol * repeats, cap)
            )

        # Sort the assets based on their name, not ticker symbol
        pos_sorted = sorted(
            self.pos_handler.positions.items(),
            key=lambda x: x[0].name
        )

        # Output the name and ID of the portfolio
        sys.stdout.write(
            string_colour(
                "\nPortfolio Holdings | %s - %s\n\n" % (
                    self.portfolio_id, self.name
                ), colour=CYAN
            )
        )

        # Create the header row and dividers
        repeats = 98
        print_row_divider(repeats)
        sys.stdout.write(
            "| Holding | Quantity | Price | Change |"
            "      Book Cost |   Market Value |       "
            "     Gain          | \n"
        )
        print_row_divider(repeats)

        # Create the asset holdings rows for each ticker
        ticker_format = '| {0:>7} | {1:>8d} | {2:>5} | ' \
            '{3:>6} | {4:>14} | {5:>14} |'
        for asset, pos in pos_sorted:
            sys.stdout.write(
                ticker_format.format(
                    asset.symbol, int(pos.quantity), "-", "-",
                    self._currency_format(pos.book_cost),
                    self._currency_format(pos.market_value)
                    
                )
            )
            # Colour the gain as red, green or white depending upon
            # whether it is negative, positive or breakeven
            colour = WHITE
            if pos.unr_gain > 0.0:
                colour = GREEN
            elif pos.unr_gain < 0.0:
                colour = RED
            gain_str = string_colour(
                self._currency_format(
                    pos.unr_gain
                ), colour=colour
            )
            perc_gain_str = string_colour(
                "%0.2f%%" % pos.unr_perc_gain,
                colour=colour
            )
            sys.stdout.write(" " * (25 - len(gain_str)))
            sys.stdout.write(gain_str)
            sys.stdout.write(" " * (22 - len(perc_gain_str)))
            sys.stdout.write(str(perc_gain_str))
            sys.stdout.write(" |\n")

        # Create the totals row
        print_row_divider(repeats)
        total_format = '| {0:>7} | {1:25} | {2:>14} | {3:>14} |'
        sys.stdout.write(
            total_format.format(
                "Total", " ",
                self._currency_format(self.pos_handler.total_book_cost()),
                self._currency_format(self.pos_handler.total_market_value())
            )
        )
        # Utilise the correct colour for the totals
        # of gain and percentage gain
        colour = WHITE
        total_gain = self.pos_handler.total_unr_gain()
        perc_total_gain = self.pos_handler.total_unr_perc_gain()
        if total_gain > 0.0:
            colour = GREEN
        elif total_gain < 0.0:
            colour = RED
        gain_str = string_colour(
            self._currency_format(total_gain),
            colour=colour
        )
        perc_gain_str = string_colour(
            "%0.2f%%" % perc_total_gain,
            colour=colour
        )
        sys.stdout.write(" " * (25 - len(gain_str)))
        sys.stdout.write(gain_str)
        sys.stdout.write(" " * (22 - len(perc_gain_str)))
        sys.stdout.write(str(perc_gain_str))
        sys.stdout.write(" |\n")
        print_row_divider(repeats)
        sys.stdout.write("\n")
