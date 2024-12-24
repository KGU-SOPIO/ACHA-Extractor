import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from Scrap.extractor.extractor import Extractor

from Scrap.serializer.course import _CourseSerializer

class CourseView(GenericAPIView):
    serializer_class = _CourseSerializer

    @extend_schema(
        summary="강좌 추출",
        description="모든 강좌의 정보를 추출합니다.",
        request=_CourseSerializer,
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="CourseResponse",
                fields={
                    "courses": serializers.ListField(
                        child=inline_serializer(
                            name="Course",
                            fields={
                                "courseName": serializers.CharField(),
                                "courseLink": serializers.URLField(),
                                "courseCode": serializers.CharField(),
                                "professor": serializers.CharField(),
                                "notices": serializers.ListField(
                                    required=False,
                                    child=inline_serializer(
                                        name="Notice",
                                        fields={
                                            "link": serializers.URLField(),
                                            "content": serializers.CharField(),
                                            "index": serializers.CharField(),
                                            "title": serializers.CharField(),
                                            "date": serializers.DateField(),
                                            "files": serializers.ListField(
                                                required=False,
                                                child=inline_serializer(
                                                    name="File",
                                                    fields={
                                                        "fileName": serializers.CharField(),
                                                        "fileLink": serializers.URLField(),
                                                    }
                                                )
                                            ),
                                        }
                                    )
                                ),
                                "activities": serializers.ListField(
                                    child=serializers.ListField(
                                        required=False,
                                        child=inline_serializer(
                                            name="Activity",
                                            fields={
                                                "available": serializers.BooleanField(),
                                                "activityName": serializers.CharField(),
                                                "activityLink": serializers.URLField(required=False),
                                                "activityCode": serializers.CharField(),
                                                "activityType": serializers.CharField(),
                                                "lectureDeadline": serializers.CharField(required=False),
                                                "lectureTime": serializers.CharField(required=False),
                                                "attendance": serializers.BooleanField(required=False),
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

            try:
                extractor = Extractor(studentId=studentId, password=password)
                courses = asyncio.run(extractor.getCourses())

                return Response(
                    {
                        "courses": courses
                    },
                    status=status.HTTP_200_OK
                )
            
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)