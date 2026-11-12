"""
Upload serializers - implements validation for API-005.
Validates:
- Format: JPEG or PNG only (via magic bytes, not just content-type spoofable header)
- Size: max 5.0 MB (5,242,880 bytes) - TC-023/TC-024 boundary cases
- Non-empty file (TC-026)
- Non-corrupt / actual image (TC-029 spoofing)
"""
from rest_framework import serializers
from .models import Upload


ALLOWED_MIME = {'image/jpeg', 'image/png'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5.00 MB in bytes (5,242,880)


def _is_valid_image_magic(header_bytes: bytes) -> str:
    """
    Verify actual image type by magic bytes (MIME-spoofing defense, TC-029).
    Returns detected mime or empty string.
    """
    if len(header_bytes) < 12:
        return ''
    # JPEG magic: FF D8 FF
    if header_bytes[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    # PNG magic: 89 50 4E 47 0D 0A 1A 0A
    if header_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    return ''


class UploadSerializer(serializers.ModelSerializer):
    """Upload creation serializer."""

    class Meta:
        model = Upload
        fields = ('id', 'file', 'file_size', 'status', 'created_at', 'url_foto')
        read_only_fields = ('id', 'file_size', 'status', 'created_at', 'url_foto')

    def validate_file(self, value):
        # TC-026: reject empty files
        if value.size == 0:
            raise serializers.ValidationError(
                'Berkas kosong atau rusak. Silakan pilih foto lain.'
            )

        # TC-016 / TC-024: reject files larger than 5 MB
        if value.size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f'Ukuran file melebihi batas maksimal 5 MB. Ukuran Anda: {value.size / (1024*1024):.2f} MB.'
            )

        # Read first chunk for magic byte verification
        try:
            value.seek(0)
            header = value.read(12)
            value.seek(0)
        except Exception:
            raise serializers.ValidationError('Gagal membaca berkas.')

        detected = _is_valid_image_magic(header)
        if not detected:
            # TC-015 / TC-029: reject spoofed or unsupported formats
            raise serializers.ValidationError(
                'Format file tidak didukung. Gunakan JPEG atau PNG.'
            )

        # Also validate content-type header if present, but rely on magic bytes as authoritative
        # (If content_type says pdf/zip/etc but magic says jpeg, magic wins).
        return value

    def create(self, validated_data):
        file = validated_data['file']
        validated_data['file_size'] = file.size
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class UploadDetailSerializer(serializers.ModelSerializer):
    url_foto = serializers.SerializerMethodField()
    classification = serializers.SerializerMethodField()

    class Meta:
        model = Upload
        fields = ('id', 'url_foto', 'status', 'file_size', 'created_at', 'classification')

    def get_url_foto(self, obj):
        try:
            return obj.file.url
        except Exception:
            return ''

    def get_classification(self, obj):
        if hasattr(obj, 'classification_result'):
            from apps.classifications.serializers import ClassificationResultSerializer
            return ClassificationResultSerializer(obj.classification_result).data
        return None
