
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tasks.models import Task


class AuthorisedTasksGenerator(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)

class TaskCreateForm(ModelForm):
    class Meta:
        model=Task
        fields=['title', 'description','priority', 'status','completed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'mb-5 rounded w-full h-8 px-2 bg-gray-100'   
        self.fields['description'].widget.attrs['class'] = 'mb-5 rounded w-full h-28 px-2 bg-gray-100'   
        self.fields['priority'].widget.attrs['class'] = 'mb-5 rounded w-full h-8 px-2 bg-gray-100' 
        self.fields['status'].widget.attrs['class'] = 'mb-5 rounded w-full h-8 px-2 bg-gray-100' 
        self.fields['completed'].widget.attrs['class'] = 'mb-8 h-4 w-4'   
        

    def clean_priority(self):
        priority = self.cleaned_data.get("priority")
        if priority <= 0:
            raise ValidationError("Priority should be higher than 0")
        return priority


class GenericAllTasksView(AuthorisedTasksGenerator,ListView):
    template_name = "user_tasks.html"
    
    def get_context_data(self, **kwargs):
        tasks_list= Task.objects.filter(deleted=False, user= self.request.user, completed=False).order_by('priority')
        completed_list= Task.objects.filter(deleted=False, user= self.request.user, completed=True).order_by('priority')

        return {"tasks" : tasks_list , 
        "completed":completed_list, 
        "completed_cnt": len(completed_list), 
        "total_cnt": len(tasks_list)+len(completed_list),
        "username": self.request.user}

class GenericPendingTasksView(AuthorisedTasksGenerator,ListView):
    template_name = "user_tasks.html"

    def get_context_data(self, **kwargs):
        tasks_list= Task.objects.filter(deleted=False, user= self.request.user, completed=False).order_by('priority')
        completed_list= Task.objects.filter(deleted=False, user= self.request.user, completed=True).order_by('priority')

        return {"tasks":tasks_list, 
        "completed":[], 
        "completed_cnt": len(completed_list), 
        "total_cnt": len(tasks_list)+len(completed_list), "username": self.request.user}

class GenericCompletedTasksView(AuthorisedTasksGenerator,ListView):
    template_name = "user_tasks.html"

    def get_context_data(self, **kwargs):
        tasks_list= Task.objects.filter(deleted=False, user= self.request.user, completed=False).order_by('priority')
        completed_list= Task.objects.filter(deleted=False, user= self.request.user, completed=True).order_by('priority')

        return {"tasks":completed_list, 
        "completed":[], 
        "completed_cnt": len(completed_list), 
        "total_cnt": len(tasks_list)+len(completed_list), "username": self.request.user}

def update_priorities(user,priority_new):
    tasks_to_update = []
    all_task_list = Task.objects.filter(deleted=False,completed=False,user=user,priority__gte=priority_new).order_by('priority')
    
    for task in all_task_list:
        if task.priority == priority_new:
            task.priority += 1
            priority_new += 1
            tasks_to_update.append(task)
    Task.objects.bulk_update(tasks_to_update,['priority'])     

class GenericTaskCreateView(CreateView):
    form_class= TaskCreateForm
    template_name="task_create.html"
    success_url="/tasks"

    def form_valid(self, form):
        priority_new = form.cleaned_data["priority"]
        user = self.request.user
        tasks = Task.objects.filter(deleted=False, user= self.request.user, completed=False, priority=priority_new)
        if tasks.exists():
            update_priorities(user , priority_new)

        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect("/tasks")


class GenericTaskDeleteView(AuthorisedTasksGenerator, DeleteView):
    model=Task
    template_name="task_delete.html"
    success_url="/tasks"

class GenericTaskUpdateView(AuthorisedTasksGenerator, UpdateView):
    model=Task
    form_class=TaskCreateForm
    template_name="task_update.html"
    success_url="/tasks"

    def form_valid(self, form):
        priority_new = form.cleaned_data["priority"]
        user = self.request.user
        if 'priority' in form.changed_data:
            tasks = Task.objects.filter(deleted=False, user= self.request.user, completed=False, priority=priority_new)
            if tasks.exists():
                update_priorities(user , priority_new)

        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect("/tasks")

class UserCreateView(CreateView):
    form_class= UserCreationForm
    template_name="signup.html"
    success_url="/user/login/"

class UserLoginView(LoginView):
    template_name="login.html"



