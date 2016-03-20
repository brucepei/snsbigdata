from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from tbd.models import Project


# Create your views here.
def home_page(request):
    return render(request, 'tbd/home.html')

def project_page(request):
    if request.method == 'POST':
        prj_name = request.POST['name']
        prj_owner = request.POST['owner']
        prj_create = request.POST.get('create', None)
        if prj_create:
            prj_create = timezone.make_aware(prj_create, timezone.get_current_timezone())
            Project.objects.create(name=prj_name, owner=prj_owner, create=prj_create)
        else:
            Project.objects.create(name=prj_name, owner=prj_owner)
        return redirect('tbd_project')
    return render(request, 'tbd/project.html', {'projects': Project.objects.all()})