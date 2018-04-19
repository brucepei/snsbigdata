from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, serializers, status, permissions
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from .serializer import UserSerializer, GroupSerializer, ApSerializer
from .models import Ap
import logging

logger = logging.getLogger(__name__)


# Create your views here.
def home_page(request):
    return render(request, 'tools/home.html')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ApViewSet(viewsets.ModelViewSet):
    queryset = Ap.objects.all().order_by('ssid')
    serializer_class = ApSerializer
    password = serializers.CharField()


class ApTypesView(APIView):
    types = Ap.ENCRYPTION_TYPE
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kw):
        response = Response(self.types, status=status.HTTP_200_OK)
        logger.debug("get {}, response data: {}".format(request.path, response.data))
        return response

@csrf_exempt
def ap_list(request):
    if request.method == 'GET':
        aps = Ap.objects.all()
        serializer = ApSerializer(aps, many=True)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == 'POST':
        logger.debug("post body={}".format(request.body))
        data = JSONParser().parse(request)
        serializer = ApSerializer(data=data)
        if serializer.is_valid():
            logger.debug("post data={}".format(serializer.validated_data))
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def ap(request, pk):
    try:
        ap = Ap.objects.get(pk)
    except Ap.DoesNotExist:
        return HttpResponse(status=404)
    if request.method == 'GET':
        ap = ApSerializer(ap)