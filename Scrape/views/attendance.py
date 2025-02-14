import asyncio

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from Scrape.extractor import Extractor
from Scrape.extractor.exception import ErrorType, ExtractorException
from Scrape.serializer import AttendancesResponseSerializer, AuthSerializer


class AttendanceView(GenericAPIView):
    serializer_class = AuthSerializer

    @extend_schema(
        tags=["강좌 API"],
        summary="강좌 강의 출결 추출",
        description="강좌의 온라인 강의 출결 정보를 추출합니다.",
        request=AuthSerializer,
        responses={status.HTTP_200_OK: AttendancesResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            courseCode = self.kwargs.get("courseCode")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                attendances = asyncio.run(
                    extractor.getLectureAttendance(courseCode=courseCode)
                )

                return Response({"data": attendances}, status=status.HTTP_200_OK)

            except ExtractorException as e:
                e.logError()
                return Response(
                    {"message": e.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as e:
                ExtractorException(
                    errorType=ErrorType.SYSTEM_ERROR, message=str(e)
                ).logError()
                return Response(
                    {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
