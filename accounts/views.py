from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from .models import User, Role
from .forms import UserLoginForm, PatientRegistrationForm, UserUpdateForm, RoleForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            patient_role, created = Role.objects.get_or_create(
                name='Patient',
                defaults={'description': 'Patient role'}
            )
            user.roles.add(patient_role)
            from patients.models import Patient
            national_id = form.cleaned_data.get('national_id', '')
            Patient.objects.create(
                user=user,
                id_type='national_id' if national_id else 'none',
                id_number=national_id,
                sha_number=form.cleaned_data.get('sha_number', ''),
            )
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Medcare Hospital.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_view(request):
    return redirect('dashboard')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form, 'profile_user': request.user})


@login_required
def user_list_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    users = User.objects.all().order_by('-created_at')
    search = request.GET.get('search')
    role = request.GET.get('role')
    status = request.GET.get('status')

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    if role:
        users = users.filter(roles__name=role)

    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)

    context = {
        'users': users,
        'roles': Role.objects.all(),
        'search': search or '',
        'selected_role': role or '',
        'selected_status': status or '',
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
def user_create_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            role_name = request.POST.get('role')
            if role_name:
                role = Role.objects.filter(name__iexact=role_name).first()
                if role:
                    user.roles.add(role)
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm()

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'roles': Role.objects.all(),
        'selected_role': '',
    })


@login_required
def user_update_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            role_name = request.POST.get('role')
            user_obj.roles.clear()
            if role_name:
                role = Role.objects.filter(name__iexact=role_name).first()
                if role:
                    user_obj.roles.add(role)
            messages.success(request, f'User {user_obj.username} updated successfully!')
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm(instance=user_obj)

    current_role = user_obj.roles.first()
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'profile_user': user_obj,
        'roles': Role.objects.all(),
        'selected_role': current_role.name if current_role else '',
    })


@login_required
def user_delete_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('accounts:user_list')

    if request.method == 'POST':
        user_obj.delete()
        messages.success(request, f'User {user_obj.username} deleted successfully!')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_confirm_delete.html', {'object': user_obj})
