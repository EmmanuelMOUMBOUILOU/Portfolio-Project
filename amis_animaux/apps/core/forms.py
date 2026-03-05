from django import forms
from apps.users.models import Profile
from apps.animals.models import Animal


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("age", "location", "bio", "avatar")
        widgets = {
            "age": forms.NumberInput(attrs={"placeholder": "ex: 29"}),
            "location": forms.TextInput(attrs={"placeholder": "ex: Paris"}),
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Parle un peu de toi…"}),
        }


class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ("name", "species", "age")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "ex: Rocky"}),
            "species": forms.TextInput(attrs={"placeholder": "ex: Dog"}),
            "age": forms.NumberInput(attrs={"placeholder": "ex: 3"}),
        }
