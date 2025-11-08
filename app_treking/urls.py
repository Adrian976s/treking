from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    RegisterView,
    TaskListView,
    TaskDetailView,
    TaskCreateView,
    TaskUpdateView,
    TaskDeleteView,
    MarkTaskDoneView,
)

urlpatterns = [
    path('', TaskListView.as_view(), name='task_list'),
    path('add/', TaskCreateView.as_view(), name='add_task'),
    path('task/<int:task_id>/', TaskDetailView.as_view(), name='task_detail'),
    path('task/<int:task_id>/edit/', TaskUpdateView.as_view(), name='edit_task'),
    path('task/<int:task_id>/delete/', TaskDeleteView.as_view(), name='delete_task'),
    path('task/<int:task_id>/done/', MarkTaskDoneView.as_view(), name='mark_task_done'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='app_treking/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]