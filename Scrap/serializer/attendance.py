from rest_framework import serializers

from Scrap.serializer.auth import AuthSerializer

class _AttendanceSerializer(serializers.Serializer):
    authentication = AuthSerializer(
        required = True,
        error_messages = {
            "required": "로그인 정보는 필수 항목입니다.",
            "blank": "로그인 정보는 필수 항목입니다."
        }
    )

    code = serializers.CharField(
        label = "강좌 코드",
        required = True,
        min_length = 5,
        max_length = 5,
        error_messages = {
            "required": "강좌 코드는 필수 항목입니다.",
            "blank": "강좌 코드는 필수 항목입니다."
        }
    )

    def validate(self, attrs):
        authentication_data = attrs["authentication"]
        attrs["studentId"] = authentication_data["studentId"]
        attrs["password"] = authentication_data["password"]
        return attrs