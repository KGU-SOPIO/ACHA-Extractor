from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    name = serializers.CharField()
    college = serializers.CharField()
    department = serializers.CharField()
    major = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    verification = serializers.BooleanField()
    userData = UserSerializer(allow_null=True)
    message = serializers.CharField()
