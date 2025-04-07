from django.http import HttpResponse
from django.urls import include, path

from Scrape.views import (
    ActivityView,
    AssignmentView,
    AttendanceView,
    AuthenticationView,
    CourseDetailView,
    CourseView,
    NoticeView,
    TimetableView,
)

app_name = "Scrape"

urlpatterns = [
    path("", lambda request: HttpResponse(status=200), name="check"),
    path(
        "v1/",
        include(
            [
                path("auth/", AuthenticationView.as_view(), name="auth"),
                path("timetable/", TimetableView.as_view(), name="timetable"),
                path("course/", CourseView.as_view(), name="course"),
                path(
                    "course/<str:courseCode>/",
                    CourseDetailView.as_view(),
                    name="course_detail",
                ),
                path(
                    "course/notice/<str:boardCode>/",
                    NoticeView.as_view(),
                    name="notice",
                ),
                path(
                    "course/assignment/<str:assignmentCode>/",
                    AssignmentView.as_view(),
                    name="assignment",
                ),
                path(
                    "course/<str:courseCode>/activity/",
                    ActivityView.as_view(),
                    name="activity",
                ),
                path(
                    "course/<str:courseCode>/attendance/",
                    AttendanceView.as_view(),
                    name="attendance",
                ),
            ]
        ),
    ),
]
