from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Task(models.Model):
    STATUS_CHOICES = (
        ("todo" , "To Do"),
        ("inprogress" , "In Progress"),
        ("done" , "Done"),
    )
    PRIORETI_CHOICES = (
        ("low" , "Low"),
        ("medium" , "Medium"),
        ("high" , "High"),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author.username} on {self.task.title}'
    
class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Attachment for {self.task.title}'
class TaskDetail(models.Model):  
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='details')
    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, default="todo")
    priority = models.CharField(max_length=20, choices=Task.PRIORETI_CHOICES, default="medium")
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Details for {self.task.title}'
    
