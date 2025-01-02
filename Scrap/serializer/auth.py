from rest_framework import serializers

class AuthSerializer(serializers.Serializer):
    studentId = serializers.CharField(
        label = "학번",
        required = True,
        min_length = 9,
        max_length = 9,
        error_messages = {
            "required": "학번은 필수 항목입니다.",
            "blank": "학번은 필수 항목입니다."
        }
    )

    password = serializers.CharField(
        label = "비밀번호",
        required = True,
        error_messages = {
            "required": "비밀번호는 필수 항목입니다.",
            "blank": "비밀번호는 필수 항목입니다."
        }
    )



class _AuthSerializer(serializers.Serializer):
    authentication = AuthSerializer(
        required = True,
        error_messages = {
            "required": "로그인 정보는 필수 항목입니다.",
            "blank": "로그인 정보는 필수 항목입니다."
        }
    )

    user = serializers.BooleanField(
        label = "사용자 정보 추출 여부",
        required = False,
        default = False
    )

    def validate(self, attrs):
        authentication_data = attrs["authentication"]
        attrs["studentId"] = authentication_data["studentId"]
        attrs["password"] = authentication_data["password"]
        return attrs