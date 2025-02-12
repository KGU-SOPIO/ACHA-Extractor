from rest_framework import serializers

from Scrape.serializer.auth import VerificationSerializer


class TimetableSerializer(serializers.Serializer):
    authentication = VerificationSerializer(
        required=True,
        error_messages={
            "required": "로그인 정보는 필수 항목입니다.",
            "blank": "로그인 정보는 필수 항목입니다.",
        },
    )

    year = serializers.IntegerField(label="연도", required=False)

    semester = serializers.ChoiceField(
        label="학기",
        choices=[1, 2],
        required=False,
        error_messages={"invalid_choice": "학기는 1 또는 2만 입력해야 합니다."},
    )

    def validate(self, attrs):
        authentication_data = attrs["authentication"]
        attrs["studentId"] = authentication_data["studentId"]
        attrs["password"] = authentication_data["password"]
        return attrs
