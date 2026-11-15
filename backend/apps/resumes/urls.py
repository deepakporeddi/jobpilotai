from django.urls import path
from .views import MasterResumeListCreateView

urlpatterns = [
    path("", MasterResumeListCreateView.as_view(), name="master-resume-list-create"),
]
