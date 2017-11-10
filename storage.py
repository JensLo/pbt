# -*- coding: utf-8 -*-

import numpy as np
import os
import time
import sys

from tables.file import File as PyTablesFile
from tables import Col
from numpy import dtype


class SafeHDFStore(PyTablesFile):
    def __init__(self, filename, mode="r", title="",
                 root_uep="/", filters=None, **kwargs):
        probe_interval = kwargs.pop("probe_interval", 1)
        self._lock = "%s.lock" % filename
        while True:
            try:
                self._flock = os.open(self._lock, os.O_CREAT |
                                                  os.O_EXCL |
                                                  os.O_WRONLY)
                break
            except FileExistsError:
                time.sleep(probe_interval)

        super(SafeHDFStore, self).__init__(filename, mode, title, 
                                           root_uep, filters, **kwargs)

    def __exit__(self, *args, **kwargs):
        _flock = self._flock
        _lock = self._lock
        super(SafeHDFStore, self).__exit__(*args, **kwargs)
        os.close(_flock)
        os.remove(_lock)


    def add(self,key, data, columns):
        print('Start Storing:', key)
        if not key.startswith('/'):
            key = '/'+key
        sys.stdout.flush()
        if not self._table_exists(key):
            table = self._createTable(key, columns, data)
        else:
            table = self._getTable(key)

        for col, value in zip(columns, data):
            if col not in ('time', 'date', 't'):
                table.row[col] = int(value*1e8)
            else:
                table.row[col] = int(value)

        table.row.append()
        table.flush()
        print('Finished Storing:', key)
        sys.stdout.flush()
        print()


    def _getGroup(self, key):
        paths = key.split('/')
        path='/'
        for p in paths[:-1]:
            if not len(p):
                continue
            new_path = path
            if not path.endswith('/'):
                new_path += '/'
            new_path += p
            try:
                group = self.get_node(new_path)
            except:
                group = self.create_group(path, p)
            path = new_path
        return group

    def _getTable(self, key):
        group = self._getGroup(key)
        return self.get_node(key)

    def _table_exists(self, key):
        group = self._getGroup(key)
        key = key.split('/')[-1]
        return key in group._v_children.keys()


    def _createTable(self, key, columns, data):
        group = self._getGroup(key)
        key = key.split('/')[-1]
        des = self._getDescription(columns, data)
        return self.create_table(group, key, des)


    def _getDescription(self,columns, data):
        tmp = {}
        for col,value in zip(columns, data):
            
            if not isinstance(value, (int, float, complex)):
                value = '*'*64

            elif np.asarray(value).dtype != object:
                if isinstance(value, (int, float, complex)):
                    tmp[col] = Col.from_dtype(dtype(dtype('int64')))
                else:
                    tmp[col] = Col.from_dtype(dtype(np.asarray(value).dtype))

        return tmp


