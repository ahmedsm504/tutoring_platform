# accounts/forms.py
from django import forms
from .models import TrialBooking


class TrialBookingForm(forms.ModelForm):
    """
    نموذج حجز الحصة التجريبية
    """
    class Meta:
        model = TrialBooking
        fields = ['name', 'country', 'gender', 'phone', 'email', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الكامل',
                'required': True
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الدولة',
                'required': True
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+20 123 456 789',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com (اختياري)',
                'required': False
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أي ملاحظات أو استفسارات (اختياري)',
                'rows': 4,
                'required': False
            }),
        }
        labels = {
            'name': 'الاسم',
            'country': 'الدولة',
            'gender': 'الجنس',
            'phone': 'رقم الهاتف',
            'email': 'البريد الإلكتروني',
            'notes': 'ملاحظات',
        }