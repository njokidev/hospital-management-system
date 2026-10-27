from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/create/', views.invoice_create_view, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoices/<int:pk>/update/', views.invoice_update_view, name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.invoice_delete_view, name='invoice_delete'),
    path('invoices/<int:pk>/print/', views.invoice_print_view, name='invoice_print'),
    path('invoices/<int:invoice_id>/add-item/', views.add_invoice_item_view, name='add_item'),
    path('invoices/<int:invoice_id>/payment/', views.payment_create_view, name='payment_create'),
    path('items/<int:item_id>/delete/', views.delete_invoice_item_view, name='delete_item'),
    path('payments/', views.payment_list_view, name='payment_list'),
    path('payments/<int:pk>/', views.payment_detail_view, name='payment_detail'),
    path('dues/', views.due_list_view, name='due_list'),
    path('revenue-report/', views.revenue_report_view, name='revenue_report'),
    # M-Pesa
    path('invoices/<int:invoice_id>/mpesa/', views.mpesa_stk_push_view, name='mpesa_stk_push'),
    path('mpesa/transactions/<int:pk>/status/', views.mpesa_status_view, name='mpesa_status'),
    path('mpesa/callback/<str:token>/', views.mpesa_callback_view, name='mpesa_callback'),
]
