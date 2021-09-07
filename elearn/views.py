from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.views import generic
# from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponse, Http404
# from .models import Customer, Profile
from .forms import  LearnerSignUpForm, InstructorSignUpForm, \
    LearnerInterestsForm, LearnerCourse, UserForm, ProfileForm, PostForm
from django.http import HttpResponseRedirect, HttpResponse
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.core import serializers
from django.conf import settings
import os
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import auth
from datetime import datetime, date
from django.core.exceptions import ValidationError
from . import models
import operator
import itertools
from django.db.models import Avg, Count, Sum
from django.forms import inlineformset_factory
from .models import Profile, Learner, User, Course, Announcement
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.forms import (AuthenticationForm, UserCreationForm,
                                       PasswordChangeForm)

from django.contrib.auth import update_session_auth_hash

from bootstrap_modal_forms.generic import (
    BSModalLoginView,
    BSModalFormView,
    BSModalCreateView,
    BSModalUpdateView,
    BSModalReadView,
    BSModalDeleteView
)
# Create your views here.


# Shared Views

def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


def services(request):
    return render(request, 'service.html')


def contact(request):
    return render(request, 'contact.html')


def login_form(request):
    return render(request, 'login.html')


def logoutView(request):
    logout(request)
    return redirect('home')


def loginView(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            if user.is_admin or user.is_superuser:
                return redirect('dashboard')
            elif user.is_instructor:
                return redirect('instructor')
            elif user.is_learner:
                return redirect('learner')
            else:
                return redirect('login_form')
        else:
            messages.info(request, "Invalid Username or Password")
            return redirect('login_form')


# Admin Views
def dashboard(request):
    learner = User.objects.filter(is_learner=True).count()
    instructor = User.objects.filter(is_instructor=True).count()
    course = Course.objects.all().count()
    users = User.objects.all().count()
    context = {'learner': learner, 'course': course, 'instructor': instructor, 'users': users}

    return render(request, 'dashboard/admin/home.html', context)


class InstructorSignUpView(CreateView):
    model = User
    form_class = InstructorSignUpForm
    template_name = 'dashboard/admin/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'instructor'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Instructor Was Added Successfully')
        return redirect('isign')


class AdminLearner(CreateView):
    model = User
    form_class = LearnerSignUpForm
    template_name = 'dashboard/admin/learner_signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'learner'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Learner Was Added Successfully')
        return redirect('addlearner')


def course(request):
    if request.method == 'POST':
        name = request.POST['name']
        color = request.POST['color']

        a = Course(name=name, color=color)
        a.save()
        messages.success(request, 'New Course Was Registed Successfully')
        return redirect('course')
    else:
        return render(request, 'dashboard/admin/course.html')


class AdminCreatePost(CreateView):
    model = Announcement
    form_class = PostForm
    template_name = 'dashboard/admin/post_form.html'
    success_url = reverse_lazy('alpost')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)


class AdminListTise(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'dashboard/admin/tise_list.html'

    def get_queryset(self):
        return Announcement.objects.filter(posted_at__lt=timezone.now()).order_by('posted_at')


class ListAllTise(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'dashboard/admin/list_tises.html'
    context_object_name = 'tises'
    paginated_by = 10

    def get_queryset(self):
        return Announcement.objects.order_by('-id')


class ADeletePost(SuccessMessageMixin, DeleteView):
    model = Announcement
    template_name = 'dashboard/admin/confirm_delete.html'
    success_url = reverse_lazy('alistalltise')
    success_message = "Announcement Was Deleted Successfully"


class ListUserView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'dashboard/admin/list_users.html'
    context_object_name = 'users'
    paginated_by = 10

    def get_queryset(self):
        return User.objects.order_by('-id')


class ADeleteuser(SuccessMessageMixin, DeleteView):
    model = User
    template_name = 'dashboard/admin/confirm_delete2.html'
    success_url = reverse_lazy('aluser')
    success_message = "User Was Deleted Successfully"


def create_user_form(request):
    return render(request, 'dashboard/admin/add_user.html')


def create_user(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password = make_password(password)

        a = User(first_name=first_name, last_name=last_name, username=username, password=password, email=email,
                 is_admin=True)
        a.save()
        messages.success(request, 'Admin Was Created Successfully')
        return redirect('aluser')
    else:
        messages.error(request, 'Admin Was Not Created Successfully')
        return redirect('create_user_form')


def acreate_profile(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        birth_date = request.POST['birth_date']
        bio = request.POST['bio']
        email = request.POST['email']
        phonenumber = request.POST['phonenumber']
        city = request.POST['city']
        country = request.POST['country']
        avatar = request.FILES['avatar']
        # hobby = request.POST['hobby']
        current_user = request.user
        user_id = current_user.id
        print(user_id)

        Profile.objects.filter(id=user_id).create(user_id=user_id, email=email, phonenumber=phonenumber, first_name=first_name,
                                                  last_name=last_name, bio=bio, birth_date=birth_date, avatar=avatar,
                                                  city=city, country=country)
        messages.success(request, 'Your Profile Was Created Successfully')
        return redirect('auser_profile')
    else:
        current_user = request.user
        user_id = current_user.id
        users = Profile.objects.filter(user_id=user_id)
        users = {'users': users}
        return render(request, 'dashboard/admin/create_profile.html', users)


def auser_profile(request):
    current_user = request.user
    user_id = current_user.id
    users = Profile.objects.filter(user_id=user_id)
    users = {'users': users}
    return render(request, 'dashboard/admin/user_profile.html', users)


# Instructor Views
def home_instructor(request):
    learner = User.objects.filter(is_learner=True).count()
    instructor = User.objects.filter(is_instructor=True).count()
    course = Course.objects.all().count()
    users = User.objects.all().count()
    context = {'learner': learner, 'course': course, 'instructor': instructor, 'users': users}

    return render(request, 'dashboard/instructor/home.html', context)


class CreatePost(CreateView):
    form_class = PostForm
    model = Announcement
    template_name = 'dashboard/instructor/post_form.html'
    success_url = reverse_lazy('llchat')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)


class TiseList(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'dashboard/instructor/tise_list.html'

    def get_queryset(self):
        return Announcement.objects.filter(posted_at__lt=timezone.now()).order_by('posted_at')


def user_profile(request):
    current_user = request.user
    user_id = current_user.id
    print(user_id)
    users = Profile.objects.filter(user_id=user_id)
    users = {'users': users}
    return render(request, 'dashboard/instructor/user_profile.html', users)


def create_profile(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        phonenumber = request.POST['phonenumber']
        bio = request.POST['bio']
        city = request.POST['city']
        country = request.POST['country']
        birth_date = request.POST['birth_date']
        avatar = request.FILES['avatar']
        current_user = request.user
        user_id = current_user.id
        print(user_id)

        Profile.objects.filter(id=user_id).create(user_id=user_id, first_name=first_name, last_name=last_name,
                                                  phonenumber=phonenumber, bio=bio, city=city, country=country,
                                                  birth_date=birth_date, avatar=avatar)
        messages.success(request, 'Profile was created successfully')
        return redirect('user_profile')
    else:
        current_user = request.user
        user_id = current_user.id
        print(user_id)
        users = Profile.objects.filter(user_id=user_id)
        users = {'users': users}
        return render(request, 'dashboard/instructor/create_profile.html', users)


# Learner Views
def home_learner(request):
    learner = User.objects.filter(is_learner=True).count()
    instructor = User.objects.filter(is_instructor=True).count()
    course = Course.objects.all().count()
    users = User.objects.all().count()

    context = {'learner': learner, 'course': course, 'instructor': instructor, 'users': users}

    return render(request, 'dashboard/learner/home.html', context)


class LearnerSignUpView(CreateView):
    model = User
    form_class = LearnerSignUpForm
    template_name = 'signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'learner'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        # return redirect('learner')
        return redirect('home')


class ITiseList(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'dashboard/learner/tise_list.html'

    def get_queryset(self):
        return Announcement.objects.filter(posted_at__lt=timezone.now()).order_by('posted_at')


def luser_profile(request):
    current_user = request.user
    user_id = current_user.id
    print(user_id)
    users = Profile.objects.filter(user_id=user_id)
    users = {'users': users}
    return render(request, 'dashboard/learner/user_profile.html', users)


def lcreate_profile(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        phonenumber = request.POST['phonenumber']
        bio = request.POST['bio']
        city = request.POST['city']
        country = request.POST['country']
        birth_date = request.POST['birth_date']
        avatar = request.FILES['avatar']
        current_user = request.user
        user_id = current_user.id
        print(user_id)

        Profile.objects.filter(id=user_id).create(user_id=user_id, first_name=first_name, last_name=last_name,
                                                  phonenumber=phonenumber, bio=bio, city=city, country=country,
                                                  birth_date=birth_date, avatar=avatar)
        messages.success(request, 'Profile was created successfully')
        return redirect('luser_profile')
    else:
        current_user = request.user
        user_id = current_user.id
        print(user_id)
        users = Profile.objects.filter(user_id=user_id)
        users = {'users': users}
        return render(request, 'dashboard/learner/create_profile.html', users)


class LearnerInterestsView(UpdateView):
    model = Learner
    form_class = LearnerInterestsForm
    template_name = 'dashboard/learner/interests_form.html'
    success_url = reverse_lazy('interests')

    def get_object(self):
        return self.request.user.learner

    def form_valid(self, form):
        messages.success(self.request, 'Course Was Updated Successfully')
        return super().form_valid(form)
