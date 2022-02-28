from datetime import datetime, timedelta
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from tasks.views import *
from tasks.models import *
from tasks.tasks import *
from django.http.response import Http404

class AuthTests(TestCase):
    def test_authenticated(self):
        endpoints = [
            "/tasks/",
            "/pending-tasks/",
            "/completed-tasks/",
            "/create-task/",
        ]

        redirect_url="/user/login/?next="

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, f"/user/login?next={endpoint}")


    def test_login_view(self):
        response = self.client.get("/user/login/")
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertInHTML("Login", response_content)
        self.assertInHTML("Username", response_content, 1)
        self.assertInHTML("Password", response_content, 1)    

    def test_logout(self):
        response = self.client.get("/user/logout/")
        self.assertEqual(response.url, "/")
        self.assertEqual(response.status_code, 302) 

    def test_signup_view(self):
        response = self.client.get("/user/signup/")
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertInHTML("Username", response_content)
        self.assertInHTML("Password", response_content)
        self.assertInHTML("Password confirmation", response_content) 
        self.assertInHTML("Email address", response_content)   
        self.assertInHTML("Report", response_content)      



class AuthorizedViewsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser1", password="test@123")
        self.client = self.factory.get("/")
        self.client.user = self.user
        self.user2 = User.objects.create_user(username="testuser2", password="test@123")
        self.task1 = Task.objects.create(priority=1,title="test task 1", description="testing purpose", user=self.user)
        self.task2 = Task.objects.create(priority=2, title="test task 2", description="testing purpose", user=self.user2)

    def test_add_task_view(self):
        response = GenericTaskCreateView.as_view()(self.client)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertInHTML("Title:", response_content)
        self.assertInHTML("Priority:", response_content)
        self.assertInHTML("Description:", response_content)
        self.assertInHTML("Status:", response_content)

    def test_update_task_view(self):
        response = GenericTaskUpdateView.as_view()(self.client, pk=self.task1.id)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertIn(self.task1.title, response_content)
        self.assertIn(self.task1.description, response_content)

    def test_delete_view(self):
        response = GenericTaskDeleteView.as_view()(self.client, pk=self.task1.id)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertIn(f"{self.task1.title}", response_content)
        self.assertIn("delete", response_content)    

    def test_soft_delete(self):
        self.task1.deleted=True
        self.task1.save()
        self.assertRaises(Http404, GenericTaskUpdateView.as_view(), self.client, pk=self.task1.id)
        self.assertRaises(Http404, GenericTaskDeleteView.as_view(), self.client, pk=self.task1.id)    

    def test_randomtask_access(self):
        self.assertRaises(Http404, GenericTaskUpdateView.as_view(), self.client, pk=self.task2.id)
        self.assertRaises(Http404, GenericTaskDeleteView.as_view(), self.client, pk=self.task2.id)
        self.assertRaises(Http404, GenericTaskUpdateView.as_view(), self.client, pk=5)
        self.assertRaises(Http404, GenericTaskDeleteView.as_view(), self.client, pk=90)

class CRUD_tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

    def add_new_task(self, **kwargs):
        return self.client.post("/tasks/add/",
            {
                "title": kwargs["title"],
                "description": "Testing whether add task works",
                "completed": kwargs.get("completed") or False,
                "deleted": kwargs.get("deleted") or False,
                "status": STATUS_CHOICES[0][1],
                "priority": kwargs.get("priority") or 1,
            },
        )

    def update_task(self, **kwargs):
        task_obj = Task.objects.get(pk=kwargs["pk"])
        return self.client.post(f"/update-task/{task_obj.pk}/",
            {
                "title": kwargs.get("title") or task_obj.title,
                "description": kwargs.get("description") or task_obj.description,
                "completed": kwargs.get("completed") or task_obj.completed,
                "deleted": kwargs.get("deleted") or task_obj.completed,
                "status": kwargs.get("status") or task_obj.status,
                "priority": kwargs.get("priority") or task_obj.priority,
            },
        )

    def create_test_tasks(self):
        for i in range(1, 5):
            Task.objects.create(
                title=f"test task{i}",
                description=f"test task {i} description",
                priority=i,
                user=self.user,
            )

    def test_add_tasks(self):
        self.create_test_tasks()
        self.add_new_task(title="test task", priority=1)
        self.add_new_task(title="another test task", priority=1)
        self.add_new_task(title="yet another test task", priority=1)
        counter = 0
        priorities_exp = [1,2,3,4,5,6,7,8,9]
        for task in Task.objects.filter(user=self.user, completed=False, deleted=False ).order_by("priority"):
            self.assertTrue(priorities_exp[counter]==task.priority)
            counter+=1

    def test_update_tasks(self):
        self.create_test_tasks()
        task = Task.objects.filter(completed=False, deleted=False, user=self.user).order_by("priority")[0]
        self.update_task(pk=task.pk, priority=task.priority + 1)
        counter = 0
        priorities_exp = [2,3,4,5,6,7,8]
        for task in Task.objects.filter(user=self.user, completed=False, deleted=False ).order_by("priority")[:3]:
            self.assertTrue(priorities_exp[counter]==task.priority)
            counter+=1      
    
    def test_task_history(self):
        self.create_test_tasks()
        task_to_update = Task.objects.filter(user=self.user, deleted=False, completed=False)[0]
        old_status = task_to_update.status
        new_status = STATUS_CHOICES[2][1]
        self.update_task(pk=task_to_update.pk, status=new_status)
        history_obj = TaskHistory.objects.filter(task=task_to_update).last()
        self.assertEqual(history_obj.old_status, old_status)
        self.assertEqual(history_obj.new_status, new_status)

class Celery_tests(TestCase): 
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="testpass")
        self.user_settings = Report.objects.create(user=self.user, confirmation=True,
            send_time=time(hour=11, minute=0, second=0),
            last_updated=datetime.now() - timedelta(days=1),
        )

    def test_send_email_report(self):
        Task.objects.bulk_create(
            [
                Task(title="test task 1", user=self.user, status="PENDING"),
                Task(title="test task 2", user=self.user, status="PENDING"),
                Task(title="test task 3", user=self.user, status="IN_PROGRESS"),
                Task(title="test task 4", user=self.user, status="COMPLETED"),
            ]
        )
        report = send_email_report(self)
        email_content = f"""
        Hi {self.user.username},
        \n\nYour tasks report: \n
        Pending tasks =   {2} \n
        In-progress tasks = {1} \n
        Completed tasks = {1} \n
        Cancelled tasks = {0} 
        
        \n\nRegards,\nYour Wonderful Task Manager App
    """
        self.assertEqual(email_content, report)       