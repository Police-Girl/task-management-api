import django_filters
from .models import Task, Priority, Status


class TaskFilter(django_filters.FilterSet):
    # Filter by exact status: ?status=PENDING or ?status=COMPLETED
    status = django_filters.ChoiceFilter(choices=Status.choices)

    # Filter by exact priority: ?priority=HIGH
    priority = django_filters.ChoiceFilter(choices=Priority.choices)

    # Date range filters — useful for "show me what's due this week"
    due_date_before = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')
    due_date_after = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')

    # Custom filter since is_overdue is a model property, not a real DB column
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'due_date_before', 'due_date_after', 'is_overdue']

    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone
        now = timezone.now()

        if value is True:
            # Overdue means still pending AND past the due date
            return queryset.filter(status=Status.PENDING, due_date__lt=now)
        elif value is False:
            return queryset.exclude(status=Status.PENDING, due_date__lt=now)
        return queryset

