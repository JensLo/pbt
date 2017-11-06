# -*- coding: utf-8 -*-

import numpy as np
import os
import time

from pandas import HDFStore, DataFrame


class SafeHDFStore(HDFStore):
    def __init__(self, *args, **kwargs):
        probe_interval = kwargs.pop("probe_interval", 1)
        self._lock = "%s.lock" % args[0]
        while True:
            try:
                self._flock = os.open(self._lock, os.O_CREAT |
                                                  os.O_EXCL |
                                                  os.O_WRONLY)
                break
            except FileExistsError:
                time.sleep(probe_interval)

        HDFStore.__init__(self, *args, **kwargs)

    def __exit__(self, *args, **kwargs):
        HDFStore.__exit__(self, *args, **kwargs)
        os.close(self._flock)
        os.remove(self._lock)


    def add(self, key, data, columns):
    	df = DataFrame([{col:v for v,col in zip(data,columns)}])
    	if '/'+key in self.keys():
    		self.append(key, df, format='table', data_columns=True)
    	else:
    		self.put(key, df, format='table', data_columns=True)