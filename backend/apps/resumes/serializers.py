from rest_framework import serializers
from .models import MasterResume

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

class MasterResumeSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = MasterResume
        fields = ["id", "file", "original_filename", "content_type", "status", "created_at"]
        read_only_fields = ["id", "original_filename", "content_type", "status", "created_at"]

    def validate_file(self, value):
        name = value.name.lower()
        extension = "." + name.rsplit(".", 1)[-1] if "." in name else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("Upload a PDF or DOCX file.")
        if value.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("File must be 10 MB or smaller.")
        if value.content_type and value.content_type not in ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError("Unsupported file content type.")
        return value

    def create(self, validated_data):
        uploaded = validated_data.pop("file")
        request = self.context["request"]
        return MasterResume.objects.create(
            owner=request.user,
            original_file=uploaded,
            original_filename=uploaded.name,
            content_type=uploaded.content_type or "",
        )
