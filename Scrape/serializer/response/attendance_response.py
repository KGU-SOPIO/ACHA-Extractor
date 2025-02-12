from rest_framework import serializers


class AttendanceItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    attendance = serializers.BooleanField()


class AttendancesSerializer(serializers.Serializer):
    week = serializers.IntegerField()
    attendances = serializers.ListField(child=AttendanceItemSerializer())


class AttendancesResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=AttendancesSerializer())
