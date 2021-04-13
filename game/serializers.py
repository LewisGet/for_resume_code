from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext_lazy as _
from .models import *


class LoginSerializer(serializers.Serializer):
    token = serializers.CharField(
        label=_("token"),
        write_only=True
    )

    class Meta:
        model = Token
        fields = {'id', 'user', 'token'}

    def validate(self, attrs):
        token = attrs.get('token')

        if token:
            user = Token.objects.get(key=token).user

            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "Token".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
