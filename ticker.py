# -*- coding: utf-8 -*-

import numpy as np
import time

import pandas as pd
from storage import SafeHDFStore

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

class TickerException(Exception):
    pass

class Ticker(object):

    def __init__(self, exchange, symbol, bartimeframes, tick_storage=None):
        global timeframes
        self.exchange = exchange
        self.exchange.load_markets()
        self.timeframes = []
        self._timeframes = []

        if symbol in self._ex.symbols:
            self.symbol =  symbol
        except:
            raise TickerException(
                'Symbol "%s" not available on exchange "%s".' %(symbol, self.exchange.name)
            )

        for timeframe in bartimeframes:
            self.add_timeframe(timeframe)

        self._lasttimes = [int(time.time()-5) for tf in bartimeframes]
        self._storage = tick_storage


    def add_timeframe(self, timeframe):
        if timeframe in self._ex.timeframes:
            self.timeframes.append(timeframe)
            self._timeframes.append(timeframes[timeframe])
        else:
            raise TickerException(
                'Timeframe "%s" not available on exchange "%s".' %(timeframes[timeframe], self.exchange.name)
            )

    def remove_timeframe(self, timeframe):
        if timeframe in self.timeframes:
            self.timeframes.remove(timeframe)
            self._timeframes.remove(timeframes[timeframe])


    def fetch_bar(self):
        now = time.time()
        i=0
        bars = []
        for _lasttime, _timeframe, timeframe in zip(self._lasttimes, self._timeframes, self.timeframes): 
            if now >= _lasttime + _timeframe:
                bar = exchange.fetch_ohlcv( symbol, timeframe, since=_lasttime*1000, limit=1, )
                events.append( BarEvent(symbol, bar[-1][0]/1000, _timeframe, *(bar[-1][1:])) )
                ticker._lasttimes[i] = int(bar[-1][0]/1000)
                i+=1

                if self._storage is not None:
                    with SafeHDFStore(self._storage, mode='a') as store:
                        key = self.exchange.name+'/'+self.symbol+'/bar/'+ list(timeframes.keys())[list(timeframes.values()).index(event.period)]
                        bar[-1][0] /= 1000
                        columns = ['time', 'open', 'high', 'low', 'close', 'volume']
                        store.add(key, bar, columns)


    def fetch_orderbook(self):
        order_book = self.exchange.fetch_order_book(self.symbol, {'depth':100})
        if self._storage is not None:
            with SafeHDFStore(self._storage, mode='a') as store:
                key = self.exchange.name+'/'+self.symbol+'/order_book'
                asks, bids = np.array(order_book['asks']), np.array(order_book['bids'])
                a_max = asks[:,0][asks[:,0]<=asks[0,0]*1.15][-1]
                b_min = bids[:,0][bids[:,0]<=bids[0,0]*0.85][-1]
                asks, abins = np.histogram(asks[:,0], weights=asks[:,1], 
                                           bins=np.linspace(asks[0,0], a_max, 150), density=False)
                bids, bbins = np.histogram(bids[:,0], weights=bids[:,1], 
                                           bins=np.linspace(b_min, bids[0,0], 150), density=False)
                _key = key+'/asks'
                data = [order_book[symbol]['time']] + asks
                columns = ['time'] + ['idx_'+str(i) for i in range(len(asks))]
                store´.add(_key, data, columns)

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


    def get_bar(self, dt=None):
        pass

    def get_tick(self, dt=None):
        pass

    def get_order_book(self, dt=None):
        if dt is None:
            order_book = self.exchange.fetch_order_book(self.symbol, {'depth':100})
            return np.array(order_book[symbol]['asks']), np.array(order_book[symbol]['bids'])
        else:



class tick_handler(object):

    def __init__(self, interval, bartimeframes, queue=None, tick_storage=None, volumn=0):
        self.interval = interval
        self.bartimeframes = bartimeframes
        self._queue = queue
        self._vol = volumn
        self._storage = tick_storage
        self.tickers = dict()


    def add_symbol(self, exchange, symbol):
        key = exchange.name+':'+symbol
        if (key not in self.tickers):
            new_ticker = Ticker(exchange, symbol, self.bartimeframes)
            self.tickers[key] =Ticker(exchange, symbol, self.bartimeframes)

    def remove_symbol(self, exchange, symbol):
        key = exchange.name+':'+symbol
        try:
            del self.tickers[key]
        except:
            pass

    def add_timeframe(self, timeframe):
        if timeframe not in self.bartimeframes:
            self.bartimeframes.append(timeframe)
            for ticker in self.tickers.values():
                ticker.add_timeframe(timeframe)
            

    def remove_timeframe(self, timeframe):
        if (timeframe in self.bartimeframes):
            self.bartimeframes.remove(timeframe)
            for ticker in self.tickers.values():
                ticker.remove_timeframe(timeframe)


    def update(self):
        events = []
        order_book = {}
        for key, ticker in self.tickers.iter_items():
            now = int(time.time())
            symbol = ticker.symbol
            exchange = ticker.exchange
            order_book[symbol] = exchange.fetch_order_book(symbol, {'depth':100})
            order_book[symbol]['time'] = now

            asks, bids = np.array(order_book[symbol]['asks']), np.array(order_book[symbol]['bids'])

            events.append( TickEvent(symbol, now, *self._get_ask_bid(asks, bids)) )
            i=0
            for _lasttime, _timeframe, timeframe in zip(ticker._lasttimes, ticker._timeframes, ticker.timeframes): 
                if now >= _lasttime + _timeframe:
                    bar = exchange.fetch_ohlcv( symbol, timeframe, since=_lasttime*1000, limit=1, )

                    events.append( BarEvent(symbol, bar[-1][0]/1000, _timeframe, *(bar[-1][1:])) )
                    ticker._lasttimes[i] = int(bar[-1][0]/1000)
                    i+=1

            print(ticker._lasttimes)

        if self._queue is not None:
            [self._queue.put(event) for event in events]
        if self._storage is not None:
            self._store(events, order_book)


    def _store(self, events, order_book):
            global timeframes
            with SafeHDFStore(self._storage, mode='a') as store:
                # Only put inside this block the code which operates on the store
                for event in events:
                    if event.type == EventType.TICK:
                        key = event.ticker+'/tick'
                        data = [event.time, event.ask, event.bid]
                        columns = ['time', 'ask', 'bid']
                        period = self.interval

                    elif event.type == EventType.BAR:
                        key = event.ticker+'/bar/'+ list(timeframes.keys())[list(timeframes.values()).index(event.period)]
                        data = [event.time, event.open_price, event.high_price, 
                                event.low_price, event.close_price, event.volume]
                        columns = ['time', 'open', 'high', 'low', 'close', 'volume']
                        period = list(timeframes.keys())[list(timeframes.values()).index(event.period)]

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






