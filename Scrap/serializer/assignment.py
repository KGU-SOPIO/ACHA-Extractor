from rest_framework import serializers

from Scrap.serializer.auth import VerificationSerializer

class AssignmentSerializer(serializers.Serializer):
    authentication = VerificationSerializer(
        required = True,
        error_messages = {
            "required": "로그인 정보는 필수 항목입니다.",
            "blank": "로그인 정보는 필수 항목입니다."
        }
    )

    code = serializers.CharField(
        label = "과제 코드",
        required = True,
        error_messages = {
            "required": "과제 코드는 필수 항목입니다.",
            "blank": "과제 코드는 필수 항목입니다."
        }
    )

    def validate(self, attrs):
        authentication_data = attrs["authentication"]
        attrs["studentId"] = authentication_data["studentId"]
        attrs["password"] = authentication_data["password"]
        return attrs