import asyncio

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from Scrape.extractor import Extractor
from Scrape.extractor.exception import ErrorType, ExtractorException
from Scrape.serializer import TimetableResponseSerializer, TimetableSerializer


class TimetableView(GenericAPIView):
    """
    이용자의 시간표 정보를 추출합니다.
    """

    serializer_class = TimetableSerializer

    @extend_schema(
        tags=["시간표 API"],
        summary="시간표 추출",
        description="시간표 정보를 추출합니다.",
        request=TimetableSerializer,
        responses={status.HTTP_200_OK: TimetableResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            year = serializer.validated_data.get("year")
            semester = serializer.validated_data.get("semester")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                timetable = asyncio.run(
                    extractor.getTimetable(year=year, semester=semester)
                )

                return Response({"data": timetable}, status=status.HTTP_200_OK)

            except ExtractorException as e:
                e.logError()
                return Response({"message": e.message}, status=e.type.httpStatus)
            except Exception as e:
                ExtractorException(
                    errorType=ErrorType.SYSTEM_ERROR, message=str(e)
                ).logError()
                return Response(
                    {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
