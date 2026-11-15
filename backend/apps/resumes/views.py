from rest_framework import generics, permissions
from .models import MasterResume
from .serializers import MasterResumeSerializer

class MasterResumeListCreateView(generics.ListCreateAPIView):
    serializer_class = MasterResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MasterResume.objects.filter(owner=self.request.user)
