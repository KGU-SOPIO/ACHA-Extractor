import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from Scrap.extractor import Extractor
from Scrap.extractor.exception import ExtractorException

from Scrap.serializer.auth import AuthSerializer

class TimetableView(GenericAPIView):
    serializer_class = AuthSerializer

    @extend_schema(
        summary="시간표 추출",
        description="시간표 정보를 추출합니다.",
        request=AuthSerializer,
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="TimetableResponse",
                fields={
                    "timetable": serializers.ListField(
                        child=inline_serializer(
                            name="TimetableObject",
                            fields={
                                "courseName": serializers.CharField(),
                                "courseIdentifier": serializers.CharField(),
                                "professor": serializers.CharField(),
                                "classroom": serializers.CharField(),
                                "day": serializers.CharField(),
                                "classTime": serializers.IntegerField(),
                                "startAt": serializers.IntegerField(),
                                "endAt": serializers.IntegerField()
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
                timetable = asyncio.run(extractor.getTimetable())

                return Response(
                    {
                        "timetable": timetable
                    },
                    status=status.HTTP_200_OK
                )
            
            except ExtractorException as e:
                ExtractorException.logError(exception=e)
                return Response({"message": e.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)