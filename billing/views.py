import json
import logging
from decimal import Decimal, ROUND_CEILING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.crypto import constant_time_compare

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta

from .models import Invoice, InvoiceItem, Payment, PaymentReceipt, MpesaTransaction
from .forms import InvoiceForm, InvoiceItemForm, PaymentForm, InvoiceFilterForm
from core.mixins import AccountantRequiredMixin, PatientOrAccountantRequiredMixin, BillingViewMixin
from core.kenya import mpesa_msisdn
from . import mpesa


class InvoiceListView(LoginRequiredMixin, BillingViewMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 25

    def get_queryset(self):
        queryset = Invoice.objects.select_related('patient', 'created_by')
        if self.request.user.is_patient:
            queryset = queryset.filter(patient__user=self.request.user)
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')

        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(patient__patient_id__icontains=search) |
                Q(patient__user__first_name__icontains=search) |
                Q(patient__user__last_name__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_id'] = 'invoiceTable'
        context['filter_form'] = InvoiceFilterForm(self.request.GET)
        context['total_invoices'] = Invoice.objects.count()
        context['total_pending'] = Invoice.objects.filter(status='Pending').count()
        context['total_paid'] = Invoice.objects.filter(status='Paid').count()
        context['total_revenue'] = Invoice.objects.filter(status='Paid').aggregate(total=Sum('net_amount'))['total'] or 0
        return context


invoice_list_view = InvoiceListView.as_view()


class InvoiceCreateView(LoginRequiredMixin, AccountantRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_form.html'
    success_url = reverse_lazy('billing:invoice_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Invoice created successfully.')
        return super().form_valid(form)


invoice_create_view = InvoiceCreateView.as_view()


class InvoiceUpdateView(LoginRequiredMixin, AccountantRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_form.html'
    success_url = reverse_lazy('billing:invoice_list')

    def form_valid(self, form):
        messages.success(self.request, 'Invoice updated successfully.')
        return super().form_valid(form)


invoice_update_view = InvoiceUpdateView.as_view()


class InvoiceDetailView(LoginRequiredMixin, PatientOrAccountantRequiredMixin, DetailView):
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_patient:
            queryset = queryset.filter(patient__user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        context['item_form'] = InvoiceItemForm()
        context['payment_form'] = PaymentForm()
        context['mpesa_transactions'] = self.object.mpesa_transactions.all()[:5]
        context['mpesa_ready'] = mpesa.is_configured()
        context['can_pay'] = _can_pay_invoice(self.request.user, self.object)
        return context


invoice_detail_view = InvoiceDetailView.as_view()


class InvoiceDeleteView(LoginRequiredMixin, AccountantRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'billing/invoice_confirm_delete.html'
    success_url = reverse_lazy('billing:invoice_list')

    def form_valid(self, form):
        messages.success(self.request, 'Invoice deleted successfully.')
        return super().form_valid(form)


invoice_delete_view = InvoiceDeleteView.as_view()


class InvoicePrintView(LoginRequiredMixin, PatientOrAccountantRequiredMixin, DetailView):
    model = Invoice
    template_name = 'billing/invoice_print.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_patient:
            queryset = queryset.filter(patient__user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        return context


invoice_print_view = InvoicePrintView.as_view()


@login_required
def payment_create_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.received_by = request.user
            payment.save()
            PaymentReceipt.objects.create(payment=payment)
            invoice.refresh_from_db()
            invoice.update_status()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        form = PaymentForm()
    return render(request, 'billing/payment_form.html', {'form': form, 'invoice': invoice})


class PaymentListView(LoginRequiredMixin, AccountantRequiredMixin, ListView):
    model = Payment
    template_name = 'billing/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 25

    def get_queryset(self):
        return Payment.objects.select_related('invoice', 'received_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_id'] = 'paymentTable'
        return context


payment_list_view = PaymentListView.as_view()


class PaymentDetailView(LoginRequiredMixin, AccountantRequiredMixin, DetailView):
    model = Payment
    template_name = 'billing/payment_detail.html'
    context_object_name = 'payment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['receipt'] = self.object.receipt
        except PaymentReceipt.DoesNotExist:
            context['receipt'] = None
        return context


payment_detail_view = PaymentDetailView.as_view()


class DueListView(LoginRequiredMixin, AccountantRequiredMixin, ListView):
    model = Invoice
    template_name = 'billing/due_list.html'
    context_object_name = 'invoices'
    paginate_by = 25

    def get_queryset(self):
        return Invoice.objects.filter(due_amount__gt=0).select_related('patient')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_id'] = 'dueTable'
        context['total_due'] = Invoice.objects.filter(due_amount__gt=0).aggregate(
            total=Sum('due_amount')
        )['total'] or 0
        return context


due_list_view = DueListView.as_view()


class RevenueReportView(LoginRequiredMixin, AccountantRequiredMixin, ListView):
    model = Invoice
    template_name = 'billing/revenue_report.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        return Invoice.objects.filter(status='Paid')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        context['total_revenue'] = Invoice.objects.filter(status='Paid').aggregate(
            total=Sum('net_amount'))['total'] or 0
        context['today_revenue'] = Invoice.objects.filter(
            status='Paid', created_at__date=today).aggregate(
            total=Sum('net_amount'))['total'] or 0
        context['weekly_revenue'] = Invoice.objects.filter(
            status='Paid', created_at__date__gte=week_ago).aggregate(
            total=Sum('net_amount'))['total'] or 0
        context['monthly_revenue'] = Invoice.objects.filter(
            status='Paid', created_at__date__gte=month_ago).aggregate(
            total=Sum('net_amount'))['total'] or 0
        context['total_outstanding'] = Invoice.objects.filter(
            due_amount__gt=0).aggregate(total=Sum('due_amount'))['total'] or 0
        return context


revenue_report_view = RevenueReportView.as_view()


@login_required
def add_invoice_item_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if request.method == 'POST':
        form = InvoiceItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.invoice = invoice
            item.save()
            invoice.total_amount = invoice.items.aggregate(
                total=Sum('total_price'))['total'] or 0
            invoice.save()
            messages.success(request, 'Item added to invoice.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    return redirect('billing:invoice_detail', pk=invoice.pk)


@login_required
def delete_invoice_item_view(request, item_id):
    item = get_object_or_404(InvoiceItem, pk=item_id)
    invoice = item.invoice
    item.delete()
    invoice.total_amount = invoice.items.aggregate(
        total=Sum('total_price'))['total'] or 0
    invoice.save()
    messages.success(request, 'Item removed from invoice.')
    return redirect('billing:invoice_detail', pk=invoice.pk)


# ─────────────────────────────── M-Pesa (STK Push) ───────────────────────────────
mpesa_logger = logging.getLogger('billing.mpesa')


def _can_pay_invoice(user, invoice):
    if user.is_superuser or user.roles.filter(name__in=['Accountant', 'Receptionist', 'Hospital Admin']).exists():
        return True
    return invoice.patient.user_id == user.id


@login_required
@require_POST
def mpesa_stk_push_view(request, invoice_id):
    """Send an M-Pesa payment prompt to the payer's phone for this invoice."""
    invoice = get_object_or_404(Invoice.objects.select_related('patient__user'), pk=invoice_id)
    if not _can_pay_invoice(request.user, invoice):
        messages.error(request, 'You do not have permission to pay this invoice.')
        return redirect('dashboard')
    if invoice.due_amount <= 0:
        messages.info(request, 'This invoice has no outstanding balance.')
        return redirect('billing:invoice_detail', pk=invoice.pk)

    try:
        msisdn = mpesa_msisdn(request.POST.get('phone', ''))
        # M-Pesa only accepts whole shillings; round the balance up so the invoice clears
        amount = Decimal(request.POST.get('amount') or invoice.due_amount).quantize(Decimal('1'), rounding=ROUND_CEILING)
        if amount < 1 or amount > invoice.due_amount.quantize(Decimal('1'), rounding=ROUND_CEILING):
            raise ValidationError('Amount must be between KSh 1 and the outstanding balance.')
        data = mpesa.stk_push(msisdn, amount, invoice.invoice_number, 'Hospital bill')
    except ValidationError as e:
        messages.error(request, ' '.join(e.messages))
        return redirect('billing:invoice_detail', pk=invoice.pk)
    except (ArithmeticError, ValueError):
        messages.error(request, 'Enter a valid amount.')
        return redirect('billing:invoice_detail', pk=invoice.pk)
    except mpesa.MpesaError as e:
        messages.error(request, f'M-Pesa: {e}')
        return redirect('billing:invoice_detail', pk=invoice.pk)

    MpesaTransaction.objects.create(
        invoice=invoice,
        phone=msisdn,
        amount=amount,
        merchant_request_id=data.get('MerchantRequestID', ''),
        checkout_request_id=data['CheckoutRequestID'],
        initiated_by=request.user,
    )
    messages.success(request, f'M-Pesa prompt sent to {msisdn}. Ask the payer to enter their M-Pesa PIN.')
    return redirect('billing:invoice_detail', pk=invoice.pk)


@csrf_exempt
@require_POST
def mpesa_callback_view(request, token):
    """Receives the STK Push result from Safaricom. Always acknowledges with 200."""
    ack = JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
    if not constant_time_compare(token, settings.MPESA_CALLBACK_TOKEN):
        mpesa_logger.warning('M-Pesa callback with bad token from %s', request.META.get('REMOTE_ADDR'))
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Rejected'}, status=403)
    try:
        body = json.loads(request.body)
        result = mpesa.parse_callback(body)
    except (ValueError, KeyError, TypeError):
        mpesa_logger.warning('Malformed M-Pesa callback: %r', request.body[:500])
        return ack

    with transaction.atomic():
        txn = (MpesaTransaction.objects.select_for_update()
               .select_related('invoice').filter(checkout_request_id=result['checkout_request_id']).first())
        if txn is None:
            mpesa_logger.warning('M-Pesa callback for unknown CheckoutRequestID %s', result['checkout_request_id'])
            return ack
        if txn.status != 'Pending':
            return ack  # duplicate delivery – already processed

        txn.result_code = result['result_code']
        txn.result_desc = result['result_desc'][:255]
        txn.raw_callback = body
        if result['result_code'] == 0:
            txn.status = 'Success'
            txn.mpesa_receipt_number = result['receipt_number']
            txn.transaction_date = result['transaction_date']
            paid = Decimal(str(result['amount'])) if result['amount'] is not None else txn.amount
            payment = Payment.objects.create(
                invoice=txn.invoice,
                amount=paid,
                payment_method='M-Pesa',
                transaction_id=result['receipt_number'],
                payer_phone='+' + (result['phone'] or txn.phone),
                received_by=txn.initiated_by,
                notes='Lipa Na M-Pesa (STK Push)',
            )
            PaymentReceipt.objects.create(payment=payment)
            txn.payment = payment
            txn.invoice.refresh_from_db()
            txn.invoice.update_status()
        elif result['result_code'] == MpesaTransaction.RESULT_CANCELLED:
            txn.status = 'Cancelled'
        elif result['result_code'] == MpesaTransaction.RESULT_TIMEOUT:
            txn.status = 'Timeout'
        else:
            txn.status = 'Failed'
        txn.save()
    return ack


@login_required
def mpesa_status_view(request, pk):
    """Polled by the invoice page while a prompt is pending."""
    txn = get_object_or_404(MpesaTransaction.objects.select_related('invoice__patient'), pk=pk)
    if not _can_pay_invoice(request.user, txn.invoice):
        return JsonResponse({'error': 'forbidden'}, status=403)
    return JsonResponse({
        'status': txn.status,
        'status_display': txn.get_status_display(),
        'receipt': txn.mpesa_receipt_number,
        'message': txn.result_desc,
    })
