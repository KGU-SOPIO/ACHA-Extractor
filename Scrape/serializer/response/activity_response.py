from rest_framework import serializers


class ActivityItemSerializer(serializers.Serializer):
    available = serializers.BooleanField()
    title = serializers.CharField()
    link = serializers.CharField()
    code = serializers.CharField()
    type = serializers.CharField()
    startAt = serializers.CharField()
    deadline = serializers.CharField()
    lectureTime = serializers.CharField()
    gradingStatus = serializers.CharField()
    timeLeft = serializers.CharField()
    lastModified = serializers.CharField()
    description = serializers.CharField()
    submitStatus = serializers.CharField()
    attendance = serializers.BooleanField()


class ActivitiesSerializer(serializers.Serializer):
    week = serializers.IntegerField()
    activities = serializers.ListField(child=ActivityItemSerializer())


class ActivityResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=ActivitiesSerializer())
