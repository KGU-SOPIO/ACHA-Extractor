from django.urls import path

from Scrap.views.verify import VerificationView
from Scrap.views.timetable import TimetableView
from Scrap.views.course import CourseView
from Scrap.views.activity import ActivityView
from Scrap.views.notice import NoticeView
from Scrap.views.attendance import AttendanceView
from Scrap.views.assignment import AssignmentView

app_name = 'Scrap'

urlpatterns = [
    path("auth/", VerificationView.as_view(), name="verify"),
    path("timetable/", TimetableView.as_view(), name="timetable"),
    path('course/', CourseView.as_view(), name='course'),
    path('course/activity/', ActivityView.as_view(), name='activity'),
    path('course/notice/', NoticeView.as_view(), name='notice'),
    path('course/attendance/', AttendanceView.as_view(), name='attendance'),
    path('course/assignment/', AssignmentView.as_view(), name='assignment')
]