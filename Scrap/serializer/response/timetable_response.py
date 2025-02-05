from rest_framework import serializers

class TimetableItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    identifier = serializers.CharField()
    professor = serializers.CharField()
    lectureRoom = serializers.CharField()
    day = serializers.CharField()
    classTime = serializers.IntegerField()
    startAt = serializers.IntegerField()
    endAt = serializers.IntegerField()

class TimetableResponseSerializer(serializers.Serializer):
    data = serializers.ListField(
        child = TimetableItemSerializer()
    )