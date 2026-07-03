from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ContactInquiry, Order, DistributorInquiry


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'placeholder': 'Password', 'class': 'form-control'}
        )
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}
        )
        # Remove verbose help text
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'product', 'quantity', 'message']
        widgets = {
            'name':     forms.TextInput(attrs={'placeholder': 'Your Name', 'class': 'form-control'}),
            'email':    forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-control'}),
            'phone':    forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-control'}),
            'product':  forms.TextInput(attrs={'placeholder': 'DTF Ink / Roll', 'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'placeholder': 'Qty', 'class': 'form-control'}),
            'message':  forms.Textarea(attrs={
                'placeholder': 'Tell us about your requirement',
                'class': 'form-control',
                'rows': 4,
            }),
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'email', 'phone', 'address', 'notes']
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-control'}),
            'email':   forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
            'phone':   forms.TextInput(attrs={'placeholder': 'Phone', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'placeholder': 'Delivery Address',
                'class': 'form-control',
                'rows': 3,
            }),
            'notes': forms.Textarea(attrs={
                'placeholder': 'Any special instructions (optional)',
                'class': 'form-control',
                'rows': 2,
            }),
        }


class DistributorForm(forms.ModelForm):
    """Distributor application form (Name, City, Phone, Business Type)."""
    class Meta:
        model = DistributorInquiry
        fields = ['name', 'city', 'phone', 'business_type']
        widgets = {
            'name':  forms.TextInput(attrs={
                'placeholder': 'Your full name', 'class': 'form-control', 'id': 'name'
            }),
            'city':  forms.TextInput(attrs={
                'placeholder': 'Your city', 'class': 'form-control', 'id': 'city'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Mobile number', 'class': 'form-control',
                'id': 'phone', 'type': 'tel', 'inputmode': 'tel'
            }),
            'business_type': forms.Select(attrs={'class': 'form-control', 'id': 'business_type'}),
        }
