from django.conf import settings
from django.db import models


class MasterResume(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PARSED = "parsed", "Parsed"
        NEEDS_REVIEW = "needs_review", "Needs review"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="master_resumes")
    original_file = models.FileField(upload_to="master-resumes/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)
    extracted_text = models.TextField(blank=True)
    extracted_profile = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    parse_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_filename


class ResumeAIAnalysis(models.Model):
    resume = models.ForeignKey(MasterResume, on_delete=models.CASCADE, related_name="ai_analyses")
    version = models.PositiveIntegerField()
    result = models.JSONField()
    source_fingerprint = models.CharField(max_length=64)
    provider = models.CharField(max_length=50)
    model = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["resume", "version"], name="uniq_resume_ai_analysis_version"),
        ]


class ResumeAIJobMatch(models.Model):
    resume = models.ForeignKey(MasterResume, on_delete=models.CASCADE, related_name="ai_job_matches")
    version = models.PositiveIntegerField()
    job_description = models.TextField()
    job_fingerprint = models.CharField(max_length=64)
    source_fingerprint = models.CharField(max_length=64)
    result = models.JSONField()
    provider = models.CharField(max_length=50)
    model = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["resume", "version"], name="uniq_resume_ai_job_match_version"),
        ]


class AIUsageEvent(models.Model):
    class Operation(models.TextChoices):
        ANALYZE = "analyze", "Resume analysis"
        JOB_MATCH = "job_match", "Job match"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_usage_events")
    resume = models.ForeignKey(MasterResume, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_usage_events")
    operation = models.CharField(max_length=20, choices=Operation.choices)
    provider = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=120, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    success = models.BooleanField(default=False)
    status_code = models.PositiveSmallIntegerField(default=500)
    error_code = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"], name="ai_usage_user_created_idx"),
            models.Index(fields=["operation", "created_at"], name="ai_usage_op_created_idx"),
        ]
