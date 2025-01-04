import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from Scrap.extractor import Extractor

from Scrap.serializer.activity import _ActivitySerializer

class ActivityView(GenericAPIView):
    serializer_class = _ActivitySerializer

    @extend_schema(
        summary="강좌 활동 추출",
        description="강좌의 활동 정보를 추출합니다.",
        request=_ActivitySerializer,
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="ActivityResponse",
                fields={
                    "activities": serializers.ListField(
                        child=serializers.ListField(
                            child=inline_serializer(
                                name="ActivityObject",
                                fields={
                                    "week": serializers.IntegerField(),
                                    "available": serializers.CharField(),
                                    "activityName": serializers.CharField(),
                                    "activityLink": serializers.CharField(),
                                    "activityCode": serializers.CharField(),
                                    "activityType": serializers.CharField(),
                                    "lectureDeadline": serializers.CharField(required=False),
                                    "lectureTime": serializers.CharField(required=False),
                                    "gradingStatus": serializers.CharField(required=False),
                                    "deadline": serializers.CharField(required=False),
                                    "timeLeft": serializers.CharField(required=False),
                                    "lastModified": serializers.CharField(required=False),
                                    "description": serializers.CharField(required=False),
                                    "submitStatus": serializers.CharField(required=False),
                                }
                            )
                        )
                    )
                }
            )
        }
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            courseCode = serializer.validated_data.get("code")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                activities = asyncio.run(extractor.getCourseActivites(courseCode=courseCode))

                return Response(
                    {
                        "activities": activities
                    },
                    status=status.HTTP_200_OK
                )
            
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)