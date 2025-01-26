from rest_framework import serializers

class ActivityItemSerializer(serializers.Serializer):
    available = serializers.BooleanField()
    title = serializers.CharField()
    link = serializers.CharField()
    code = serializers.CharField()
    type = serializers.CharField()
    lectureDeadline = serializers.CharField()
    lectureTime = serializers.CharField()
    gradingStatus = serializers.CharField()
    deadline = serializers.CharField()
    timeLeft = serializers.CharField()
    lastModified = serializers.CharField()
    description = serializers.CharField()
    submitStatus = serializers.CharField()
    attendance = serializers.BooleanField()

class ActivityResponseSerializer(serializers.Serializer):
    data = serializers.ListField(
        child = serializers.ListField(
            child = ActivityItemSerializer()
        )
    )