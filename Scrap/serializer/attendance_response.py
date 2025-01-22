from rest_framework import serializers

class AttendanceItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    attendance = serializers.BooleanField()

class AttendancesResponseSerializer(serializers.Serializer):
    data = serializers.ListField(
        child = AttendanceItemSerializer()
    )
