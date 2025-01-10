import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from Scrap.extractor import Extractor
from Scrap.extractor.exception import ErrorType, ExtractorException

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
                    "data": serializers.ListField(
                        child=serializers.ListField(
                            child=inline_serializer(
                                name="ActivityObject",
                                fields={
                                    "available": serializers.CharField(),
                                    "name": serializers.CharField(),
                                    "link": serializers.CharField(),
                                    "code": serializers.CharField(),
                                    "type": serializers.CharField(),
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
                        "data": activities
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