from django.urls import path
from .views import MasterResumeListCreateView, CandidateProfileDetailView

urlpatterns = [
    path("", MasterResumeListCreateView.as_view(), name="master-resume-list-create"),
    path("<int:pk>/profile/", CandidateProfileDetailView.as_view(), name="candidate-profile-detail"),
]
