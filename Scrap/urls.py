from django.urls import path

from Scrap.views.course import CourseAPI
from Scrap.views.attendance import AttendanceAPI
from Scrap.views.notice import NoticeAPI
from Scrap.views.assignment import AssignmentAPI
from Scrap.views.activity import ActivityAPI

app_name = 'Scrap'

urlpatterns = [
    path('course/', CourseAPI.as_view(), name='course'),
    path('course/attendance/', AttendanceAPI.as_view(), name='attendance'),
    path('course/notice/', NoticeAPI.as_view(), name='notice'),
    path('course/assignment/', AssignmentAPI.as_view(), name='assignment'),
    path('course/activity/', ActivityAPI.as_view(), name='activity')
]