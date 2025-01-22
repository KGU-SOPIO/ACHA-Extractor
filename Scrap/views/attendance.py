import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from Scrap.extractor import Extractor
from Scrap.extractor.exception import ErrorType, ExtractorException

from Scrap.serializer.attendance import AttendanceSerializer
from Scrap.serializer.attendance_response import AttendancesResponseSerializer

class AttendanceView(GenericAPIView):
    serializer_class = AttendanceSerializer

    @extend_schema(
        tags=["강좌 API"],
        summary="강좌 강의 출결 상태 추출",
        description="강좌의 온라인 강의 출결 정보를 추출합니다.",
        request=AttendanceSerializer,
        responses={
            status.HTTP_200_OK: AttendancesResponseSerializer
        }
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            courseCode = serializer.validated_data.get("code")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                attendances = asyncio.run(extractor.getLectureAttendance(courseCode=courseCode))

                return Response(
                    {
                        "data": attendances
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