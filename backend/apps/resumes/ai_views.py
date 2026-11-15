from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MasterResume
from .ai_service import AIConfigurationError, AIProviderError, analyze_resume, match_job


class ResumeAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        resume_id = request.data.get("resume_id")
        if not resume_id:
            return Response({"detail": "resume_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        resume = MasterResume.objects.filter(owner=request.user, pk=resume_id).first()
        if not resume:
            return Response({"detail": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)
        if not resume.extracted_text.strip():
            return Response({"detail": "This resume has no extracted text to analyze."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Response({"resume_id": resume.id, "analysis": analyze_resume(resume)})
        except AIConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIProviderError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class JobMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        resume_id = request.data.get("resume_id")
        job_description = request.data.get("job_description", "")
        if not resume_id:
            return Response({"detail": "resume_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(job_description, str) or len(job_description.strip()) < 100:
            return Response({"detail": "Paste a job description with at least 100 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if len(job_description) > 15000:
            return Response({"detail": "Job description must be 15,000 characters or less."}, status=status.HTTP_400_BAD_REQUEST)
        resume = MasterResume.objects.filter(owner=request.user, pk=resume_id).first()
        if not resume:
            return Response({"detail": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)
        if not resume.extracted_text.strip():
            return Response({"detail": "This resume has no extracted text to compare."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = match_job(resume, job_description.strip())
            return Response({"resume_id": resume.id, "match": result})
        except AIConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIProviderError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
