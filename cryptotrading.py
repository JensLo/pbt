# -*- coding: utf-8 -*-

import numpy as np


import ccxt
import configparser
from decimal import Decimal, getcontext, ROUND_HALF_DOWN

try:
    import requests
    requests.get("http://google.com")
except:
    import os
    import px
    px.run()
    os.environ['http_proxy'] = "http://127.0.0.1:3129" 
    os.environ['https_proxy'] = "https://127.0.0.1:3129" 

from __future__ import print_function
from enum import Enum

getcontext().prec = 8

ORDERSTATUS = Enum("Orderstatus", "OPEN PARTIAL CANCELED CLOSED")
ORDERTYPE = Enum("Ordertype", "BUY SELL")

POSITIONSTATUS = Enum("Psitionstatus", "OPEN CLOSED")
POSITIONTYPE = Enum("PositionType", "LONG SHORT")







class Position(object):
    def __init__(self, exchange, home_currency, position_type, 
                 currency_pair, ticker):
        self.exchange = exchange            # kraken, bittrex, poloniex, ...
        self.home_currency = home_currency  # Account denomination (e.g. EUR)
        self.position_type = position_type  # Long or short
        self.currency_pair = currency_pair  # Intended traded currency pair
        
        self.setup_currencies()
        self.update_position_price()
        

    def setup_currencies(self):
        if self.exchange.markets is None:
            self.exchange.load_markets()

        base_currency, quote_currency = self.currency_pair.split('/')
        
        if base_currencynot in self.exchange.currcies:
            raise ValueError("'base currency' cannot be found on exchange %s"%exchange.name)
        if quote_currency in self.exchange.currcies:
            raise ValueError("'quote currency' cannot be found on exchange %s"%exchange.name)
        if self.home_currency in self.exchange.currcies:
            raise ValueError("'home currency' cannot be found on exchange %s"%exchange.name)

        self.base_currency = base_currency    # For ETH/BTC, this is ETH
        self.quote_currency = quote_currency   # For ETH/BTC, this is BTC
        # For ETH/BTC, with account denominated in EUR, this is ETH/EUR and BTC/EUR
        self.base_home_currency_pair = "%s%s" % (self.base_currency, self.home_currency)
        self.quote_home_currency_pair = "%s%s" % (self.quote_currency, self.home_currency)
        
        self.base_home_avalable = self.base_home_avalable in self.exchange.markets.keys()
        self.self.avg_price = dict(base = Decimal(0), home = Decimal(0))
        self.units = Decimal(0)


    def _get_price(self, ticker):
        if self.position_type == POSITIONTYPE.LONG:
            return Decimal(ticker_cur['highestBid'])    
        else: # POSITIONTYPE.SHORT
            return Decimal(ticker_cur['lowestAsk']) 
            
    def get_current_price_base(self):
        ticker_cur = self.exchange.fetch_ticker(self.currency_pair)['info']
        return self._get_price(ticker_cur)
            
    def get_current_price_home(self):
        if self.base_home_avalable:
            ticker_cur = self.exchange.fetch_ticker(self.base_home_currency_pair)['info']
            cur_home_price = self._get_price(ticker_cur)

        else: #calculate base/home via base/quote * quote/home
            ticker_quote = self.exchange.fetch_ticker(self.quote_home_currency_pair)['info']
            cur_price = self.get_current_price_base()
            cur_home_price = cur_price * self._get_price(ticker_quote)

        return cur_home_price

    def calculate_change(self):
        if self.position_type == POSITIONTYPE.LONG:
            mult = Decimal(1)
        else:
            mult = Decimal(-1)
        change_base = (mult * (self.get_current_price_base() - self.avg_price['base']))
        change_home = (mult * (self.get_current_price_home() - self.avg_price['home']))
        return dict(base=change_base, home=change_home)


    def calculate_profit(self):
        return dict((key,value * self.units) 
                    for key, value in self.calculate_change().items())

    def calculate_profit_perc_base(self):
        if self.units > 0:
            return dict((key,value * self.avg_price[key])
                         for key, value in self.calculate_change().items())
        else:
            return Decimal(0)


    def update_position_price(self):
        self.cur_price = self.get_current_price_base()
        self.profit_base = self.calculate_profit_base()
        self.profit_home = self.calculate_profit_home()
        self.profit_perc_base = self.calculate_profit_perc_base()
        self.profit_perc_home = self.calculate_profit_perc_home()

    def add_units(self, units):
        units = Decimal(units)
        new_total_units = self.units + units
        new_total_cost_base = self.avg_price['base']*self.units + self.get_current_price_base()*units
        new_total_cost_home = self.avg_price['home']*self.units + self.get_current_price_home()*units
        self.avg_price['base'] = new_total_cost_base/new_total_units
        self.avg_price['home'] = new_total_cost_home/new_total_units
        self.units = new_total_units
        self.update_position_price()

    def remove_units(self, units):
        remove_price_base = self.get_current_price_base()
        remove_price_home = self.get_current_price_home()
        units = Decimal(units)
        self.units -= units
        self.update_position_price()
        # Calculate PnL
        return dict((key,value * units) for self.calculate_change().items())
        

    def close_position(self):
        return self.remove_units(self.units)



class order:
    def __init__(self, exchange, ):
        self.exchange     = exchange
        self.order_type   = order_type
        self.base         = base
        self.currency     = currency
        self.status       = 'open' # 'partial, filled, canceled'
        self.value        = value
        self.price        = price
        self.filled       = 0.0
        self.
    
    
    def while_open(self):
        while(1):
            if self.check_status() == ORDERSTATUS.PARTIAL:
                position
            time.sleep(10)
            
    def check_status(self):
        self.status = 
    

    def excecute(self):
        
        
        
    
class position:
    def __init__(self, order ):
        

    
    
    

def getValueIn(exchange, currency, fiat, value):
    return exchange.fetch_ticker('%s/%s'%(currency, fiat))['bid']*value

def buy(exchange, pair, value, order_type='limit'):
    #returns order
    pass


def sell(exchange, pair, value, order_type='limit'):


def close(position):