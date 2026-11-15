from rest_framework import generics, permissions
from .models import MasterResume
from .serializers import MasterResumeSerializer, CandidateProfileSerializer

class MasterResumeListCreateView(generics.ListCreateAPIView):
    serializer_class = MasterResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return MasterResume.objects.filter(owner=self.request.user)

class CandidateProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get","patch","head","options"]
    def get_queryset(self):
        return MasterResume.objects.filter(owner=self.request.user)
