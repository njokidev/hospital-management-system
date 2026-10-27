from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import AdminRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Branch
from .forms import BranchForm


class BranchListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Branch
    template_name = 'hospitals/branch_list.html'
    context_object_name = 'branches'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Branches'
        context['table_id'] = 'branchTable'
        context['create_url'] = reverse_lazy('hospitals:branch_create')
        context['create_text'] = 'Add Branch'
        return context


class BranchCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'hospitals/branch_form.html'
    success_url = reverse_lazy('hospitals:branch_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('hospitals:branch_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Branch created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Branch'
        context['cancel_url'] = reverse_lazy('hospitals:branch_list')
        return context


class BranchUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = 'hospitals/branch_form.html'
    success_url = reverse_lazy('hospitals:branch_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('hospitals:branch_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Branch updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Branch'
        context['cancel_url'] = reverse_lazy('hospitals:branch_list')
        return context


class BranchDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Branch
    template_name = 'hospitals/branch_confirm_delete.html'
    success_url = reverse_lazy('hospitals:branch_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('hospitals:branch_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Branch deleted successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Branch'
        context['cancel_url'] = reverse_lazy('hospitals:branch_list')
        return context
