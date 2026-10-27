from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.db.models import Q, Sum, F
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from .models import (
    Supplier, Medicine, MedicineCategory, Prescription,
    PrescriptionItem, DispensedMedicine
)
from .forms import (
    SupplierForm, MedicineForm, MedicineCategoryForm,
    PrescriptionForm, PrescriptionItemForm, DispenseForm
)
from core.mixins import PharmacistRequiredMixin, DoctorOrPharmacistRequiredMixin, DoctorPharmacistOrPatientRequiredMixin


class MedicineListView(LoginRequiredMixin, PharmacistRequiredMixin, ListView):
    model = Medicine
    template_name = 'pharmacy/medicine_list.html'
    context_object_name = 'medicines'
    paginate_by = 25

    def get_queryset(self):
        queryset = Medicine.objects.all()
        search = self.request.GET.get('search')
        category = self.request.GET.get('category')
        stock_alert = self.request.GET.get('stock_alert')
        expiry_alert = self.request.GET.get('expiry_alert')

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(generic_name__icontains=search) |
                Q(batch_number__icontains=search)
            )
        if category:
            queryset = queryset.filter(category=category)
        if stock_alert:
            queryset = queryset.filter(stock_quantity__lte=models.F('minimum_stock'))
        if expiry_alert:
            soon = timezone.now().date() + timedelta(days=90)
            queryset = queryset.filter(expiry_date__lte=soon)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_id'] = 'medicineTable'
        context['categories'] = Medicine.CATEGORY_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['low_stock_count'] = Medicine.objects.filter(
            stock_quantity__lte=F('minimum_stock')
        ).count()
        context['expiring_count'] = Medicine.objects.filter(
            expiry_date__lte=timezone.now().date() + timedelta(days=90)
        ).count()
        return context


class MedicineCreateView(LoginRequiredMixin, PharmacistRequiredMixin, CreateView):
    model = Medicine
    form_class = MedicineForm
    template_name = 'pharmacy/medicine_form.html'
    success_url = reverse_lazy('pharmacy:medicine_list')

    def form_valid(self, form):
        messages.success(self.request, 'Medicine created successfully.')
        return super().form_valid(form)


class MedicineUpdateView(LoginRequiredMixin, PharmacistRequiredMixin, UpdateView):
    model = Medicine
    form_class = MedicineForm
    template_name = 'pharmacy/medicine_form.html'
    success_url = reverse_lazy('pharmacy:medicine_list')

    def form_valid(self, form):
        messages.success(self.request, 'Medicine updated successfully.')
        return super().form_valid(form)


class MedicineDeleteView(LoginRequiredMixin, PharmacistRequiredMixin, DeleteView):
    model = Medicine
    template_name = 'pharmacy/medicine_confirm_delete.html'
    success_url = reverse_lazy('pharmacy:medicine_list')

    def form_valid(self, form):
        messages.success(self.request, 'Medicine deleted successfully.')
        return super().form_valid(form)


class MedicineDetailView(LoginRequiredMixin, PharmacistRequiredMixin, DetailView):
    model = Medicine
    template_name = 'pharmacy/medicine_detail.html'
    context_object_name = 'medicine'


class SupplierListView(LoginRequiredMixin, PharmacistRequiredMixin, ListView):
    model = Supplier
    template_name = 'pharmacy/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 25

    def get_queryset(self):
        queryset = Supplier.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(contact_person__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_id'] = 'supplierTable'
        return context


class SupplierCreateView(LoginRequiredMixin, PharmacistRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'pharmacy/supplier_form.html'
    success_url = reverse_lazy('pharmacy:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Supplier created successfully.')
        return super().form_valid(form)


class SupplierUpdateView(LoginRequiredMixin, PharmacistRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'pharmacy/supplier_form.html'
    success_url = reverse_lazy('pharmacy:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Supplier updated successfully.')
        return super().form_valid(form)


class PrescriptionListView(LoginRequiredMixin, DoctorPharmacistOrPatientRequiredMixin, ListView):
    model = Prescription
    template_name = 'pharmacy/prescription_list.html'
    context_object_name = 'prescriptions'
    paginate_by = 25

    def get_queryset(self):
        queryset = Prescription.objects.select_related('doctor', 'patient')
        if self.request.user.is_patient:
            queryset = queryset.filter(patient__user=self.request.user)
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')

        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search) |
                Q(doctor__first_name__icontains=search) |
                Q(doctor__last_name__icontains=search)
            )
        if status == 'pending':
            queryset = queryset.filter(is_dispensed=False)
        elif status == 'dispensed':
            queryset = queryset.filter(is_dispensed=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_id'] = 'prescriptionTable'
        return context


class PrescriptionCreateView(LoginRequiredMixin, DoctorOrPharmacistRequiredMixin, CreateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = 'pharmacy/prescription_form.html'
    success_url = reverse_lazy('pharmacy:prescription_list')

    def form_valid(self, form):
        form.instance.doctor = self.request.user
        messages.success(self.request, 'Prescription created successfully.')
        return super().form_valid(form)


class PrescriptionDetailView(LoginRequiredMixin, DoctorPharmacistOrPatientRequiredMixin, DetailView):
    model = Prescription
    template_name = 'pharmacy/prescription_detail.html'
    context_object_name = 'prescription'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_patient:
            queryset = queryset.filter(patient__user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('medicine')
        return context


class PrescriptionPrintView(LoginRequiredMixin, DoctorPharmacistOrPatientRequiredMixin, DetailView):
    model = Prescription
    template_name = 'pharmacy/prescription_print.html'
    context_object_name = 'prescription'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_patient:
            queryset = queryset.filter(patient__user=self.request.user)
        return queryset


class PrescriptionPDFExportView(LoginRequiredMixin, DoctorPharmacistOrPatientRequiredMixin, View):
    def get(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)
        if request.user.is_patient and prescription.patient.user != request.user:
            messages.error(request, 'You do not have permission to access this prescription.')
            return redirect('pharmacy:prescription_list')
        template = get_template('pharmacy/prescription_print.html')
        html = template.render({'prescription': prescription})
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), result)
        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.prescription_number}.pdf"'
            return response
        return HttpResponse('Error generating PDF', status=500)


class DispenseView(LoginRequiredMixin, PharmacistRequiredMixin, CreateView):
    model = DispensedMedicine
    form_class = DispenseForm
    template_name = 'pharmacy/prescription_form.html'
    success_url = reverse_lazy('pharmacy:prescription_list')

    def form_valid(self, form):
        prescription = form.cleaned_data['prescription']
        total_cost = sum(
            item.medicine.unit_price * item.quantity
            for item in prescription.items.all()
        )

        DispensedMedicine.objects.create(
            prescription=prescription,
            dispensed_by=self.request.user,
            total_cost=total_cost
        )

        for item in prescription.items.all():
            medicine = item.medicine
            medicine.stock_quantity -= item.quantity
            medicine.save()

        prescription.is_dispensed = True
        prescription.save()

        messages.success(self.request, f'Medicine dispensed successfully. Total cost: {settings.CURRENCY_SYMBOL} {total_cost:,.2f}')
        return redirect(self.success_url)


class StockAlertView(LoginRequiredMixin, PharmacistRequiredMixin, ListView):
    model = Medicine
    template_name = 'pharmacy/stock_alert.html'
    context_object_name = 'medicines'

    def get_queryset(self):
        return Medicine.objects.filter(
            stock_quantity__lte=F('minimum_stock'),
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_id'] = 'stockAlertTable'
        return context


class ExpiryAlertView(LoginRequiredMixin, PharmacistRequiredMixin, ListView):
    model = Medicine
    template_name = 'pharmacy/expiry_alert.html'
    context_object_name = 'medicines'

    def get_queryset(self):
        soon = timezone.now().date() + timedelta(days=90)
        return Medicine.objects.filter(
            expiry_date__lte=soon,
            is_active=True
        ).order_by('expiry_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_id'] = 'expiryAlertTable'
        return context


medicine_list_view = MedicineListView.as_view()
medicine_create_view = MedicineCreateView.as_view()
medicine_update_view = MedicineUpdateView.as_view()
medicine_delete_view = MedicineDeleteView.as_view()
medicine_detail_view = MedicineDetailView.as_view()
supplier_list_view = SupplierListView.as_view()
supplier_create_view = SupplierCreateView.as_view()
supplier_update_view = SupplierUpdateView.as_view()
prescription_list_view = PrescriptionListView.as_view()
prescription_create_view = PrescriptionCreateView.as_view()
prescription_detail_view = PrescriptionDetailView.as_view()
prescription_print_view = PrescriptionPrintView.as_view()
prescription_pdf_view = PrescriptionPDFExportView.as_view()
dispense_view = DispenseView.as_view()
stock_alert_view = StockAlertView.as_view()
expiry_alert_view = ExpiryAlertView.as_view()
