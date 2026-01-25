from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),

    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Items
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_edit'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),

    # Room Inventory
    path('room/<int:room_pk>/', views.RoomInventoryView.as_view(), name='room_inventory'),
    path('room/<int:room_pk>/add/', views.RoomInventoryAddView.as_view(), name='room_inventory_add'),
    path('room-inventory/<int:pk>/edit/', views.RoomInventoryUpdateView.as_view(), name='room_inventory_edit'),
    path('room-inventory/<int:pk>/delete/', views.RoomInventoryDeleteView.as_view(), name='room_inventory_delete'),

    # Reports
    path('report/', views.InventoryReportView.as_view(), name='report'),
]