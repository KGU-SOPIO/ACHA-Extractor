import asyncio

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from Scrap.extractor.extractor import Extractor

from Scrap.serializer.assignment import _AssignmentSerializer

class AssignmentView(GenericAPIView):
    serializer_class = _AssignmentSerializer

    @extend_schema(
        summary="강좌 과제 추출",
        description="강좌의 과제 정보를 추출합니다.",
        request=_AssignmentSerializer,
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="AssignmentResponse",
                fields={
                    "assignment": inline_serializer(
                        name="AssignmentObject",
                        fields={
                            "gradingStatus": serializers.CharField(),
                            "deadline": serializers.CharField(),
                            "timeLeft": serializers.CharField(),
                            "lastModified": serializers.CharField(),
                            "description": serializers.CharField(),
                            "submitStatus": serializers.CharField(),
                        }
                    )
                }
            )
        }
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get("studentId")
            password = serializer.validated_data.get("password")
            assignmentCode = serializer.validated_data.get("code")

            try:
                extractor = Extractor(studentId=studentId, password=password)
                assignment = asyncio.run(extractor.getCourseAssignment(assignmentCode=assignmentCode))

                return Response(
                    {
                        "assignment": assignment
                    },
                    status=status.HTTP_200_OK
                )
                
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)