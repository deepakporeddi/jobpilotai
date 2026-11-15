from django.urls import path
from .views import MasterResumeListCreateView, CandidateProfileDetailView
from .ai_views import ResumeAnalysisView, JobMatchView

urlpatterns = [
    path("", MasterResumeListCreateView.as_view(), name="master-resume-list-create"),
    path("<int:pk>/profile/", CandidateProfileDetailView.as_view(), name="candidate-profile-detail"),
    path("ai/analyze/", ResumeAnalysisView.as_view(), name="resume-ai-analysis"),
    path("ai/job-match/", JobMatchView.as_view(), name="resume-ai-job-match"),
]
