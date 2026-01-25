from django import forms
from .models import Building, Floor, Room


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['name', 'address', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bino nomi'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Manzil'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tavsif'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ['number', 'description', 'is_active']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Etaj raqami', 'min': 1}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Tavsif'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['number', 'room_type', 'capacity', 'monthly_price', 'status', 'description', 'is_active']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Xona raqami'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'monthly_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }