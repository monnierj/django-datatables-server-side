# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.core.paginator import Paginator
from django.db.models import ForeignKey
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.views.generic import View
import json


DATATABLES_SERVERSIDE_MAX_COLUMNS = 30


class DatatablesServerSideColumn(object):

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


class DatatablesServerSideView(View):

    searchable_columns = []
    foreign_fields = {}
    model = None

    def __init__(self, *args, **kwargs):
        super(DatatablesServerSideView, self).__init__(*args, **kwargs)
        choice_fields_completion = {}

        choice_fields = [field for field in self.model._meta.fields
                         if not isinstance(field, ForeignKey)]

        for field in choice_fields:
            search_choices = {}
            for cur_choice in field.choices:
                try:
                    search_choices[cur_choice[1]] = cur_choice[0]
                except IndexError:
                    search_choices[cur_choice[0]] = cur_choice[0]
                except UnicodeDecodeError:
                    search_choices[cur_choice[1].decode('utf-8')] = \
                        cur_choice[0]

            if search_choices:
                choice_fields_completion[field.name] = search_choices

        self.choice_fields_completion = choice_fields_completion
        self.foreign_fields = self.foreign_fields

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        try:
            params = self.read_parameters(request.GET)
        except ValueError:
            return HttpResponseBadRequest()

        qs = self.get_initial_queryset()
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

            if query_dict.get(column_base + '[name]') is not None:
                columns.append(DatatablesServerSideColumn(
                    query_dict.get(column_base + '[name]'),
                    query_dict.get(column_base + '[orderable]'),
                    query_dict.get(column_base + '[searchable]')))

            column_index = column_index + 1
        params['columns'] = columns

        return params

    def get_initial_queryset(self):
        return self.model.objects.all()

    def render_column(self, row, column):
        if column in self.foreign_fields:
            fk_value = getattr(row, column)
            return unicode(fk_value) if fk_value else None
        else:
            return getattr(row, column)

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
        print(page_id)

        objects = self.prepare_results(paginator.page(page_id))
        return {"draw": draw_idx,
                "recordsTotal": paginator.count,
                "recordsFiltered": paginator.count,
                "data": objects}

    def customize_row(self, row, obj):
        pass
