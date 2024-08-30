from django.urls import path

from Scrap.views.course import CourseAPI

app_name = 'Scrap'

urlpatterns = [
    path('course/', CourseAPI.as_view(), name='Course')
]