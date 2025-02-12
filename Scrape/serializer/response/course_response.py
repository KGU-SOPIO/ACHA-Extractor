from rest_framework import serializers

from Scrape.serializer.response.activity_response import ActivityItemSerializer
from Scrape.serializer.response.notice_response import NoticeItemSerializer


class CourseItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    link = serializers.CharField()
    identifier = serializers.CharField()
    code = serializers.CharField()
    professor = serializers.CharField()
    noticeCode = serializers.CharField()
    notices = serializers.ListField(child=NoticeItemSerializer())
    activities = serializers.ListField(
        child=serializers.ListField(child=ActivityItemSerializer())
    )


class CourseResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=CourseItemSerializer())


class CourseNotExistResponse(serializers.Serializer):
    message = serializers.CharField()
