import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from Scrap.extractor import Extractor
from Scrap.extractor.exception import ErrorType, ExtractorException

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
                    "data": serializers.ListField(
                        child=inline_serializer(
                            name="CourseObject",
                            fields={
                                "name": serializers.CharField(),
                                "link": serializers.URLField(),
                                "identifier": serializers.CharField(),
                                "code": serializers.CharField(),
                                "professor": serializers.CharField(),
                                "noticeCode": serializers.CharField(),
                                "notices": serializers.ListField(
                                    required=False,
                                    child=inline_serializer(
                                        name="NoticeObject_",
                                        fields={
                                            "link": serializers.URLField(),
                                            "content": serializers.CharField(),
                                            "index": serializers.CharField(),
                                            "title": serializers.CharField(),
                                            "date": serializers.DateField(),
                                            "files": serializers.ListField(
                                                required=False,
                                                child=inline_serializer(
                                                    name="FileObject_",
                                                    fields={
                                                        "name": serializers.CharField(),
                                                        "link": serializers.URLField(),
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
                                            name="ActivityObject_",
                                            fields={
                                                "available": serializers.BooleanField(),
                                                "name": serializers.CharField(),
                                                "link": serializers.URLField(required=False),
                                                "code": serializers.CharField(),
                                                "type": serializers.CharField(),
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
                        "data": courses
                    },
                    status=status.HTTP_200_OK
                )
            
            except ExtractorException as e:
                e.logError()
                return Response({"message": e.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                ExtractorException(type=ErrorType.SYSTEM_ERROR, message=str(e), args=e.args).logError()
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)