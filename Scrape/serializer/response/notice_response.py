from rest_framework import serializers


class FileItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    link = serializers.CharField()


class NoticeItemSerializer(serializers.Serializer):
    link = serializers.CharField()
    content = serializers.CharField()
    index = serializers.CharField()
    title = serializers.CharField()
    professor = serializers.CharField()
    date = serializers.DateField()
    files = serializers.ListField(child=FileItemSerializer())


class NoticeResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=NoticeItemSerializer())
