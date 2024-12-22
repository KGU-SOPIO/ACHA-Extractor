from rest_framework import serializers
from django.core.validators import RegexValidator

from Scrap.serializer.auth import AuthSerializer

class _NoticeSerializer(serializers.Serializer):
    authentication = AuthSerializer(
        required = True,
        error_messages = {
            "required": "로그인 정보는 필수 항목입니다.",
            "blank": "로그인 정보는 필수 항목입니다."
        }
    )

    code = serializers.CharField(
        label = "공지사항 게시판 코드",
        required = True,
        validators = [RegexValidator(regex=r'^\d{6}$', message="공지사항 게시판 코드는 6자리 숫자여야 합니다.")],
        error_messages = {
            "required": "공지사항 게시판 코드는 필수 항목입니다.",
            "blank": "공지사항 게시판 코드는 필수 항목입니다."
        }
    )

    def validate(self, attrs):
        authentication_data = attrs["authentication"]
        attrs["studentId"] = authentication_data["studentId"]
        attrs["password"] = authentication_data["password"]
        return attrs