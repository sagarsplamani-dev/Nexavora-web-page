from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("syllabus.txt", views.download_syllabus, name="syllabus"),
]
