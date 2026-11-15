from pathlib import Path
from rest_framework import serializers
from .models import MasterResume

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

class MasterResumeSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    extracted_profile = serializers.JSONField(read_only=True)
    extracted_text = serializers.CharField(read_only=True)

    class Meta:
        model = MasterResume
        fields = ["id","file","original_filename","content_type","status","parse_error","extracted_profile","extracted_text","created_at"]
        read_only_fields = ["id","original_filename","content_type","status","parse_error","extracted_profile","extracted_text","created_at"]

    def validate_file(self, value):
        extension = Path(value.name).suffix.lower()
        if extension not in {".pdf",".docx"}:
            raise serializers.ValidationError("Upload a PDF or Word DOCX file.")
        if value.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("File must be 10 MB or smaller.")
        header = value.read(8)
        value.seek(0)
        if extension == ".pdf" and not header.startswith(b"%PDF-"):
            raise serializers.ValidationError("The uploaded file does not appear to be a valid PDF.")
        if extension == ".docx" and not header.startswith(b"PK"):
            raise serializers.ValidationError("The uploaded file does not appear to be a valid DOCX document.")
        return value

    def create(self, validated_data):
        uploaded = validated_data.pop("file")
        resume = MasterResume.objects.create(owner=self.context["request"].user,original_file=uploaded,original_filename=uploaded.name,content_type=uploaded.content_type or "")
        try:
            from .parser import extract_resume_text, build_review_profile
            resume.extracted_text = extract_resume_text(resume.original_file.path,resume.original_filename)
            resume.extracted_profile = build_review_profile(resume.extracted_text)
            resume.status = MasterResume.Status.NEEDS_REVIEW
        except Exception as exc:
            resume.status = MasterResume.Status.FAILED
            resume.parse_error = str(exc)
        resume.save(update_fields=["extracted_text","extracted_profile","status","parse_error","updated_at"])
        return resume

class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterResume
        fields = ["id","extracted_profile"]
