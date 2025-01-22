from rest_framework import serializers

from Scrap.serializer.auth import VerificationSerializer

class CourseSerializer(serializers.Serializer):
    authentication = VerificationSerializer(
        required = True,
        error_messages = {
            "required": "로그인 정보는 필수 항목입니다.",
            "blank": "로그인 정보는 필수 항목입니다."
        }
    )

    extract = serializers.BooleanField(
        required = False,
        default = True
    )

    def validate(self, attrs):
        authentication_data = attrs["authentication"]
        attrs["studentId"] = authentication_data["studentId"]
        attrs["password"] = authentication_data["password"]
        return attrs