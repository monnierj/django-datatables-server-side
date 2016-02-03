# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.core.paginator import Paginator
from django.db.models import ForeignKey, Q
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.views.generic import View
from django.utils import six
from django_datatables_server_side.parameters import (
    Column, Order, ColumnOrderError)
import json


DATATABLES_SERVERSIDE_MAX_COLUMNS = 30


class DatatablesServerSideView(View):
    columns = []
    searchable_columns = []
    foreign_fields = {}
    model = None

    def __init__(self, *args, **kwargs):
        super(DatatablesServerSideView, self).__init__(*args, **kwargs)
        choice_fields_completion = {}
        choice_fields_values = {}

        choice_fields = [field for field in self.model._meta.fields
                         if not isinstance(field, ForeignKey)]

        for field in choice_fields:
            search_choices = {}
            render_choices = {}

            for cur_choice in field.choices:
                try:
                    search_choices[cur_choice[1]] = cur_choice[0]
                except IndexError:
                    search_choices[cur_choice[0]] = cur_choice[0]
                except UnicodeDecodeError:
                    search_choices[cur_choice[1].decode('utf-8')] = \
                        cur_choice[0]

                try:
                    render_choices[cur_choice[0]] = cur_choice[1]
                except UnicodeDecodeError:
                    render_choices[cur_choice[0]] = cur_choice[1].decode(
                        'utf-8')
                except IndexError:
                    render_choices[cur_choice[0]] = cur_choice[0]

            if search_choices:
                choice_fields_completion[field.name] = search_choices

            if render_choices:
                choice_fields_values[field.name] = render_choices

        self.choice_fields_values = choice_fields_values
        self.choice_fields_completion = choice_fields_completion
        self.foreign_fields = self.foreign_fields

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        try:
            params = self.read_parameters(request.GET)
        except ValueError:
            return HttpResponseBadRequest()

        # Prepare the queryset and apply the search and order filters
        qs = self.get_initial_queryset()

        if 'search_value' in params:
            qs = self.filter_queryset(params['search_value'], qs)

        if len(params['orders']):
            qs = qs.order_by(
                *[order.get_order_mode() for order in params['orders']])

        paginator = Paginator(qs, params['length'])

        return HttpResponse(
            json.dumps(
                self.get_response_dict(paginator, params['draw'],
                                       params['start'])
            ),
            content_type="application/json")

    def read_parameters(self, query_dict):
        """ Converts and cleans up the GET parameters. """
        params = {field: int(query_dict[field]) for field
                  in ['draw', 'start', 'length']}

        column_index = 0
        has_finished = False
        columns = []

        while column_index < DATATABLES_SERVERSIDE_MAX_COLUMNS and\
                not has_finished:
            column_base = 'columns[%d]' % column_index

            try:
                column_name = query_dict[column_base + '[name]']
                if column_name != '':
                    columns.append(Column(
                        column_name,
                        query_dict.get(column_base + '[orderable]'),
                        query_dict.get(column_base + '[searchable]')))
                else:
                    columns.append(Column('', placeholder=True))
            except KeyError:
                has_finished = True

            column_index += 1

        orders = []
        order_index = 0
        has_finished = False
        while order_index < len(self.columns) and not has_finished:
            try:
                order_base = 'order[%d]' % order_index
                order_column = query_dict[order_base + '[column]']
                orders.append(Order(
                    order_column,
                    query_dict[order_base + '[dir]'],
                    columns))
            except ColumnOrderError:
                pass
            except KeyError:
                has_finished = True
            
            order_index += 1

        search_value = query_dict.get('search[value]')
        if search_value:
            params['search_value'] = search_value

        params.update({'columns': columns, 'orders': orders})
        return params

    def get_initial_queryset(self):
        return self.model.objects.all()

    def render_column(self, row, column):
        val = getattr(row, column)

        if column in self.foreign_fields:
            fk_value = val
            return unicode(fk_value) if fk_value else None
        elif column in self.choice_fields_completion:
            return self.choice_fields_values[column][val]
        else:
            return val

    def prepare_results(self, qs):
        json_data = []

        for cur_object in qs:
            retdict = {fieldname: self.render_column(cur_object, fieldname)
                       for fieldname in self.columns}
            self.customize_row(retdict, cur_object)
            json_data.append(retdict)
        return json_data

    def get_response_dict(self, paginator, draw_idx, start_pos):
        page_id = (start_pos // paginator.per_page) + 1
        if page_id > paginator.num_pages:
            page_id = paginator.num_pages
        elif page_id < 1:
            page_id = 1

        objects = self.prepare_results(paginator.page(page_id))
        return {"draw": draw_idx,
                "recordsTotal": paginator.count,
                "recordsFiltered": paginator.count,
                "data": objects}

    def customize_row(self, row, obj):
        pass

    def choice_field_search(self, column, search_value):
        values_dict = self.choice_fields_completion[column]
        matching_choices = [val for key, val in six.iteritems(values_dict)
                            if key.startswith(search_value)]
        return Q(**{column + '__in': matching_choices})

    def filter_queryset(self, search_value, qs):
        search_filters = Q()
        for col in self.searchable_columns:
            if col in self.foreign_fields:
                query_param_name = self.foreign_fields[col]
            elif col in self.choice_fields_completion:
                search_filters |= self.choice_field_search(
                    col, search_value)
                continue
            else:
                query_param_name = col
            search_filters |=\
                Q(**{query_param_name+'__istartswith': search_value})

        return qs.filter(search_filters)
