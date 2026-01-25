from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from .models import User
from .forms import LoginForm, UserForm, ProfileForm


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Xush kelibsiz, {user.get_full_name() or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Login yoki parol noto\'g\'ri')
        return render(request, self.template_name, {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Siz tizimdan chiqdingiz')
    return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Foydalanuvchi muvaffaqiyatli yaratildi')
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Foydalanuvchi muvaffaqiyatli yangilandi')
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Foydalanuvchi o\'chirildi')
        return super().form_valid(form)