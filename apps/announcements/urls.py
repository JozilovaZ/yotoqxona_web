from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.AnnouncementListView.as_view(), name='list'),
    path('create/', views.AnnouncementCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.AnnouncementUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='delete'),
]
