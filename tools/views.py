from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, serializers, status, permissions
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from datetime import datetime
from .serializer import UserSerializer, GroupSerializer, ApSerializer, APSerializer
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

class ApView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, *args, **kw):
        response = Response({}, status=status.HTTP_200_OK)
        logger.debug("get {}, response data: {}".format(request.data, response.data))
        return response

        
@csrf_exempt
def ap_list(request):
    if request.method == 'GET':
        aps = Ap.objects.all()
        for ap in aps:
            print("ap {} {} aging time={}".format(ap.id, ap.ssid, ap.aging_time()))
            ap.aging = ap.aging_time()
        serializer = APSerializer(aps, many=True)
        return JsonResponse(serializer.data, safe=False)
        
@csrf_exempt
def ap(request):
    if request.method == 'POST':
        logger.debug("post body={}".format(request.body))
        data = JSONParser().parse(request)
        method = data['method']
        data = data['data']
        try:
            if method == 'save':
                serializer = APSerializer(data=data)
                if serializer.is_valid():
                    logger.debug("post data={}".format(serializer.validated_data))
                    # data = serializer.validated_data
                    try:
                        ap = Ap.objects.get(id=data['id'])
                        logger.debug("Get ap {}".format(ap))
                        ap.brand = data['brand']
                        ap.ssid = data['ssid']
                        ap.password = data['password']
                        ap.type = data['type']
                        ap.owner = data['owner']
                        if 'aging' in data and data['aging']:
                            ap.update_aging()
                        ap.save()
                    except Exception as err:
                        logger.debug("Cannot get ap id={}, so create it: {}".format(data['id'], err))
                        if 'aging' in data:
                            del data['aging']
                        ap = Ap.objects.create(**data)
                    return JsonResponse(data, status=201)
            elif method == 'delete':
                ap = Ap.objects.get(**data)
                ap.delete()
                return JsonResponse({}, status=201)
        except Exception as err:
            logger.error("failed to save ap: {}".format(err))
            return JsonResponse({'error': err.message}, status=400)
