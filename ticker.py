# -*- coding: utf-8 -*-

import numpy as np
import time

import pandas as pd
from .storage import SafeHDFStore

from qstrader.event import TickEvent, BarEvent, EventType


timeframes = {
                '1s': 1,
                '5s': 5,
                '10s':10,
                '15s':15,
                '30s':30,
                '1m': 1*60,
                '5m': 5*60,
                '15m': 15*60,
                '30m': 30*60,
                '1h': 60*60,
                '2h': 2*60*60,
                '4h': 4*60*60,
                '1d': 1440*60,
                '2d': 2*1440*60,
                '1w': 10080*60,
                '2w': 21600*60,
            }

class Tickers(object):

    def __init__(self, tickers):
        self.tickers = tickers


class Ticker(object):

    def __init__(self, exchange, symbols, interval, bartimeframes, queue, tick_storage, volumn=0):
        global timeframes
        self._ex = exchange
        self._ex.load_markets()
        self._symbols = exchange.symbols
        self.exchange = exchange.name
        self.symbols =  [sym for sym in symbols if sym in self._ex.symbols]
        self.interval = interval 
        self._interval = timeframes[interval]
        self.timeframes = [tf for tf in bartimeframes if tf in self._ex.timeframes]
        self._timeframes = [timeframes[tf] for tf in bartimeframes if tf in self._ex.timeframes]
        self._lasttimes = [int(time.time()) for tf in bartimeframes]
        self._queue = queue
        self._vol = volumn
        self._storage = tick_storage


    def add_symbol(self, symbol):
        if (symbol not in self.symbols) and (symbol in self._ex.symbols):
            self.symbols.append(symbol)

    def remove_symbol(self, symbol):
        try:
            self.symbols.remove(symbol)
        except:
            pass

    def add_timeframe(self, timeframe):
        if (timeframe not in self.timeframes) and (timeframe in self._ex.timeframes):
            self.timeframes.append(timeframes)
            self._ex_timeframes.append(self._ex.timeframes[timeframe])
            self._timeframes.append(timeframes[timeframe])

    def remove_timeframe(self, timeframe):
        try:
            self.timeframes.remove(timeframe)
            self._ex_timeframes.remove(self._ex.timeframes[timeframe])
            self._timeframes.remove(timeframes[timeframe])
        except:
            pass


    def update(self):
        events = []
        order_book = {}
        for symbol in self.symbols:
            now = int(time.time())
            order_book[symbol] = self._ex.fetch_order_book(symbol, {'depth':100})
            order_book[symbol]['time'] = now

            asks, bids = np.array(order_book[symbol]['asks']), np.array(order_book[symbol]['bids'])

            events.append( TickEvent(symbol, now, *self._get_ask_bid(asks, bids)) )

            for _lasttime, _timeframe, timeframe in zip(self._lasttimes, self._timeframes, self.timeframes): 
                if now >= _lasttime + _timeframe:
                    bar = self._ex.fetch_ohlcv( symbol, timeframe, since=_lasttime*1000, limit=1, )
                    events.append( BarEvent(symbol, bar[-1][0]/1000, _timeframe, *(bar[-1][1:])) )
                    _lasttime = bar[-1][0]/1000

        [self._queue.put(event) for event in events]
        self._store(events, order_book)


    def _get_ask_bid(self, asks, bids ):
        try:
            ask = asks[np.cumsum(asks) >= self._vol][0]
        except:
            ask = asks[0]
        try:
            bid = bids[np.cumsum(bids) >= self._vol][0]
        except:
            bid = bids[0]

        return ask[0], bid[0]


    def _store(self, events, order_book):
        global timeframes
        with SafeHDFStore(self._storage) as store:
            # Only put inside this block the code which operates on the store
            for event in events:
                if event.type == EventType.TICK:
                    key = event.ticker+'/tick'
                    data = [event.time, event.ask, event.bid]
                    columns = ['time', 'ask', 'bid']
                    period = self.interval

                elif event.type == EventType.BAR:
                    key = event.ticker+'/bar/'+ timeframes.keys()[list(timeframes.values()).index(event.period)]
                    data = [event.time, event.open_price, event.high_price, 
                            event.low_price, event.close_price, event.volume]
                    columns = ['time', 'open', 'high', 'low', 'close', 'volume']
                    period = timeframes.keys()[list(timeframes.values()).index(event.period)]

                print(period)

                store.add(key, data, columns)
                #store.get_storer(key).attrs.period = period

            for symbol in self.symbols:
                key = symbol+'/order_book'
                asks, bids = np.array(order_book[symbol]['asks']), np.array(order_book[symbol]['bids'])
                a_max = asks[:,0][asks[:,0]<=asks[0,0]*1.15][-1]
                b_min = bids[:,0][bids[:,0]<=bids[0,0]*0.85][-1]
                asks, abins = np.histogram(asks[:,0], weights=asks[:,1], 
                                           bins=np.linspace(asks[0,0], a_max, 150), density=False)
                bids, bbins = np.histogram(bids[:,0], weights=bids[:,1], 
                                           bins=np.linspace(b_min, bids[0,0], 150), density=False)
                
                _key = key+'/asks'
                data = [order_book[symbol]['time']] + asks
                columns = ['time'] + ['idx_'+str(i) for i in range(len(asks))]
                store.add(_key, data, columns)

                _key = key+'/ask_bins'
                data = [order_book[symbol]['time']] + abins[:-1]
                columns = ['time'] + ['idx_'+str(i) for i in range(len(asks))]
                store.add(_key, data, columns)

                _key = key+'/bids'
                data = [order_book[symbol]['time']] + bids
                columns = ['time'] + ['idx_'+str(i) for i in range(len(bids))]
                store.add(_key, data, columns)

                _key = key+'/bid_bins'
                data = [order_book[symbol]['time']] + bbins[1:]
                columns = ['time'] + ['idx_'+str(i) for i in range(len(bids))]
                store.add(_key, data, columns)






