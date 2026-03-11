from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Ro'yxat va qidiruv
    path('', views.StudentListView.as_view(), name='student_list'),

    # Yangi talaba qo'shish
    path('create/', views.StudentCreateView.as_view(), name='student_create'),

    # Talaba profili
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),

    # Tahrirlash
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),

    # O'chirish
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),

    # Xonadan xonaga ko'chirish
    path('<int:pk>/transfer/', views.StudentTransferView.as_view(), name='student_transfer'),

    # Yotoqxonadan chiqarish (Checkout)
    path('<int:pk>/checkout/', views.StudentCheckoutView.as_view(), name='student_checkout'),

    # Ko'chirishlar tarixi
    path('transfers/', views.TransferHistoryView.as_view(), name='transfer_history'),
]