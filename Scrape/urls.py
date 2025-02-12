from django.http import HttpResponse
from django.urls import path

from Scrape.views import *

app_name = "Scrape"

urlpatterns = [
    path("", lambda request: HttpResponse(status=200), name="check"),
    path("auth/", AuthenticationView.as_view(), name="auth"),
    path("timetable/", TimetableView.as_view(), name="timetable"),
    path("course/", CourseView.as_view(), name="course"),
    path("course/activity/", ActivityView.as_view(), name="activity"),
    path("course/notice/", NoticeView.as_view(), name="notice"),
    path("course/attendance/", AttendanceView.as_view(), name="attendance"),
    path("course/assignment/", AssignmentView.as_view(), name="assignment"),
]
