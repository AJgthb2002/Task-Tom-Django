from datetime import datetime, time
from django.core.mail import send_mail
from tasks.models import Task, Report

from task_manager.celery import app


@app.task
def send_email_report(report):
    user = report.user
    valid_user_tasks = Task.objects.filter(user=user, deleted=False)
    pending_tasks = valid_user_tasks.filter(status="PENDING").count()
    in_progress_tasks = valid_user_tasks.filter(status="IN_PROGRESS").count()
    completed_tasks = valid_user_tasks.filter(status="COMPLETED").count() 
    cancelled_tasks = valid_user_tasks.filter(status="CANCELLED").count()
    email_content = f"""
        Hi {user.username},
        \n\nYour tasks report: \n
        Pending tasks =   {pending_tasks} \n
        In-progress tasks = {in_progress_tasks} \n
        Completed tasks = {completed_tasks} \n
        Cancelled tasks = {cancelled_tasks} 
        
        \n\nRegards,\nYour Wonderful Task Manager App
    """
    send_mail("Tasks Report", email_content, "taskmanager@gdc.com", user.email )
    


@app.task
def periodic_emailer():
    currentTime = datetime.now()
    reports = Report.objects.filter(
        send_time__range=(
            time(currentTime.hour, currentTime.minute, 0),
            time(currentTime.hour, currentTime.minute, 59)
        ),
        confirmation=True
    )
    for r in reports:
        send_email_report(r)


app.conf.beat_schedule={"send-task-report" : {
    'task': 'tasks.tasks.periodic_emailer',
    'schedule': 60.0,
},
}
