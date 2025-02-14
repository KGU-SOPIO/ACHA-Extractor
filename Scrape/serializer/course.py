from rest_framework import serializers


class CourseSerializer(serializers.Serializer):
    studentId = serializers.CharField(
        label="학번",
        required=True,
        min_length=9,
        max_length=9,
        error_messages={
            "required": "학번은 필수 항목입니다.",
            "blank": "학번은 필수 항목입니다.",
        },
    )

    password = serializers.CharField(
        label="비밀번호",
        required=True,
        error_messages={
            "required": "비밀번호는 필수 항목입니다.",
            "blank": "비밀번호는 필수 항목입니다.",
        },
    )

    year = serializers.IntegerField(label="연도", required=False)

    semester = serializers.ChoiceField(
        label="학기",
        choices=[1, 2],
        required=False,
        error_messages={"invalid_choice": "개설 학기는 1 또는 2만 입력해야 합니다."},
    )

    extract = serializers.BooleanField(required=False, default=True)
