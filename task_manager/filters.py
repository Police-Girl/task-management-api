"""
filters.py — Task Filtering

Defines all the ways users can filter their task list via URL parameters.

Examples:
  ?status=PENDING
  ?priority=HIGH
  ?due_date_before=2025-12-31
  ?due_date_after=2025-01-01
  ?is_overdue=true
"""

import django_filters
from .models import Task, Status


class TaskFilter(django_filters.FilterSet):
    """All supported filter parameters for the task list endpoint."""

    # ?status=PENDING or ?status=COMPLETED
    status = django_filters.ChoiceFilter(choices=Task.status.field.choices)

    # ?priority=HIGH
    priority = django_filters.ChoiceFilter(choices=Task.priority.field.choices)

    # ?due_date_before=2025-06-01  (tasks due ON or BEFORE this date)
    due_date_before = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='lte'       # lte = less than or equal (≤)
    )

    # ?due_date_after=2025-01-01  (tasks due ON or AFTER this date)
    due_date_after = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='gte'       # gte = greater than or equal (≥)
    )

    # ?is_overdue=true
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'due_date_before', 'due_date_after', 'is_overdue']

    def filter_overdue(self, queryset, name, value):
        """
        Custom filter — can't filter by a @property directly,
        so we translate it into queryset conditions.
        """
        from django.utils import timezone
        now = timezone.now()

        if value is True:
            # Overdue = PENDING tasks past their due date
            return queryset.filter(status=Status.PENDING, due_date__lt=now)
        elif value is False:
            return queryset.exclude(status=Status.PENDING, due_date__lt=now)
        return queryset
