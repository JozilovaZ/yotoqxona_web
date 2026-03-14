from django import forms
from .models import Building, Floor, Room


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['name', 'image', 'city', 'street', 'address', 'monthly_price', 'daily_price', 'latitude', 'longitude', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bino nomi'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shahar'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ko'cha"}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Manzil'}),
            'monthly_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000', 'placeholder': "Oylik narx (so'm)"}),
            'daily_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000', 'placeholder': "Kunlik narx (so'm)"}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Masalan: 41.311081'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Masalan: 69.240562'}),
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
        fields = ['number', 'room_type', 'capacity', 'status', 'description', 'is_active']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Xona raqami'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }