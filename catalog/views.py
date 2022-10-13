import datetime

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.views.generic import DeleteView, UpdateView, CreateView

from catalog.forms import BookFilterForm, BookInstanceUpdateForm, RenewBookForm
from catalog.models import Author, Book, BookInstance, Genre


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_genres = Genre.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # Available books with "les" in the title
    num_books_contains = Book.objects.filter(title__icontains="les", author__last_name__contains='zola').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_books_contains': num_books_contains,
        'num_visits': num_visits,
    }
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


@require_http_methods(["GET", "POST"])
@login_required
def do_logout(request):
    assert isinstance(request, HttpRequest)

    messages.add_message(request, messages.INFO, '{0} logged out.'.format(request.user))
    logout(request)
    return redirect('index')


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    model = Author


class AuthorCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Author
    permission_required = 'catalog.can_change_author'
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}

    # Ajout d'un message sur une class based view
    def form_valid(self, form):
        messages.add_message(self.request, messages.INFO, 'Nouvel auteur ajouté(e)')
        return super().form_valid(form)


class AuthorUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Author
    permission_required = 'catalog.can_change_author'
    fields = '__all__'  # Not recommended (potential security issue if more fields added)

    def form_valid(self, form):
        messages.add_message(self.request, messages.INFO, "L'auteur({0}) a été modifié".format(self.object))
        return super().form_valid(form)


class AuthorDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Author
    permission_required = 'catalog.can_change_author'
    success_url = reverse_lazy('authors')


class BookListView(generic.ListView):
    model = Book
    paginate_by = 30

    def __init__(self):
        super().__init__()
        self.object_list = Book.objects.all()

    def get(self, request, *args, **kwargs):
        form = BookFilterForm(self.request.GET or None)
        if form.is_valid():
            query = Book.objects.all()
            if form["genre"].value().__len__() != 0 and not None:
                query = query.filter(genre__in=form.cleaned_data['genre'])
            if form.cleaned_data['author'] is not None:
                query = Book.objects.filter(author=form.cleaned_data['author'])
            if form.cleaned_data['title'] is not None:
                query = query.filter(title__icontains=form.cleaned_data['title'])
            if form.cleaned_data['language'] is not None:
                query = query.filter(language=form.cleaned_data['language'])
            self.object_list = query
        return self.render_to_response(self.get_context_data(form=form))


class BookDetailView(generic.DetailView):
    model = Book


class BookCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Book
    permission_required = 'catalog.can_change_author'
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    success_url = reverse_lazy('bookinstance-create')

    def get_success_url(self):
        return reverse_lazy('bookinstance-create', args=[self.object.id])


class BookUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Book
    permission_required = 'catalog.can_change_author'
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']


class BookDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    permission_required = 'catalog.can_change_author'
    success_url = reverse_lazy('books')


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class BooksOnLoan(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/list_books_on loan.html'
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


class BookInstanceUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = BookInstance
    permission_required = 'catalog.can_change_author'
    form_class = BookInstanceUpdateForm
    success_url = reverse_lazy('books')


class BookInstanceDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = BookInstance
    permission_required = 'catalog.can_change_author'
    success_url = reverse_lazy('books')


class BookInstanceCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BookInstance
    fields = ['book', 'imprint', 'due_back', 'borrower', 'status']
    permission_required = 'catalog.can_change_author'
    success_url = reverse_lazy('book-detail')

    def get_initial(self):
        initial = super().get_initial()
        initial['book'] = Book.objects.get(pk=self.kwargs['id'])
        return initial.copy()

    def get_success_url(self):
        return reverse_lazy('book-detail', args=[self.kwargs['id']])

    # def get_context_data(self, **kwargs):
    #     # Call the base implementation first to get a context
    #     context = super().get_context_data(**kwargs)
    #     context['bookid'] = Book.objects.get(pk=self.kwargs['id'])
    #     return context
