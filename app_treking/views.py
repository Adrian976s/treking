from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .models import Task, TaskDetail, TaskComment
from .forms import TaskForm, TaskDetailForm, UserRegistrationForm, CommentForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('task_list')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = UserRegistrationForm()
    return render(request, 'app_treking/register.html', {'form': form})

from django.db.models import Count
from django.db.models import Q

@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(details__status=status_filter)
    
    # Filter by priority
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tasks = tasks.filter(details__priority=priority_filter)

    # Statistics
    total_tasks = tasks.count()
    tasks_by_status = Task.objects.filter(user=request.user).values('details__status').annotate(
        count=Count('id')
    )
    tasks_by_priority = Task.objects.filter(user=request.user).values('details__priority').annotate(
        count=Count('id')
    )
    completed_tasks = Task.objects.filter(user=request.user, details__status='done').count()
    pending_tasks = total_tasks - completed_tasks

    context = {
        'tasks': tasks,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'total_tasks': total_tasks,
        'tasks_by_status': tasks_by_status,
        'tasks_by_priority': tasks_by_priority,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }
    
    return render(request, 'app_treking/task_list.html', context)

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    comments = task.comments.all().order_by('-created_at')
    
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
            return redirect('task_detail', task_id=task.id)
    else:
        comment_form = CommentForm()
    
    return render(request, 'app_treking/task_detail.html', {
        'task': task,
        'comments': comments,
        'comment_form': comment_form
    })

@login_required
def add_task(request):
    if request.method == 'POST':
        task_form = TaskForm(request.POST)
        detail_form = TaskDetailForm(request.POST)
        
        if task_form.is_valid() and detail_form.is_valid():
            task = task_form.save(commit=False)
            task.user = request.user
            task.save()
            
            task_detail = detail_form.save(commit=False)
            task_detail.task = task
            task_detail.save()
            
            return redirect('task_list')
    else:
        task_form = TaskForm()
        detail_form = TaskDetailForm()
    
    return render(request, 'app_treking/add_task.html', {
        'task_form': task_form,
        'detail_form': detail_form
    })
