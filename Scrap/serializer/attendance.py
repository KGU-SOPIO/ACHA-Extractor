from rest_framework import serializers
from django.core.validators import RegexValidator

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
        validators = [RegexValidator(regex=r'^\d{5}$', message="강좌 코드는 5자리 숫자여야 합니다.")],
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