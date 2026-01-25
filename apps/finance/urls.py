from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Dashboard
    path('', views.FinanceDashboardView.as_view(), name='dashboard'),

    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/bulk/', views.BulkInvoiceCreateView.as_view(), name='invoice_bulk'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.InvoiceUpdateView.as_view(), name='invoice_edit'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),

    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),

    # Debtors
    path('debtors/', views.DebtorListView.as_view(), name='debtor_list'),

    # Reports
    path('reports/', views.FinanceReportView.as_view(), name='reports'),
]