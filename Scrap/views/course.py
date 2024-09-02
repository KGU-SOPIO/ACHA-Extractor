import asyncio

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from Scrap.extractor.extractor import Extractor

from Scrap.serializer.login import LoginSerializer

class CourseAPI(APIView):
    def get(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            studentId = serializer.validated_data.get('studentId')
            password = serializer.validated_data.get('password')

            try:
                extractor = Extractor(studentId, password)
                courses = asyncio.run(extractor.extractCourse())

                return Response(
                    {
                        'courses': courses
                    },
                    status = status.HTTP_200_OK
                )
            
            except Exception as e:
                return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)