
from django.conf import settings
from django.core.files.storage import FileSystemStorage


def get_video_storage():
    """
    Use Cloudinary for video uploads when configured.
    Otherwise, use local filesystem storage for development.
    """
    if settings.CLOUDINARY_CONFIGURED:
        from cloudinary_storage.storage import VideoMediaCloudinaryStorage

        return VideoMediaCloudinaryStorage()

    return FileSystemStorage(location=settings.MEDIA_ROOT)
