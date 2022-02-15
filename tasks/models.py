
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    oldstatus= models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    newstatus= models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])  
    change_date = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.task.title + " changed from " + self.oldstatus + " to " + self.newstatus + " on " + str(self.change_date)


@receiver(pre_save, sender=Task)
def CreateTaskHistory(sender, instance, **kwargs):
    old_task = Task.objects.get(pk=instance.id)
    if old_task.status != instance.status:
        TaskHistory.objects.create(oldstatus=old_task.status, newstatus=instance.status, task=instance, user=old_task.user).save()