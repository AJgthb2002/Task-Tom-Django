from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from tasks.views import *
from tasks.apiviews import TaskViewSet, TaskHistoryViewSet
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers

router= SimpleRouter()
router.register('api/task', TaskViewSet)

task_router = routers.NestedSimpleRouter(router, "api/task", lookup="task")
task_router.register("history", TaskHistoryViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tasks/', GenericAllTasksView.as_view()),
    path('pending-tasks/', GenericPendingTasksView.as_view()),
    path('completed-tasks/', GenericCompletedTasksView.as_view()),
    path('create-task/', GenericTaskCreateView.as_view()),
    path('delete-task/<pk>/', GenericTaskDeleteView.as_view()),
    path('update-task/<pk>/', GenericTaskUpdateView.as_view()),
    path('user/signup/', UserCreateView.as_view()),
    path('user/login/', UserLoginView.as_view()),
    path('user/logout/', LogoutView.as_view())
]+ router.urls + task_router.urls
