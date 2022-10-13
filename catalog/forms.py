from django import forms
import datetime
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
    genre = forms.ModelMultipleChoiceField(queryset=Genre.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)
    language = forms.ModelChoiceField(queryset=Language.objects.all(), required=False)

    class Meta:
        model = Book
        fields = ['title', 'author', 'language', 'genre']
