from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    studentId = serializers.CharField(
        label = '학번',
        required = True,
        error_messages = {
            'required': '학번은 필수 항목입니다.'
        }
    )

    password = serializers.CharField(
        label = '비밀번호',
        required = True,
        error_messages = {
            'required': '비밀번호는 필수 항목입니다.'
        }
    )