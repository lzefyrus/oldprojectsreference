# encode: utf-8

import django_filters

import domain.models as domain_models


class ExamFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(name="name", lookup_expr='icontains')

    class Meta:
        model = domain_models.Exam
        fields = ('name',)


class LaboratoryFilter(django_filters.FilterSet):

    brand__name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = domain_models.Laboratory
        fields = ('brand__name', 'description', 'street',)
