from django import forms
from django.utils import timezone
from .models import Invoice, Payment
from students.models import Student
from buildings.models import Building, Floor


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
        building_id = kwargs.pop('building_id', None)
        super().__init__(*args, **kwargs)
        qs = Student.objects.filter(is_active=True)
        if building_id:
            qs = qs.filter(room__floor__building_id=building_id)
        self.fields['student'].queryset = qs


class PaymentForm(forms.ModelForm):
    # Oylar ro'yxati
    MONTH_CHOICES = [
        ('', '--- Oyni tanlang ---'),
        ('Yanvar', 'Yanvar'), ('Fevral', 'Fevral'), ('Mart', 'Mart'),
        ('Aprel', 'Aprel'), ('May', 'May'), ('Iyun', 'Iyun'),
        ('Iyul', 'Iyul'), ('Avgust', 'Avgust'), ('Sentabr', 'Sentabr'),
        ('Oktabr', 'Oktabr'), ('Noyabr', 'Noyabr'), ('Dekabr', 'Dekabr'),
    ]

    # Referens maydonini oylar tanlashga o'zgartiramiz
    reference = forms.ChoiceField(
        choices=MONTH_CHOICES,
        label="Qaysi oy uchun",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Payment
        fields = ['student', 'invoice', 'amount', 'payment_method', 'payment_date', 'reference', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'value': timezone.now().strftime('%Y-%m-%dT%H:%M')  # Hozirgi vaqtni avtomatik qo'yish
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        building_id = kwargs.pop('building_id', None)
        super().__init__(*args, **kwargs)
        qs = Student.objects.filter(is_active=True)
        if building_id:
            qs = qs.filter(room__floor__building_id=building_id)
        self.fields['student'].queryset = qs
        self.fields['invoice'].required = False

        # Hozirgi oyni avtomatik tanlab qo'yish
        current_month = ["", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
                         "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"][timezone.now().month]
        self.fields['reference'].initial = current_month

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
        building_id = kwargs.pop('building_id', None)
        super().__init__(*args, **kwargs)
        if building_id:
            self.fields['building'].queryset = Building.objects.filter(id=building_id)
            self.fields['building'].initial = building_id
            self.fields['floor'].queryset = Floor.objects.filter(building_id=building_id, is_active=True)
        if 'building' in self.data:
            try:
                bid = int(self.data.get('building'))
                self.fields['floor'].queryset = Floor.objects.filter(
                    building_id=bid,
                    is_active=True
                )
            except (ValueError, TypeError):
                pass