import asyncio

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from Scrape.extractor import Extractor
from Scrape.extractor.exception import ErrorType, ExtractorException
from Scrape.serializer import (
    CourseNotExistResponse,
    CourseResponseSerializer,
    CourseSerializer,
)


class CourseView(GenericAPIView):
    serializer_class = CourseSerializer

    @extend_schema(
        tags=["강좌 API"],
        summary="강좌 추출",
        description="모든 강좌의 정보를 추출합니다.",
        request=CourseSerializer,
        responses={
            status.HTTP_200_OK: CourseResponseSerializer,
            status.HTTP_404_NOT_FOUND: CourseNotExistResponse,
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            year = serializer.validated_data.get("year")
            semester = serializer.validated_data.get("semester")
            extract = serializer.validated_data.get("extract")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                courses = asyncio.run(
                    extractor.getCourses(year=year, semester=semester, extract=extract)
                )

                return Response({"data": courses}, status=status.HTTP_200_OK)

            except ExtractorException as e:
                e.logError()

                if e.type == ErrorType.COURSE_NOT_EXIST:
                    return Response(
                        {"message": e.message}, status=status.HTTP_404_NOT_FOUND
                    )
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
