from django.urls import path
from . import views

app_name = 'buildings'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Buildings
    path('list/', views.BuildingListView.as_view(), name='building_list'),
    path('create/', views.BuildingCreateView.as_view(), name='building_create'),
    path('<int:pk>/', views.BuildingDetailView.as_view(), name='building_detail'),
    path('<int:pk>/stats/', views.BuildingStatsView.as_view(), name='building_stats'),
    path('<int:pk>/edit/', views.BuildingUpdateView.as_view(), name='building_update'),
    path('<int:pk>/delete/', views.BuildingDeleteView.as_view(), name='building_delete'),

    # Floors
    path('<int:building_pk>/floors/', views.FloorListView.as_view(), name='floor_list'),
    path('<int:building_pk>/floors/create/', views.FloorCreateView.as_view(), name='floor_create'),
    # SHU YERDA: floor_edit edi, floor_update qildik (shablonga moslash uchun)
    path('floors/<int:pk>/edit/', views.FloorUpdateView.as_view(), name='floor_update'),
    path('floors/<int:pk>/delete/', views.FloorDeleteView.as_view(), name='floor_delete'),

    # Rooms
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('floors/<int:floor_pk>/rooms/create/', views.RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('rooms/<int:pk>/edit/', views.RoomUpdateView.as_view(), name='room_edit'),
    path('rooms/<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room_delete'),

    # API
    path('api/floors/<int:building_id>/', views.get_floors_api, name='api_floors'),
    path('api/rooms/<int:floor_id>/', views.get_rooms_api, name='api_rooms'),
]