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
            raise serializers.ValidationError(
                {'password': "Password of {} should be more than 8 characters!".format(data['type'])})
        elif data['type'] == 'OPEN' and pass_len != 0:
            raise serializers.ValidationError({'password': "Password of OPEN should be empty!"})
        return data


class AgingField(serializers.DurationField):
    def to_representation(self, duration):
        days = duration.days
        seconds = duration.seconds

        minutes = seconds // 60
        seconds = seconds % 60

        hours = minutes // 60
        minutes = minutes % 60

        string = '{:02d}h:{:02d}m:{:02d}s'.format(hours, minutes, seconds)
        if days:
            string = '{} days '.format(days) + string
        return string


class APSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    ping_aging = AgingField(read_only=True, source='ping_aging_delta')
    scan_aging = AgingField(read_only=True, source='scan_aging_delta')
    connect_aging = AgingField(read_only=True, source='connect_aging_delta')

    class Meta:
        model = Ap
        fields = ('id', 'brand', 'ssid', 'type', 'password', 'owner', 'ip', 'ping_aging', 'scan_aging', 'connect_aging')

