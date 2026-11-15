from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .ai_service import AIProviderError, _validate_payload, ANALYSIS_SCHEMA
from .models import AIUsageEvent, MasterResume, ResumeAIAnalysis, ResumeAIJobMatch


TEST_REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [\n        "rest_framework.authentication.TokenAuthentication",\n        "rest_framework.authentication.SessionAuthentication",\n    ],
    "DEFAULT_THROTTLE_RATES": {"ai_analysis": "1000/hour", "ai_job_match": "1000/hour"},
}


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class AIEndpointTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="candidate", password="Strong-pass-123")
        self.other_user = user_model.objects.create_user(username="other", password="Strong-pass-123")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.resume = MasterResume.objects.create(
            owner=self.user,
            original_file=ContentFile(b"%PDF-test", name="resume.pdf"),
            original_filename="resume.pdf",
            extracted_text="Python developer with Django and PostgreSQL experience.",
            extracted_profile={"skills": ["Python", "Django"]},
        )
        self.analysis = {
            "headline": "Backend developer",
            "summary": "Evidence-backed summary.",
            "strengths": ["Python experience"],
            "improvement_areas": ["Add project outcomes"],
            "skills_detected": ["Python", "Django"],
            "suggested_actions": ["Quantify impact"],
            "evidence_notes": ["Skills appear in the skills section"],
        }
        self.match = {
            "match_score": 82,
            "fit_summary": "Good evidence alignment.",
            "matching_evidence": ["Django project"],
            "relevant_skills": ["Python"],
            "skills_to_validate": ["Kubernetes"],
            "experience_gaps": ["No explicit Kubernetes project"],
            "resume_improvements": ["Add relevant project details"],
            "caveats": ["Estimated score, not a hiring prediction"],
        }

    def test_analysis_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/resumes/ai/analyze/", {"resume_id": self.resume.id}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_user_cannot_analyze_another_users_resume(self):
        other_resume = MasterResume.objects.create(
            owner=self.other_user,
            original_file=ContentFile(b"%PDF-other", name="other.pdf"),
            original_filename="other.pdf",
            extracted_text="Private resume content",
        )
        response = self.client.post("/api/resumes/ai/analyze/", {"resume_id": other_resume.id}, format="json")
        self.assertEqual(response.status_code, 404)

    @patch("apps.resumes.ai_views.analyze_resume")
    def test_analysis_is_persisted_with_incrementing_versions_and_usage(self, analyze):
        analyze.return_value = self.analysis
        first = self.client.post("/api/resumes/ai/analyze/", {"resume_id": self.resume.id}, format="json")
        second = self.client.post("/api/resumes/ai/analyze/", {"resume_id": self.resume.id}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual((first.data["version"], second.data["version"]), (1, 2))
        self.assertEqual(ResumeAIAnalysis.objects.filter(resume=self.resume).count(), 2)
        self.assertEqual(AIUsageEvent.objects.filter(user=self.user, success=True).count(), 2)
        latest = self.client.get("/api/resumes/ai/analyze/", {"resume_id": self.resume.id})
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(latest.data["version"], 2)

    @patch("apps.resumes.ai_views.analyze_resume")
    def test_provider_failure_is_sanitized_and_recorded(self, analyze):
        analyze.side_effect = AIProviderError("provider failed")
        response = self.client.post("/api/resumes/ai/analyze/", {"resume_id": self.resume.id}, format="json")
        self.assertEqual(response.status_code, 502)
        event = AIUsageEvent.objects.get(user=self.user)
        self.assertFalse(event.success)
        self.assertEqual(event.error_code, "provider")
        self.assertEqual(ResumeAIAnalysis.objects.count(), 0)

    def test_job_match_rejects_short_description(self):
        response = self.client.post(
            "/api/resumes/ai/job-match/",
            {"resume_id": self.resume.id, "job_description": "Too short"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("apps.resumes.ai_views.match_job")
    def test_job_match_is_persisted_and_versioned(self, match):
        match.return_value = self.match
        payload = {"resume_id": self.resume.id, "job_description": "Backend engineer role requiring Python and Django. " * 4}
        first = self.client.post("/api/resumes/ai/job-match/", payload, format="json")
        second = self.client.post("/api/resumes/ai/job-match/", payload, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual((first.data["version"], second.data["version"]), (1, 2))
        self.assertEqual(ResumeAIJobMatch.objects.filter(resume=self.resume).count(), 2)
        latest = self.client.get("/api/resumes/ai/job-match/", {"resume_id": self.resume.id})
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(latest.data["match"]["match_score"], 82)


class AISchemaValidationTests(TestCase):
    def test_rejects_missing_or_wrong_typed_fields(self):
        with self.assertRaises(AIProviderError):
            _validate_payload({"headline": "Developer"}, ANALYSIS_SCHEMA)

    def test_rejects_non_string_list_entries(self):
        data = {
            "headline": "Developer", "summary": "Summary",
            "strengths": [1], "improvement_areas": [], "skills_detected": [],
            "suggested_actions": [], "evidence_notes": [],
        }
        with self.assertRaises(AIProviderError):
            _validate_payload(data, ANALYSIS_SCHEMA)

    def test_truncates_long_text_and_clamps_match_score(self):
        from .ai_service import MATCH_SCHEMA
        data = {
            "match_score": 120, "fit_summary": "A" * 1500,
            "matching_evidence": [], "relevant_skills": [], "skills_to_validate": [],
            "experience_gaps": [], "resume_improvements": [], "caveats": [],
        }
        result = _validate_payload(data, MATCH_SCHEMA)
        self.assertEqual(result["match_score"], 100)
        self.assertEqual(len(result["fit_summary"]), 1000)
