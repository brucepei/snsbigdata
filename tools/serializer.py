from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import Ap
import logging


logger = logging.getLogger(__name__)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class ApSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Ap
        fields = ('id', 'brand', 'ssid', 'type', 'password', 'owner', 'ping_aging', 'scan_aging', 'connect_aging', 'ip')

    def validate(self, data):
        logger.info("validate ap setting: {} at {}!".format(data, __name__))
        pass_len = len(data['password'])
        if data['type'] != 'OPEN' and pass_len < 8:
            raise serializers.ValidationError({'password': "Password of {} should be more than 8 characters!".format(data['type'])})
        elif data['type'] == 'OPEN' and pass_len != 0:
            raise serializers.ValidationError({'password': "Password of OPEN should be empty!"})
        return data


class APSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    brand = serializers.CharField(max_length=30, allow_blank=True)
    ssid = serializers.CharField(max_length=20)
    type = serializers.ChoiceField(choices=Ap.ENCRYPTION_TYPE, default='OPEN')
    password = serializers.CharField(max_length=20, allow_blank=True)
    owner = serializers.CharField(max_length=30)
    ip = serializers.IPAddressField(allow_null=True, allow_blank=True, required=False)
    ping_aging = serializers.FloatField(allow_null=True, required=False)
    scan_aging = serializers.FloatField(allow_null=True, required=False)
    connect_aging = serializers.FloatField(allow_null=True, required=False)

    def create(self, validated_data):
        return Ap.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.brand = validated_data.get('brand', instance.brand)
        instance.ssid = validated_data.get('ssid', instance.ssid)
        instance.type = validated_data.get('type', instance.type)
        instance.password = validated_data.get('password', instance.password)
        instance.owner = validated_data.get('owner', instance.owner)
        instance.ip = validated_data.get('ip', instance.ip)
        instance.save()
        return instance


