import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from Scrap.extractor import Extractor

from Scrap.serializer.auth import AuthSerializer

class VerificationView(GenericAPIView):
    serializer_class = AuthSerializer

    @extend_schema(
        summary="인증 정보 검증",
        description="학교 시스템에 로그인하여 인증 정보를 검증합니다.",
        request=AuthSerializer,
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="VerificationResponse",
                fields={
                    "verification": serializers.BooleanField(),
                    "message": serializers.CharField()
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
                verification, message = asyncio.run(extractor.verifyAuthentication())

                return Response(
                    {
                        "verification": verification,
                        "message": message
                    },
                    status=status.HTTP_200_OK
                )
            
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)