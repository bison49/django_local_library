import re

from django import forms
import datetime

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Book, BookInstance, Author, Genre, Language


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text="Enter a date between now and 4 weeks (default 3).")

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Check if a date is not in the past.
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        # Remember to always return the cleaned data.
        return data


class BookCreateForm(forms.ModelForm):

    class Meta:
        model = Book
        fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language', 'book_cover']
        labels = {
            'book_cover': "Upload an image to display for the book"
        }


class BookInstanceUpdateForm(forms.ModelForm):
    imprint = forms.CharField(disabled=True)

    class Meta:
        model = BookInstance
        fields = ['book', 'imprint', 'due_back', 'borrower', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'] = forms.ModelChoiceField(queryset=Book.objects.
                                                     filter(id=self.instance.book.id), disabled=True)


class BookFilterForm(forms.ModelForm):
    title = forms.CharField(required=False)
    author = forms.ModelChoiceField(queryset=Author.objects.all(), required=False)
    genre = forms.ModelMultipleChoiceField(queryset=Genre.objects.all(), widget=forms.CheckboxSelectMultiple,
                                           required=False)
    language = forms.ModelChoiceField(queryset=Language.objects.all(), required=False)

    class Meta:
        model = Book
        fields = ['title', 'author', 'language', 'genre']


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=150)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2',)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Email already exists"))
        return email

    #
    # def clean_password2(self):
    #     password1 = self.cleaned_data['password1']
    #     password2 = self.cleaned_data['password2']
    #
    #     if password1 and password2 and password1 != password2:
    #         raise ValidationError(_("Password don't match"))
    #     return password2
