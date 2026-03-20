from django import forms
from .models import Application
from buildings.models import Building, Floor, Room


class ApplicationForm(forms.ModelForm):
    """Talaba ariza formasi"""

    class Meta:
        model = Application
        fields = [
            'first_name', 'last_name', 'middle_name', 'phone',
            'student_id', 'faculty', 'group', 'course',
            'room', 'message'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'room': forms.HiddenInput(),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "Qo'shimcha ma'lumot..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get('room'):
            try:
                room_id = int(self.data.get('room'))
                self.fields['room'].queryset = Room.objects.filter(pk=room_id)
            except (ValueError, TypeError):
                self.fields['room'].queryset = Room.objects.none()
        elif self.initial.get('room'):
            room = self.initial['room']
            room_id = room.pk if hasattr(room, 'pk') else room
            self.fields['room'].queryset = Room.objects.filter(pk=room_id)
        else:
            self.fields['room'].queryset = Room.objects.none()

    def clean_room(self):
        room = self.cleaned_data.get('room')
        if room and room.available_beds <= 0:
            raise forms.ValidationError("Bu xonada bo'sh joy qolmagan.")
        return room


class ApplicationReviewForm(forms.Form):
    """Admin ariza ko'rib chiqish formasi"""
    ACTION_CHOICES = [
        ('payment_required', "To'lov so'rash"),
        ('approved', 'Tasdiqlash'),
        ('rejected', 'Rad etish'),
    ]
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label="Harakat",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_amount = forms.DecimalField(
        max_digits=12, decimal_places=2,
        required=False,
        label="To'lov summasi",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    admin_note = forms.CharField(
        required=False,
        label="Izoh",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
