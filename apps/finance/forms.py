from django import forms
from django.utils import timezone
from .models import Invoice, Payment
from apps.students.models import Student
from apps.buildings.models import Building, Floor


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['student', 'invoice_type', 'amount', 'due_date', 'period_start', 'period_end', 'description',
                  'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(is_active=True)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'invoice', 'amount', 'payment_method', 'payment_date', 'reference', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(is_active=True)
        self.fields['invoice'].required = False

        # Agar student tanlangan bo'lsa
        if 'student' in self.data:
            try:
                student_id = int(self.data.get('student'))
                self.fields['invoice'].queryset = Invoice.objects.filter(
                    student_id=student_id,
                    status__in=['pending', 'partial', 'overdue']
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['invoice'].queryset = Invoice.objects.filter(
                student=self.instance.student
            )
        else:
            self.fields['invoice'].queryset = Invoice.objects.none()


class BulkInvoiceForm(forms.Form):
    building = forms.ModelChoiceField(
        queryset=Building.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Bino (ixtiyoriy)'
    )
    floor = forms.ModelChoiceField(
        queryset=Floor.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Etaj (ixtiyoriy)'
    )
    invoice_type = forms.ChoiceField(
        choices=Invoice.InvoiceType.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Turi'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
        label='Summa'
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='To\'lov muddati'
    )
    period_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Davr boshi'
    )
    period_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Davr oxiri'
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label='Tavsif'
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