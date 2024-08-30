from django.urls import path, include

urlpatterns = [
    path('', include('Scrap.urls'), name='Scrap')
]