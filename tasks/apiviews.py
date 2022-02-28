from django.http import JsonResponse
from django.views import View
from django.http.response import HttpResponse

from tasks.models import Task, TaskHistory
from tasks.models import STATUS_CHOICES

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins

from django.contrib.auth.models import User

from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    ChoiceFilter,
    BooleanFilter,
    DateFilter,
)

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["username",]


class TaskSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model=Task
        fields=['id', 'title','description','user', 'completed', 'status']

class TaskFilter(FilterSet):
    completed = BooleanFilter()

class TaskViewSet(ModelViewSet):
    queryset= Task.objects.all()
    serializer_class= TaskSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter

    def get_queryset(self):
        return Task.objects.filter(user= self.request.user, deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskHistorySerializer(ModelSerializer):
    # task = TaskSerializer()

    class Meta:
        model = TaskHistory
        fields = ["old_status", "new_status", "change_date" ]

class HistoryFilter(FilterSet):

    old_status = ChoiceFilter(choices=STATUS_CHOICES)
    new_status = ChoiceFilter(choices=STATUS_CHOICES)
    change_date = DateFilter(method="datefilter")

    def date_filter(self, queryset, name, value):
        return queryset.filter(
            updated_date__year=value.year,
            updated_date__month=value.month,
            updated_date__day=value.day,
        )


class TaskHistoryViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = TaskHistory.objects.all()
    serializer_class = TaskHistorySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = HistoryFilter

    def get_queryset(self):
        return TaskHistory.objects.filter(
            task_id=self.kwargs["pk"],
            task__user = self.request.user,
        )
