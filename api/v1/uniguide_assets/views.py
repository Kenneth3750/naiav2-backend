from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import mimetypes
import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import reverse


class UniguideAssets(APIView):
    def _assets_dir(self):
        project_root_candidate = os.path.join(settings.BASE_DIR, "..", "lugares_universidad")
        app_dir_candidate = os.path.join(settings.BASE_DIR, "lugares_universidad")

        if os.path.exists(project_root_candidate):
            return os.path.abspath(project_root_candidate)

        return os.path.abspath(app_dir_candidate)

    def get(self, request, filename=None):
        if filename:
            return self.serve_image(filename)
        return self.list_images(request)

    def list_images(self, request):
        try:
            assets_dir = self._assets_dir()
            if not os.path.exists(assets_dir):
                return Response(
                    {
                        "images": [],
                        "message": "Uniguide assets directory not found",
                        "directory": assets_dir,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            allowed_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
            images = []

            for file_name in os.listdir(assets_dir):
                file_path = os.path.join(assets_dir, file_name)
                if not os.path.isfile(file_path):
                    continue
                if not file_name.lower().endswith(allowed_extensions):
                    continue

                mime_type, _ = mimetypes.guess_type(file_name)
                image_url = request.build_absolute_uri(
                    reverse("uniguide_assets_detail", kwargs={"filename": file_name})
                )
                images.append(
                    {
                        "filename": file_name,
                        "url": image_url,
                        "size": os.path.getsize(file_path),
                        "mime_type": mime_type,
                    }
                )

            images.sort(key=lambda item: item["filename"].lower())
            return Response(
                {"total_images": len(images), "images": images, "directory": assets_dir},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to list uniguide assets", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def serve_image(self, filename):
        assets_dir = self._assets_dir()
        safe_name = os.path.basename(filename)
        file_path = os.path.join(assets_dir, safe_name)

        if not os.path.exists(file_path):
            raise Http404(f"Image not found: {safe_name}")

        if not os.path.commonpath([file_path, assets_dir]) == assets_dir:
            raise Http404("Invalid file path")

        allowed_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
        if not safe_name.lower().endswith(allowed_extensions):
            raise Http404("File is not an image")

        mime_type, _ = mimetypes.guess_type(safe_name)
        if not mime_type:
            mime_type = "application/octet-stream"

        response = FileResponse(open(file_path, "rb"), content_type=mime_type, as_attachment=False)
        response["Cache-Control"] = "public, max-age=3600"
        return response
