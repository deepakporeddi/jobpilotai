# Initial schema for the pre-existing resume library.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="MasterResume",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_file", models.FileField(upload_to="master-resumes/%Y/%m/")),
                ("original_filename", models.CharField(max_length=255)),
                ("content_type", models.CharField(blank=True, max_length=100)),
                ("extracted_text", models.TextField(blank=True)),
                ("extracted_profile", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("uploaded", "Uploaded"), ("parsed", "Parsed"), ("needs_review", "Needs review"), ("failed", "Failed")], default="uploaded", max_length=20)),
                ("parse_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="master_resumes", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
