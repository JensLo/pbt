# -*- coding: utf-8 -*-

import numpy as np
import os
import time
import sys

from tables.file import File as PyTablesFile
from tables import Col, Int64Col, StringCol, table
from numpy import dtype

def _shape(array):
    return len(array)

class SafeHDFStoreException(Exception):
    pass

class SafeHDFStore(PyTablesFile):
    def __init__(self, filename, mode="r", title="",
                 root_uep="/", filters=None, **kwargs):
        probe_interval = kwargs.pop("probe_interval", 1)
        self._lock = "%s.lock" % filename
        self.mode = mode
        while mode == 'w' or mode == 'a':
            try:
                self._flock = os.open(self._lock, os.O_CREAT |
                                                  os.O_EXCL |
                                                  os.O_WRONLY)
                break
            except FileExistsError:
                time.sleep(probe_interval)

        super(SafeHDFStore, self).__init__(filename, mode, title, 
                                           root_uep, filters, **kwargs)

        #self.__dict__.update(self.getTables())

    def __exit__(self, *args, **kwargs):
        _mode = self.mode
        if self.mode == 'w' or self.mode == 'a':
            _flock = self._flock
            _lock = self._lock
            
        super(SafeHDFStore, self).__exit__(*args, **kwargs)
        if _mode == 'w' or _mode == 'a':
            os.close(_flock)
            os.remove(_lock)


    def __getitem__(self, key):
        if key.count('/')==0:
            if not key.startswith('/'):
                key = '/'+key
        return self._getTable(key)

            
    def __setitem__(self, key, data):
        if self._table_exists(key):
            if not key.startswith('/'):
                key = '/'+key
                _table = self._getTable(key)
                if _shape(data) == _shape(_table.colnames):
                    for col, value in zip(_table.colnames, data):
                        _table.row[col] = value

                    _table.row.append()
                    _table.flush()
                else:
                    raise SafeHDFStoreException(
                        'data shape is (%s) and table shape is (%s)'%(_shape(data), _shape(_table.colnames))
                    )
        else:
            raise SafeHDFStoreException(
                'key needs to point to a table'
            )
            

    def add(self, key, data, columns=None):
        if not self._table_exists(key):
            if columns is None:
                raise SafeHDFStoreException(
                        '"columns" argument is needed to create a new table @%s'%(key)
                    )
                return
            self._createTable(key, columns, data)
        self.__setitem__(key, data)


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
        if not key.startswith('/'):
            key = '/'+key
        self._getGroup(key)
        return self.get_node(key)

    def _table_exists(self, key):
        if not key.startswith('/'):
            key = '/'+key
        group = self._getGroup(key)
        key = key.split('/')[-1]
        return key in group._v_children.keys()


    def _createTable(self, key, columns, data):
        if not key.startswith('/'):
            key = '/'+key
        group = self._getGroup(key)
        key = key.split('/')[-1]
        des = self._getDescription(columns, data)
        return self.create_table(group, key, des)


    def _getDescription(self,columns, data):
        tmp = {}
        for col,value in zip(columns, data):
            
            if isinstance(int(value), (int, float, complex)):
                tmp[col] = Int64Col()

            elif isinstance(value, (str, bytes)):
                tmp[col] = StringCol(itemsize=128)

            else:
                tmp[col] = Col.from_dtype(dtype(np.asarray(value).dtype))

        return tmp


    @property    
    def tables(self):
        _tables=dict()
        for node in self:
            if isinstance(node, table.Table):
                _tables[node._v_pathname] = node
        return _tables

    @property
    def keys(self):
        _keys=[]
        for node in self:
            if isinstance(node, table.Table):
                _keys.append(node._v_pathname)
        return _keys

    def read(self, key, start=None, stop=None, step=None, field=None):
        return self._getTable(key).read(tart, stop, step, field)

    def read_where(key, condition, condvars=None, field=None, start=None, stop=None, step=None):
        return self._getTable(key).read_where(condition, condvars, field, start, stop, step)

    def where(key, condition, condvars=None, start=None, stop=None, step=None):
        return self._getTable(key).where(condition, condvars, start, stop, step)

