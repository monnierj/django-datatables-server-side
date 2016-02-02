# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class Column(object):

    def __init__(self, name, searchable, orderable):
        if name is None or searchable is None or\
                orderable is None:
            raise ValueError

        self.name = name
        self.searchable = True if searchable == "true" else False
        self.orderable = True if orderable == "true" else False

    def __repr__(self):
        return '%s (searchable: %s, orderable: %s)' %\
            (self.name, self.searchable, self.orderable)


class Order(object):

    def __init__(self, column, direction, columns_list):
        self.ascending = True if direction == 'asc' else False
        self.column = columns_list[int(column)]

    def __repr__(self):
        return '%s: %s' % (
            self.column.name, 'ASC' if self.ascending else 'DESC')

    def get_order_mode(self):
        if not self.ascending:
            return '-' + self.column.name
        return self.column.name
