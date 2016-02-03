# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class ColumnOrderError(Exception):
    pass


class Column(object):

    def __init__(self, name, searchable='true', orderable='true',
                 placeholder=False):
        if name is None or searchable is None or\
                orderable is None:
            raise ValueError

        self.name = name
        self.searchable = True if searchable == "true" else False
        self.orderable = True if orderable == "true" else False
        self.placeholder = placeholder or (name == '')

    def __repr__(self):
        return '%s (searchable: %s, orderable: %s)' %\
            (self.name or '<placeholder>', self.searchable, self.orderable)


class Order(object):

    def __init__(self, column, direction, columns_list):
        try:
            self.ascending = True if direction == 'asc' else False
            self.column = columns_list[int(column)]
            if self.column.placeholder:
                raise ColumnOrderError(
                    'Requested to order a placeholder column (index %s)'
                    + column)
        except KeyError:
            raise ColumnOrderError(
                'Requested to order a non-existing column (index %s)'
                + column)

    def __repr__(self):
        return '%s: %s' % (
            self.column.name, 'ASC' if self.ascending else 'DESC')

    def get_order_mode(self):
        if not self.ascending:
            return '-' + self.column.name
        return self.column.name
