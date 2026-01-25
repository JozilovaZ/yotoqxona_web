from django import forms
from .models import Student
from apps.buildings.models import Building, Floor, Room


class StudentForm(forms.ModelForm):
    building = forms.ModelChoiceField(
        queryset=Building.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_building'}),
        label='Bino'
    )
    floor = forms.ModelChoiceField(
        queryset=Floor.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_floor'}),
        label='Etaj'
    )

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'middle_name', 'gender', 'birth_date', 'photo',
            'phone', 'email', 'emergency_contact', 'emergency_phone',
            'student_id', 'faculty', 'group', 'course',
            'room', 'check_in_date', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'room': forms.Select(attrs={'class': 'form-select', 'id': 'id_room'}),
            'check_in_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agar instance mavjud bo'lsa (tahrirlash)
        if self.instance and self.instance.pk and self.instance.room:
            self.fields['building'].initial = self.instance.room.floor.building
            self.fields['floor'].queryset = Floor.objects.filter(
                building=self.instance.room.floor.building,
                is_active=True
            )
            self.fields['floor'].initial = self.instance.room.floor
            self.fields['room'].queryset = Room.objects.filter(
                floor=self.instance.room.floor,
                is_active=True
            )
        else:
            self.fields['room'].queryset = Room.objects.none()


class StudentTransferForm(forms.Form):
    building = forms.ModelChoiceField(
        queryset=Building.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'transfer_building'}),
        label='Bino'
    )
    floor = forms.ModelChoiceField(
        queryset=Floor.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'transfer_floor'}),
        label='Etaj'
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'transfer_room'}),
        label='Xona'
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label='Sabab'
    )

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student

        if 'building' in self.data:
            try:
                building_id = int(self.data.get('building'))
                self.fields['floor'].queryset = Floor.objects.filter(
                    building_id=building_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                pass

        if 'floor' in self.data:
            try:
                floor_id = int(self.data.get('floor'))
                self.fields['room'].queryset = Room.objects.filter(
                    floor_id=floor_id,
                    is_active=True
                ).exclude(status='full')
            except (ValueError, TypeError):
                pass

    def clean_room(self):
        room = self.cleaned_data.get('room')
        if room and room.available_beds <= 0:
            raise forms.ValidationError('Bu xonada bo\'sh joy yo\'q')
        if self.student and room == self.student.room:
            raise forms.ValidationError('Talaba allaqachon shu xonada')
        return room