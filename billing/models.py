from django.db import models
from django.conf import settings


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.patient}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Invoice.objects.all().order_by('-id').first()
            if last:
                last_num = int(last.invoice_number.split('-')[1])
                self.invoice_number = f'INV-{str(last_num + 1).zfill(6)}'
            else:
                self.invoice_number = 'INV-000001'
        self.net_amount = self.total_amount - self.discount + self.tax
        self.due_amount = self.net_amount - self.paid_amount
        super().save(*args, **kwargs)

    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.net_amount

    def update_status(self):
        """Set Paid/Partial after a payment has been recorded."""
        if self.status == 'Cancelled':
            return
        if self.is_fully_paid:
            new = 'Paid'
        elif self.paid_amount > 0:
            new = 'Partial'
        else:
            new = 'Pending'
        if new != self.status:
            self.status = new
            self.save()


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('M-Pesa', 'M-Pesa'),
        ('Cash', 'Cash'),
        ('Airtel Money', 'Airtel Money'),
        ('Card', 'Card (Visa / Mastercard)'),
        ('Bank Transfer', 'Bank Transfer / EFT / RTGS'),
        ('Cheque', 'Cheque'),
        ('SHA', 'SHA (Social Health Authority)'),
        ('Insurance', 'Private Insurance'),
    ]
    MOBILE_MONEY_METHODS = ('M-Pesa', 'Airtel Money')

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='Cash')
    transaction_id = models.CharField(
        'Transaction / reference code', max_length=100, blank=True,
        help_text='M-Pesa code (e.g. SJK4H7XY2Q), bank reference, cheque no. or SHA claim number',
    )
    payer_phone = models.CharField('Payer phone', max_length=20, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='received_payments')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} - {self.invoice.invoice_number} - {self.amount}"

    @property
    def receipt_number(self):
        try:
            return self.receipt.receipt_number
        except PaymentReceipt.DoesNotExist:
            return f"PAY-{str(self.pk).zfill(6)}"

    @property
    def created_by(self):
        return self.received_by

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        total_paid = Payment.objects.filter(invoice=self.invoice).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        self.invoice.paid_amount = total_paid
        self.invoice.save()


class PaymentReceipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payment Receipt'
        verbose_name_plural = 'Payment Receipts'

    def __str__(self):
        return f"Receipt {self.receipt_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last = PaymentReceipt.objects.all().order_by('-id').first()
            if last:
                last_num = int(last.receipt_number.split('-')[1])
                self.receipt_number = f'REC-{str(last_num + 1).zfill(6)}'
            else:
                self.receipt_number = 'REC-000001'
        super().save(*args, **kwargs)


class MpesaTransaction(models.Model):
    """An M-Pesa STK Push (Lipa Na M-Pesa Online) request and its outcome."""

    STATUS_CHOICES = [
        ('Pending', 'Awaiting customer'),
        ('Success', 'Successful'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled by customer'),
        ('Timeout', 'Timed out'),
    ]
    # Daraja ResultCode values worth naming
    RESULT_CANCELLED = 1032
    RESULT_TIMEOUT = 1037

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='mpesa_transactions')
    phone = models.CharField(max_length=15, help_text='2547XXXXXXXX')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.CharField(max_length=255, blank=True)
    mpesa_receipt_number = models.CharField(max_length=20, blank=True, db_index=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='mpesa_transaction')
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='mpesa_requests')
    raw_callback = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'M-Pesa Transaction'
        verbose_name_plural = 'M-Pesa Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.checkout_request_id} - {self.invoice.invoice_number} ({self.status})"
