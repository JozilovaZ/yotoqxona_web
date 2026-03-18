from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Telefon raqam yoki login',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parol'
        })
    )


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class PhoneRegistrationForm(forms.Form):
    """Forma bilan ro'yxatdan o'tish: ism, familiya, username, parol, telefon"""
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ismingiz',
            'autofocus': True
        }),
        label='Ism'
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Familiyangiz'
        }),
        label='Familiya'
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Login (masalan: ali2024)'
        }),
        label='Username'
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+998 90 123 45 67'
        }),
        label='Telefon raqam'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parol kiriting'
        }),
        label='Parol'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parolni qayta kiriting'
        }),
        label='Parol (qayta)'
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Bu username allaqachon band")
        return username

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip().replace(' ', '').replace('-', '')
        if not phone.startswith('+998') and not phone.startswith('998'):
            if phone.startswith('9') and len(phone) == 9:
                phone = '+998' + phone
            elif phone.startswith('0'):
                phone = '+998' + phone[1:]
            else:
                raise forms.ValidationError("Telefon raqam noto'g'ri formatda")
        if not phone.startswith('+'):
            phone = '+' + phone
        digits = phone.replace('+', '')
        if not digits.isdigit() or len(digits) != 12:
            raise forms.ValidationError("Telefon raqam 12 ta raqamdan iborat bo'lishi kerak (+998XXXXXXXXX)")
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan")
        return phone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Parollar bir xil emas")
        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            phone=self.cleaned_data['phone'],
            role=User.Role.APPLICANT,
        )
        return user


# Legacy form - keep for backwards compatibility
class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiya'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon raqam'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parol'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parolni tasdiqlang'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.APPLICANT
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
