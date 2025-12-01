from django import forms
from .models import User

class UserRegistrationForm(forms.ModelForm):
    """Form for user registration (patients and doctors)"""
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create password'
        }),
        label='Password',
        required=True,
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        label='Confirm Password',
        required=True
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+63 912 345 6789'
            }),
            'role': forms.HiddenInput(),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Passwords do not match.')
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
        
        return password2
    
    def clean_role(self):
        role = self.cleaned_data.get('role')
        if not role or role not in ['patient', 'doctor']:
            raise forms.ValidationError('Please select a valid role.')
        return role
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """Form for user login"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email'
        }),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        label='Password'
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile with body metrics"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'phone_number', 
            'address', 
            'date_of_birth',
            'gender',
            'height',
            'weight',
            'profile_picture'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number (e.g., +639123456789)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your complete address',
                'rows': 3
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'YYYY-MM-DD'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control',
            }, choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')]),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter height in cm (e.g., 170)',
                'step': '0.1',
                'min': '0'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter weight in kg (e.g., 65.5)',
                'step': '0.1',
                'min': '0'
            }),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'phone_number': 'Phone Number',
            'address': 'Address',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'height': 'Height (cm)',
            'weight': 'Weight (kg)',
            'profile_picture': 'Profile Photo',
        }
        help_texts = {
            'height': 'Enter your height in centimeters',
            'weight': 'Enter your weight in kilograms',
            'date_of_birth': 'Required for age calculation and BMI tracking',
        }

    def clean_height(self):
        """Validate height is within reasonable range"""
        height = self.cleaned_data.get('height')
        if height is not None:
            if height < 50 or height > 300:
                raise forms.ValidationError('Height must be between 50 and 300 cm')
        return height

    def clean_weight(self):
        """Validate weight is within reasonable range"""
        weight = self.cleaned_data.get('weight')
        if weight is not None:
            if weight < 20 or weight > 500:
                raise forms.ValidationError('Weight must be between 20 and 500 kg')
        return weight