from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('create-bill/', views.create_bill, name='create_bill'),

    # Customer
    path('customers/', views.customer_list_create, name='customer_list_create'),
    path('ajax/customers/', views.customer_autocomplete, name='customer_autocomplete'),
    path('customers/edit/<int:pk>/', views.customer_update, name='customer_update'),
    path('customers/delete/<int:pk>/', views.customer_delete, name='customer_delete'),
    path('customers/autocomplete/', views.customer_autocomplete, name='customer_autocomplete'),

    # Staff
    path('staffs/', views.staff_list_create, name='staff_list_create'),
    path('staffs/edit/<int:pk>/', views.staff_update, name='staff_update'),
    path('staffs/delete/<int:pk>/', views.staff_delete, name='staff_delete'),
    path('staffs/autocomplete/', views.staff_autocomplete, name='staff_autocomplete'),

    # Services
    path('ajax/services/', views.service_list_by_category, name='service_list_by_category'),
    path('services/', views.service_list, name='service_list'),
    path('services/add/', views.service_add, name='service_add'),
    path('services/edit/<int:service_id>/', views.service_edit, name='service_edit'),
    path('services/delete/<int:service_id>/', views.service_delete, name='service_delete'),

    # Invoice-related
    # path('invoice/<int:bill_id>/', views.generate_invoice, name='generate_invoice'),
    path('invoice/', views.invoice, name='invoice'),
    path('invoice-preview/<int:bill_id>/', views.invoice_preview, name='invoice_preview'),
    # path('invoice/pdf/<int:bill_id>/', views.generate_invoice, name='generate_invoice'), 
    path('invoice_pdf/<int:bill_id>/', views.invoice_pdf, name='invoice_pdf'),
    path('bills/', views.bill_list, name='list_bills'),
    path('bill_items/', views.view_billitems, name='view_billitems'),
    
    #reports
    path('staff-report/', views.staff_performance_report, name='staff_report'),
    path('salary_report/', views.salary_report, name='salary_report'),
    path('salary-report/monthly/', views.monthly_salary_report, name='monthly_salary_report'),
    path("save-salary/", views.save_salary_record, name="save_salary_record"),
    
    
    path("salary-slip/<int:record_id>/", views.salary_slip_preview, name="salary_slip_preview"),
    path("salary-slip/<int:record_id>/send/", views.salary_slip_send_whatsapp, name="salary_slip_send_whatsapp"),
    path('salary/pdf/<int:record_id>/', views.salary_pdf, name='salary_pdf'),


    path("service_report/daily/", views.service_report, name="daily_service_report"),
    path("service_report/monthly/", views.service_report_monthly, name="monthly_service_report"),
    path("service_report/weekly/", views.service_report_weekly, name="weekly_service_report"),

    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_add, name="product_add"),
    path("stockin/add/", views.stockin_add, name="stockin_add"),
    path("stockout/add/", views.stockout_add, name="stockout_add"),


     # Auth
    path('', views.login_view, name="login"),
    
    path("logout/", views.logout_view, name="logout"),

    


    # Dashboard
    path('base/', views.base, name='base'),
    
]
