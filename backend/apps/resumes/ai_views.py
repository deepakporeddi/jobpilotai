import hashlib
import json
import os
import time

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from .ai_service import AIConfigurationError, AIProviderError, analyze_resume, match_job
from .models import AIUsageEvent, MasterResume, ResumeAIAnalysis, ResumeAIJobMatch


class AIAnalysisRateThrottle(UserRateThrottle):
    scope = "ai_analysis"


class AIJobMatchRateThrottle(UserRateThrottle):
    scope = "ai_job_match"


def _fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _provider_metadata():
    return (
        os.getenv("AI_PROVIDER", "openai_compatible").strip()[:50],
        os.getenv("AI_MODEL", "").strip()[:120],
    )


def _record_usage(user, resume, operation, started, success, status_code, error_code=""):
    provider, model = _provider_metadata()
    try:
        AIUsageEvent.objects.create(
            user=user,
            resume=resume,
            operation=operation,
            provider=provider,
            model=model,
            latency_ms=min(2_147_483_647, max(0, int((time.monotonic() - started) * 1000))),
            success=success,
            status_code=status_code,
            error_code=error_code[:50],
        )
    except Exception:
        # Telemetry must never turn a successful AI request into a failed request.
        pass


def _owned_resume(request):
    resume_id = request.data.get("resume_id")
    try:
        resume_id = int(resume_id)
    except (TypeError, ValueError):
        return None, Response({"detail": "A valid resume_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    resume = MasterResume.objects.filter(owner=request.user, pk=resume_id).first()
    if resume is None:
        return None, Response({"detail": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)
    if not isinstance(resume.extracted_text, str) or not resume.extracted_text.strip():
        return None, Response({"detail": "This resume has no extracted text to analyze."}, status=status.HTTP_400_BAD_REQUEST)
    return resume, None


class ResumeAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIAnalysisRateThrottle]

    def post(self, request):
        resume, error = _owned_resume(request)
        if error:
            return error
        started = time.monotonic()
        try:
            result = analyze_resume(resume)
            fingerprint = _fingerprint({"text": resume.extracted_text, "profile": resume.extracted_profile})
            with transaction.atomic():
                locked_resume = MasterResume.objects.select_for_update().get(pk=resume.pk, owner=request.user)
                version = (ResumeAIAnalysis.objects.filter(resume=locked_resume).order_by("-version").values_list("version", flat=True).first() or 0) + 1
                saved = ResumeAIAnalysis.objects.create(
                    resume=locked_resume, version=version, result=result,
                    source_fingerprint=fingerprint, provider=_provider_metadata()[0],
                    model=_provider_metadata()[1],
                )
            _record_usage(request.user, resume, AIUsageEvent.Operation.ANALYZE, started, True, status.HTTP_200_OK)
            return Response({"resume_id": resume.id, "version": saved.version, "created_at": saved.created_at, "analysis": result})
        except AIConfigurationError as exc:
            _record_usage(request.user, resume, AIUsageEvent.Operation.ANALYZE, started, False, 503, "configuration")
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIProviderError as exc:
            _record_usage(request.user, resume, AIUsageEvent.Operation.ANALYZE, started, False, 502, "provider")
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    def get(self, request):
        resume_id = request.query_params.get("resume_id")
        try:
            resume_id = int(resume_id)
        except (TypeError, ValueError):
            return Response({"detail": "A valid resume_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        resume = MasterResume.objects.filter(owner=request.user, pk=resume_id).first()
        if resume is None:
            return Response({"detail": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)
        saved = resume.ai_analyses.first()
        if saved is None:
            return Response({"detail": "No saved AI analysis exists for this resume."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"resume_id": resume.id, "version": saved.version, "created_at": saved.created_at, "analysis": saved.result})


class JobMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIJobMatchRateThrottle]

    def post(self, request):
        resume, error = _owned_resume(request)
        if error:
            return error
        job_description = request.data.get("job_description", "")
        if not isinstance(job_description, str) or len(job_description.strip()) < 100:
            return Response({"detail": "Paste a job description with at least 100 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if len(job_description) > 15000:
            return Response({"detail": "Job description must be 15,000 characters or less."}, status=status.HTTP_400_BAD_REQUEST)
        job_description = job_description.strip()
        started = time.monotonic()
        try:
            result = match_job(resume, job_description)
            source_fingerprint = _fingerprint({"text": resume.extracted_text, "profile": resume.extracted_profile})
            job_fingerprint = hashlib.sha256(job_description.encode("utf-8")).hexdigest()
            with transaction.atomic():
                locked_resume = MasterResume.objects.select_for_update().get(pk=resume.pk, owner=request.user)
                version = (ResumeAIJobMatch.objects.filter(resume=locked_resume).order_by("-version").values_list("version", flat=True).first() or 0) + 1
                provider, model = _provider_metadata()
                saved = ResumeAIJobMatch.objects.create(
                    resume=locked_resume, version=version, job_description=job_description,
                    job_fingerprint=job_fingerprint, source_fingerprint=source_fingerprint,
                    result=result, provider=provider, model=model,
                )
            _record_usage(request.user, resume, AIUsageEvent.Operation.JOB_MATCH, started, True, status.HTTP_200_OK)
            return Response({"resume_id": resume.id, "version": saved.version, "created_at": saved.created_at, "match": result})
        except AIConfigurationError as exc:
            _record_usage(request.user, resume, AIUsageEvent.Operation.JOB_MATCH, started, False, 503, "configuration")
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIProviderError as exc:
            _record_usage(request.user, resume, AIUsageEvent.Operation.JOB_MATCH, started, False, 502, "provider")
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    def get(self, request):
        resume_id = request.query_params.get("resume_id")
        try:
            resume_id = int(resume_id)
        except (TypeError, ValueError):
            return Response({"detail": "A valid resume_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        resume = MasterResume.objects.filter(owner=request.user, pk=resume_id).first()
        if resume is None:
            return Response({"detail": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)
        saved = resume.ai_job_matches.first()
        if saved is None:
            return Response({"detail": "No saved job match exists for this resume."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"resume_id": resume.id, "version": saved.version, "created_at": saved.created_at, "match": saved.result})
