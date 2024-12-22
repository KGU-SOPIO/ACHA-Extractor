import asyncio

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from Scrap.extractor.extractor import Extractor

from Scrap.serializer.assignment import AssignmentSerializer

class AssignmentAPI(APIView):
    def get(self, request):
        serializer = AssignmentSerializer(data=request.data)

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