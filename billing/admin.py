from django.contrib import admin
from .models import Invoice, InvoiceItem, Payment, PaymentReceipt, MpesaTransaction


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'patient', 'total_amount', 'discount', 'tax',
                    'net_amount', 'paid_amount', 'due_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['invoice_number', 'patient__patient_id', 'patient__user__first_name',
                     'patient__user__last_name']
    inlines = [InvoiceItemInline, PaymentInline]
    readonly_fields = ['invoice_number', 'net_amount', 'due_amount', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    actions = ['mark_as_paid', 'export_as_csv']

    def mark_as_paid(self, request, queryset):
        updated = queryset.filter(status__in=['Unpaid', 'Partial']).update(status='Paid')
        self.message_user(request, f'{updated} invoice(s) marked as paid.')
    mark_as_paid.short_description = "Mark selected invoices as paid"

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="invoices.csv"'
        writer = csv.writer(response)
        writer.writerow(['Invoice Number', 'Patient', 'Total Amount', 'Discount', 'Tax',
                         'Net Amount', 'Paid Amount', 'Due Amount', 'Status', 'Created At'])
        for invoice in queryset:
            writer.writerow([
                invoice.invoice_number, invoice.patient, invoice.total_amount,
                invoice.discount, invoice.tax, invoice.net_amount, invoice.paid_amount,
                invoice.due_amount, invoice.status, invoice.created_at
            ])
        return response
    export_as_csv.short_description = "Export selected invoices as CSV"


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'total_price']
    search_fields = ['description']
    raw_id_fields = ['invoice']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'amount', 'payment_method', 'transaction_id',
                    'received_by', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['invoice__invoice_number', 'transaction_id']
    raw_id_fields = ['invoice', 'received_by']
    date_hierarchy = 'created_at'


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'payment', 'generated_at']
    raw_id_fields = ['payment']
    date_hierarchy = 'generated_at'


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['checkout_request_id', 'invoice', 'phone', 'amount', 'status', 'mpesa_receipt_number', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['checkout_request_id', 'mpesa_receipt_number', 'phone', 'invoice__invoice_number']
    readonly_fields = [f.name for f in MpesaTransaction._meta.fields]
