from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Talaba sahifalari
    path('', views.StudentHomeView.as_view(), name='home'),
    path('rooms/', views.AvailableRoomsView.as_view(), name='available_rooms'),
    path('rooms/<int:pk>/', views.BuildingDetailForApplicantView.as_view(), name='building_detail'),
    path('nizom/', views.DormRulesView.as_view(), name='dorm_rules'),
    path('apply/', views.ApplicationCreateView.as_view(), name='apply'),
    path('my/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='detail'),

    # Admin sahifalari
    path('admin/list/', views.ApplicationListView.as_view(), name='admin_list'),
    path('admin/<int:pk>/review/', views.ApplicationReviewView.as_view(), name='admin_review'),
    path('admin/<int:pk>/confirm-payment/', views.ConfirmPaymentView.as_view(), name='confirm_payment'),

    # API
    path('api/floors/<int:building_id>/', views.get_floors_json, name='api_floors'),
    path('api/rooms/<int:floor_id>/', views.get_rooms_json, name='api_rooms'),
]
