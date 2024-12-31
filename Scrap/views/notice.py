import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from Scrap.extractor.extractor import Extractor

from Scrap.serializer.notice import _NoticeSerializer

class NoticeView(GenericAPIView):
    serializer_class = _NoticeSerializer

    @extend_schema(
        summary="강좌 공지사항 추출",
        description="강좌의 모든 공지사항을 추출합니다.",
        request=_NoticeSerializer,
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="NoticeResponse",
                fields={
                    "notices": serializers.ListField(
                        child=inline_serializer(
                            name="NoticeObject",
                            fields={
                                "link": serializers.URLField(),
                                "content": serializers.CharField(),
                                "index": serializers.CharField(),
                                "title": serializers.CharField(),
                                "date": serializers.DateField(),
                                "files": serializers.ListField(
                                    required=False,
                                    child=inline_serializer(
                                        name="FileObject",
                                        fields={
                                            "fileName": serializers.CharField(),
                                            "fileLink": serializers.URLField(),
                                        }
                                    )
                                ),
                            }
                        )
                    )
                }
            ),
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
                        "notices": notices
                    },
                    status=status.HTTP_200_OK
                )
            
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)