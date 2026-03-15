from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.db.models import Q
from .models import User
from .forms import LoginForm, UserForm, ProfileForm, PhoneRegistrationForm
from .view_mixins import BuildingStaffMixin


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
            # Telefon raqam bilan ham login qilish imkoniyati
            user = authenticate(request, username=username, password=password)
            if user is None:
                # Telefon raqam bilan qidirish
                try:
                    phone_user = User.objects.get(phone=username)
                    user = authenticate(request, username=phone_user.username, password=password)
                except User.DoesNotExist:
                    pass
            if user is not None:
                login(request, user)
                messages.success(request, f'Xush kelibsiz, {user.get_full_name() or user.username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Telefon raqam yoki parol noto\'g\'ri')
        return render(request, self.template_name, {'form': form})


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = PhoneRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PhoneRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Ro\'yxatdan muvaffaqiyatli o\'tdingiz, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
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


class UserListView(BuildingStaffMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(Q(building_id=bid) | Q(id=self.request.user.id))
        return qs


class UserCreateView(BuildingStaffMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        bid = self.get_user_building_id()
        if bid:
            user.building_id = bid
            user.is_staff = True
        user.save()
        messages.success(self.request, 'Foydalanuvchi muvaffaqiyatli yaratildi')
        return redirect(self.success_url)


class UserUpdateView(BuildingStaffMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_queryset(self):
        qs = User.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(building_id=bid)
        return qs

    def form_valid(self, form):
        messages.success(self.request, 'Foydalanuvchi muvaffaqiyatli yangilandi')
        return super().form_valid(form)


class UserDeleteView(BuildingStaffMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_queryset(self):
        qs = User.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(building_id=bid)
        return qs

    def form_valid(self, form):
        messages.success(self.request, 'Foydalanuvchi o\'chirildi')
        return super().form_valid(form)