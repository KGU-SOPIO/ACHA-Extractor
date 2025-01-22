from rest_framework import serializers

class AssignmentItemSerializer(serializers.Serializer):
    gradingStatus = serializers.CharField()
    deadline = serializers.CharField()
    timeLeft = serializers.CharField()
    lastModified = serializers.CharField()
    description = serializers.CharField()
    submitStatus = serializers.CharField()

class AssignmentResponseSerializer(serializers.Serializer):
    data = AssignmentItemSerializer()