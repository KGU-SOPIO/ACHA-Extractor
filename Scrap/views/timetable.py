import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from Scrap.extractor import Extractor
from Scrap.extractor.exception import ErrorType, ExtractorException

from Scrap.serializer.auth import VerificationSerializer
from Scrap.serializer.timetable_response import TimetableResponseSerializer

class TimetableView(GenericAPIView):
    serializer_class = VerificationSerializer

    @extend_schema(
        tags=["시간표 API"],
        summary="시간표 추출",
        description="시간표 정보를 추출합니다.",
        request=VerificationSerializer,
        responses={
            status.HTTP_200_OK: TimetableResponseSerializer
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
                        "data": timetable
                    },
                    status=status.HTTP_200_OK
                )
            
            except ExtractorException as e:
                e.logError()

                if e.type == ErrorType.TIMETABLE_NOT_EXIST:
                    return Response({"message": e.message}, status=status.HTTP_404_NOT_FOUND)
                return Response({"message": e.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                ExtractorException(type=ErrorType.SYSTEM_ERROR, message=str(e), args=e.args).logError()
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)