import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from Scrap.extractor import Extractor
from Scrap.extractor.exception import ErrorType, ExtractorException

from Scrap.serializer.notice import NoticeSerializer
from Scrap.serializer.notice_response import NoticeResponseSerializer

class NoticeView(GenericAPIView):
    serializer_class = NoticeSerializer

    @extend_schema(
        tags=["강좌 API"],
        summary="강좌 공지사항 추출",
        description="강좌의 모든 공지사항을 추출합니다.",
        request=NoticeSerializer,
        responses={
            status.HTTP_200_OK: NoticeResponseSerializer
        }
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            boardCode = serializer.validated_data.get("code")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                notices = asyncio.run(extractor.getCourseNotice(boardCode=boardCode))

                return Response(
                    {
                        "data": notices
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