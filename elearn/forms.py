from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError
from django import forms

from elearn.models import (Learner, Course, User, Announcement)


class PostForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('content',)


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput())
    confirm_email = forms.EmailField(widget=forms.EmailInput())

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',

        ]

    def clean(self):
        cleaned_data = super(ProfileForm, self).clean()
        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")

        if email != confirm_email:
            raise forms.ValidationError(
                "Emails must match!"
            )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class InstructorSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def __init__(self, *args, **kwargs):
        super(InstructorSignUpForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_instructor = True
        if commit:
            user.save()
        return user


class LearnerSignUpForm(UserCreationForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User

    def __init__(self, *args, **kwargs):
        super(LearnerSignUpForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_learner = True
        user.save()
        learner = Learner.objects.create(user=user)
        learner.interests.add(*self.cleaned_data.get('interests'))
        return user


class LearnerInterestsForm(forms.ModelForm):
    class Meta:
        model = Learner
        fields = ('interests',)
        widgets = {
            'interests': forms.CheckboxSelectMultiple
        }


class LearnerCourse(forms.ModelForm):
    class Meta:
        model = Learner
        fields = ('interests',)
        widgets = {
            'interests': forms.CheckboxSelectMultiple
        }

    @transaction.atomic
    def save(self):
        learner = Learner()
        learner.interests.add(*self.cleaned_data.get('interests'))
        return learner._id
