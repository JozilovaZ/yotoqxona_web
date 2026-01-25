from django import forms
from .models import Attendance
from apps.students.models import Student
from apps.buildings.models import Building, Floor


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status', 'check_in_time', 'check_out_time', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'check_in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class BulkAttendanceForm(forms.Form):
    building = forms.ModelChoiceField(
        queryset=Building.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'bulk_building'}),
        label='Bino'
    )
    floor = forms.ModelChoiceField(
        queryset=Floor.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'bulk_floor'}),
        label='Etaj'
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Sana'
    )
    default_status = forms.ChoiceField(
        choices=Attendance.Status.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Standart holat'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'building' in self.data:
            try:
                building_id = int(self.data.get('building'))
                self.fields['floor'].queryset = Floor.objects.filter(
                    building_id=building_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                pass