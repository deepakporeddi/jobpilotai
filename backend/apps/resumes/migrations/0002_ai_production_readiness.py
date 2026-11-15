import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resumes", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ResumeAIAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("result", models.JSONField()),
                ("source_fingerprint", models.CharField(max_length=64)),
                ("provider", models.CharField(max_length=50)),
                ("model", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resume", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_analyses", to="resumes.masterresume")),
            ],
            options={"ordering": ["-version"]},
        ),
        migrations.AddConstraint(
            model_name="resumeaianalysis",
            constraint=models.UniqueConstraint(fields=("resume", "version"), name="uniq_resume_ai_analysis_version"),
        ),
        migrations.CreateModel(
            name="ResumeAIJobMatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("job_description", models.TextField()),
                ("job_fingerprint", models.CharField(max_length=64)),
                ("source_fingerprint", models.CharField(max_length=64)),
                ("result", models.JSONField()),
                ("provider", models.CharField(max_length=50)),
                ("model", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resume", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_job_matches", to="resumes.masterresume")),
            ],
            options={"ordering": ["-version"]},
        ),
        migrations.AddConstraint(
            model_name="resumeaijobmatch",
            constraint=models.UniqueConstraint(fields=("resume", "version"), name="uniq_resume_ai_job_match_version"),
        ),
        migrations.CreateModel(
            name="AIUsageEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("operation", models.CharField(choices=[("analyze", "Resume analysis"), ("job_match", "Job match")], max_length=20)),
                ("provider", models.CharField(blank=True, max_length=50)),
                ("model", models.CharField(blank=True, max_length=120)),
                ("latency_ms", models.PositiveIntegerField(default=0)),
                ("success", models.BooleanField(default=False)),
                ("status_code", models.PositiveSmallIntegerField(default=500)),
                ("error_code", models.CharField(blank=True, max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resume", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ai_usage_events", to="resumes.masterresume")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_usage_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="aiusageevent",
            index=models.Index(fields=["user", "created_at"], name="ai_usage_user_created_idx"),
        ),
        migrations.AddIndex(
            model_name="aiusageevent",
            index=models.Index(fields=["operation", "created_at"], name="ai_usage_op_created_idx"),
        ),
    ]
