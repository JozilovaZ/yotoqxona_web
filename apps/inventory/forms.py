from django import forms
from .models import InventoryCategory, InventoryItem, RoomInventory


class CategoryForm(forms.ModelForm):
    class Meta:
        model = InventoryCategory
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-tv (Bootstrap Icons)'}),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['category', 'name', 'description', 'unit_price']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
        }


class RoomInventoryForm(forms.ModelForm):
    class Meta:
        model = RoomInventory
        fields = ['item', 'quantity', 'condition', 'serial_number', 'purchase_date', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }