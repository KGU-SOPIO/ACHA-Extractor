import asyncio

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from Scrape.extractor import Extractor
from Scrape.extractor.exception import ErrorType, ExtractorException
from Scrape.serializer import AuthSerializer, NoticeResponseSerializer


class NoticeView(GenericAPIView):
    serializer_class = AuthSerializer

    @extend_schema(
        tags=["강좌 API"],
        summary="강좌 공지사항 추출",
        description="강좌의 모든 공지사항을 추출합니다.",
        request=AuthSerializer,
        responses={status.HTTP_200_OK: NoticeResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            boardCode = self.kwargs.get("boardCode")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                notices = asyncio.run(extractor.getCourseNotice(boardCode=boardCode))

                return Response({"data": notices}, status=status.HTTP_200_OK)

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
