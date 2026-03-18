from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'participant', 'is_active', 'is_staff'
        ]


class UserUpdateForm(forms.ModelForm):
    new_password = forms.CharField(
        label='Nova senha (opcional)',
        required=False,
        widget=forms.PasswordInput(render_value=False)
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'participant', 'is_active', 'is_staff'
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user
