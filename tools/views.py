from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, serializers, status, permissions, generics
from django.urls import reverse, resolve
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.decorators import action
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


class ApListView(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)
    queryset = Ap.objects.all()
    serializer_class = APSerializer

    @action(methods=['get'], detail=False)
    def list_type(self, request, *args, **kwargs):
        response = Response(Ap.ENCRYPTION_TYPE, status=status.HTTP_200_OK)
        logger.debug("get {}, response data: {}".format(request.path, response.data))
        return response

    def list(self, request, *args, **kws):
        all_aps = self.get_queryset()
        serialized_aps = APSerializer(all_aps, many=True)
        response = Response(serialized_aps.data, status=status.HTTP_200_OK)
        logger.debug("List APs, response data: {}".format(response.data))
        return response

    def create(self, request, *args, **kws):
        logger.debug("Create AP with data: {}".format(request.data))
        return self.get(request, *args, **kws)


@csrf_exempt
def ap_list(request):
    if request.method in ('GET', 'POST'):
        aps = Ap.objects.all()
        for ap in aps:
            logger.debug("ap {} {} ping_aging={}".format(ap.id, ap.ssid, ap.aging_time(ap.ping_aging)))
            ap.ping_aging = ap.aging_time(ap.ping_aging)
            ap.scan_aging = ap.aging_time(ap.scan_aging)
            ap.connect_aging = ap.aging_time(ap.connect_aging)
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
                    logger.debug("save data={}".format(data))
                    # data = serializer.validated_data
                    if data['id'] > 0:
                        ap = Ap.objects.get(id=data['id'])
                        logger.debug("Get ap {}={}".format(data['id'], ap))
                        ap.brand = data['brand']
                        ap.ssid = data['ssid']
                        ap.password = data['password']
                        ap.type = data['type']
                        ap.owner = data['owner']
                        ap.ip = data['ip']
                        if 'ping_aging' in data and data['ping_aging']:
                            ap.update_aging('ping')
                        if 'scan_aging' in data and data['scan_aging']:
                            ap.update_aging('scan')
                        if 'connect_aging' in data and data['connect_aging']:
                            ap.update_aging('connect')
                        ap.save()
                    else:
                        logger.debug("No ap id, so create it!")
                        del data['id']
                        if 'aging' in data:
                            del data['aging']
                        ap = Ap.objects.create(**data)
                        data = ApSerializer(ap).data
                    return JsonResponse(data, status=201)
                else:
                    return JsonResponse({'invalid_data': serializer.errors}, status=400)
            if method == 'refresh':
                logger.debug("refresh data={}".format(data))
                if data['ssid']:
                    ap = Ap.objects.get(ssid=data['ssid'])
                    logger.debug("Get ap {}={}".format(data['ssid'], ap))
                    if 'ping' in data and data['ping']:
                        ap.update_aging('ping')
                    if 'scan' in data and data['scan']:
                        ap.update_aging('scan')
                    if 'connect' in data and data['connect']:
                        ap.update_aging('connect')
                    ap.save()
                    data = ApSerializer(ap).data
                return JsonResponse(data, status=201)
            elif method == 'delete':
                ap = Ap.objects.get(**data)
                ap.delete()
                return JsonResponse({}, status=201)
        except Exception as err:
            logger.error("failed to edit ap: {}".format(err))
            return JsonResponse({'error': err.message}, status=400)
