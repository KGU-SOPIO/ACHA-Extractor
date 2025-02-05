import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from Scrap.extractor import Extractor
from Scrap.extractor.exception import ErrorType, ExtractorException

from Scrap.serializer import AuthSerializer, AuthResponseSerializer

class AuthenticationView(GenericAPIView):
    serializer_class = AuthSerializer

    @extend_schema(
        tags=["인증 API"],
        summary="인증 정보 검증 및 학생 정보 추출",
        description="학교 시스템에 로그인하여 인증 정보를 검증하고, 학생 정보를 추출합니다.",
        request=AuthSerializer,
        responses={
            status.HTTP_200_OK: AuthResponseSerializer
        }
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            getUser = serializer.validated_data.get("user")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                verification, userData, message = asyncio.run(extractor.verifyAuthentication(getUser=getUser))

                return Response(
                    {
                        "verification": verification,
                        "userData": userData or None,
                        "message": message
                    },
                    status=status.HTTP_200_OK
                )
            
            except ExtractorException as e:
                e.logError()
                return Response(
                    {
                        "verification": False,
                        "userData": None,
                        "message": e.message
                    },
                    status=status.HTTP_200_OK
                )
            
            except Exception as e:
                ExtractorException(errorType=ErrorType.SYSTEM_ERROR, message=str(e)).logError()
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)