from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.urls import reverse
from .models import Task, TaskDetail, TaskComment, TaskAttachment
from .forms import TaskForm, TaskDetailForm, UserRegistrationForm, CommentForm
from django.views import View                # базовий варіант
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from django.db.models import Count, Q

# TODO: Винести налаштування пагінації в settings.py
TASKS_PER_PAGE = 20  # тимчасово тут, потім перенести

class RegisterView(FormView):
    template_name = 'app_treking/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('task_list')

    # фікс для випадку, коли юзер вже залогінений
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('task_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Registration successful!')
        return super().form_valid(form)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'app_treking/task_list.html'
    context_object_name = 'tasks'
    paginate_by = TASKS_PER_PAGE

    def get_queryset(self):
        # оптимізуємо запити, select_related для деталей і префетч для вкладень
        qs = Task.objects.filter(user=self.request.user).select_related('details').prefetch_related('attachments')

        search_query = self.request.GET.get('search', '')
        if search_query:
            qs = qs.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

        # TODO: переробити на enum/choices для статусів
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            qs = qs.filter(details__status=status_filter)

        # TODO: додати сортування (зараз за умовчанням за id)
        priority_filter = self.request.GET.get('priority', '')
        if priority_filter:
            qs = qs.filter(details__priority=priority_filter)

        # сортуємо за часом створення (спочатку нові)
        qs = qs.order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # перевикористовуємо базовий запит для оптимізації
        base_qs = Task.objects.filter(user=self.request.user)
        tasks = base_qs.select_related('details')
        total_tasks = tasks.count()
        tasks_by_status = tasks.values('details__status').annotate(count=Count('id'))
        tasks_by_priority = tasks.values('details__priority').annotate(count=Count('id'))
        completed_tasks = tasks.filter(details__status='done').count()
        pending_tasks = total_tasks - completed_tasks

        # рахуємо % виконання (захист від ділення на 0)
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        context.update({
            'search_query': self.request.GET.get('search', ''),
            'status_filter': self.request.GET.get('status', ''),
            'priority_filter': self.request.GET.get('priority', ''),
            'total_tasks': total_tasks,
            'tasks_by_status': tasks_by_status,
            'tasks_by_priority': tasks_by_priority,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': completion_rate,
        })
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'app_treking/task_detail.html'
    context_object_name = 'task'
    pk_url_kwarg = 'task_id'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # оптимізуємо запити до коментарів
        context['comments'] = self.object.comments.select_related('author').order_by('-created_at')
        context['comment_form'] = CommentForm()
        return context

    def post(self, request, *args, **kwargs):
        # перевіряємо, чи задача не видалена
        self.object = self.get_object()
        if not self.object:
            messages.error(request, 'Task was deleted')
            return redirect('task_list')

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = self.object
            comment.author = request.user
            try:
                comment.save()
                messages.success(request, 'Comment added successfully!')
                return redirect('task_detail', task_id=self.object.id)
            except Exception as e:
                # логуємо помилку якщо є
                print(f"Error saving comment: {e}")  # TODO: додати нормальне логування
                messages.error(request, 'Error saving comment. Please try again.')

        context = self.get_context_data()
        context['comment_form'] = form
        return self.render_to_response(context)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'app_treking/add_task.html'
    success_url = reverse_lazy('task_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'detail_form' not in context:
            context['detail_form'] = TaskDetailForm()
        # provide task_form variable for templates expecting that name
        context['task_form'] = context.get('form') or self.get_form()
        return context

    def form_valid(self, form):
        # save main task
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()

        # save details
        detail_form = TaskDetailForm(self.request.POST)
        if detail_form.is_valid():
            detail = detail_form.save(commit=False)
            detail.task = self.object
            detail.save()

        # attachments
        for f in self.request.FILES.getlist('attachments'):
            TaskAttachment.objects.create(task=self.object, file=f)

        messages.success(self.request, 'Task created successfully.')
        return redirect(self.success_url)


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'app_treking/add_task.html'
    pk_url_kwarg = 'task_id'

    def test_func(self):
        task = self.get_object()
        return task.user == self.request.user or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['detail_form'] = TaskDetailForm(instance=self.object.details)
        except TaskDetail.DoesNotExist:
            context['detail_form'] = TaskDetailForm()
        context['edit_mode'] = True
        # templates expect 'task' and 'task_form'
        context['task'] = self.object
        context['task_form'] = context.get('form') or self.get_form()
        return context

    def form_valid(self, form):
        try:
            self.object = form.save()
            detail_form = TaskDetailForm(self.request.POST, instance=getattr(self.object, 'details', None))
            if detail_form.is_valid():
                detail = detail_form.save(commit=False)
                detail.task = self.object
                detail.save()

                # обробляємо нові файли
                for f in self.request.FILES.getlist('attachments'):
                    # TODO: додати валідацію розміру/типу файлів
                    TaskAttachment.objects.create(task=self.object, file=f)

                messages.success(self.request, 'Task updated successfully.')
            else:
                messages.error(self.request, 'Error updating task details')
                return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error updating task: {str(e)}')
            return self.form_invalid(form)

        return redirect('task_detail', task_id=self.object.id)


class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Task
    template_name = 'app_treking/confirm_delete.html'
    pk_url_kwarg = 'task_id'

    def test_func(self):
        task = self.get_object()
        return task.user == self.request.user or self.request.user.is_staff

    def get_success_url(self):
        messages.success(self.request, 'Task deleted successfully')
        return reverse_lazy('task_list')

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            return response
        except Exception as e:
            messages.error(request, f'Error deleting task: {str(e)}')
            return redirect('task_list')


class MarkTaskDoneView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        task = get_object_or_404(Task, id=self.kwargs.get('task_id'))
        return task.user == self.request.user or self.request.user.is_staff

    def post(self, request, task_id):
        try:
            # перевикористовуємо task з test_func
            task = get_object_or_404(Task, id=task_id)
            task_detail = task.details
        except TaskDetail.DoesNotExist:
            # якщо деталей нема - створюємо
            task_detail = TaskDetail.objects.create(task=task)
        except Exception as e:
            messages.error(request, f'Error marking task as done: {str(e)}')
            return redirect('task_list')

        task_detail.status = 'done'
        task_detail.save()
        messages.success(request, 'Task marked as done')
        return redirect('task_detail', task_id=task.id)
