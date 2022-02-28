
from django.contrib.auth.models import User
from django.db import models
from datetime import time
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

STATUS_CHOICES = [
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
]


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    priority= models.IntegerField(default=0)
    user = models.ForeignKey(User , on_delete=models.CASCADE , null=True,blank=True)
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )

    def __str__(self):
        return self.title

class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    old_status= models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    new_status= models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])  
    change_date = models.DateTimeField(auto_now=True) 
    

    def __str__(self):
        return self.task.title + " changed from " + self.old_status + " to " + self.new_status + " on " + str(self.change_date)


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    confirmation = models.BooleanField(blank=True, default=False, help_text="I want to receive daily reports")
    send_time = models.TimeField(default=time(0, 0, 0), help_text="Enter time in UTC format hh:mm:ss .")
    last_updated = models.DateTimeField(null=True)
    

@receiver(pre_save, sender=Task)
def create_task_history(sender, instance, **kwargs):
    try:
        old_task = Task.objects.get(id=instance.id)
        if old_task.status != instance.status:
            print("Created history")
            TaskHistory.objects.create(old_status=old_task.status, new_status=instance.status, task=instance).save()
    except Exception as e:
        print(e)        
  

