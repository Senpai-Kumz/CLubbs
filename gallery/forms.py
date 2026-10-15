
from django import forms
from django.contrib.auth.models import User
from .models import Profile


class UserRegisterForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        confirmation = self.cleaned_data.get("password_confirm")

        if password and confirmation and password != confirmation:
            raise forms.ValidationError("Passwords do not match.")

        return confirmation

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar", "bio", "brand_color"]
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Tell us about yourself..."
                }
            ),
            "brand_color": forms.TextInput(
                attrs={"type": "color"}
            ),
        }