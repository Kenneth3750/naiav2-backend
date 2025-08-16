from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import mimetypes
import os
import re
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.urls import reverse
import logging

class GovImages(APIView):
    def format_file_size(self, size_bytes):
        """Formatea el tamaño del archivo a una representación legible"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def extract_step_number(self, filename):
        """Extrae el número de paso de nombres de archivo como 'step1.png', 'step_2.jpg', etc."""
        match = re.search(r'step[_-]?(\d+)', filename.lower())
        if match:
            return int(match.group(1))
        return None
        
    def get(self, request, filename=None):
        """
        GET /gov-images/ - Lista todas las imágenes disponibles
        GET /gov-images/<filename> - Sirve una imagen específica
        """
        # Si se especifica un filename, servir la imagen
        if filename:
            return self.serve_image(request, filename)
        
        # Si no, listar todas las imágenes
        return self.list_images(request)

    
    def list_images(self, request):
        """Lista todas las imágenes en la carpeta gov_images"""
        try:
            # Ruta a la carpeta gov_images en la raíz del proyecto
            images_dir = os.path.join(settings.BASE_DIR, 'gov_images')
            
            # Verificar que la carpeta existe
            if not os.path.exists(images_dir):
                return Response({
                    "images": [],
                    "message": "Gov images directory not found",
                    "directory": images_dir
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Extensiones de imagen permitidas
            allowed_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')
            
            images = []
            
            # Recorrer archivos en la carpeta
            for filename in os.listdir(images_dir):
                file_path = os.path.join(images_dir, filename)
                
                # Verificar que es un archivo y tiene extensión de imagen
                if os.path.isfile(file_path) and filename.lower().endswith(allowed_extensions):
                    # Obtener información del archivo
                    file_stats = os.stat(file_path)
                    file_size = file_stats.st_size
                    
                    # Detectar tipo MIME
                    mime_type, _ = mimetypes.guess_type(filename)
                    
                    # Crear URL para servir la imagen
                    image_url = request.build_absolute_uri(
                        reverse('gov_images_detail', kwargs={'filename': filename})
                    )
                    
                    image_info = {
                        "filename": filename,
                        "url": image_url,
                        "size": file_size,
                        "size_formatted": self.format_file_size(file_size),
                        "mime_type": mime_type,
                        "extension": os.path.splitext(filename)[1].lower()
                    }
                    
                    # Información específica para pasos del pasaporte
                    if filename.startswith('step'):
                        step_number = self.extract_step_number(filename)
                        if step_number:
                            image_info["step"] = step_number
                            image_info["category"] = "passport_process"
                    
                    images.append(image_info)
            
            # Ordenar por nombre de archivo
            images.sort(key=lambda x: x['filename'])
            
            # Separar por categorías si es necesario
            passport_images = [img for img in images if img.get('category') == 'passport_process']
            other_images = [img for img in images if img.get('category') != 'passport_process']
            
            response_data = {
                "total_images": len(images),
                "images": images,
                "passport_process_images": sorted(passport_images, key=lambda x: x.get('step', 0)),
                "other_images": other_images,
                "directory": images_dir
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": "Failed to list government images",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def serve_image(self, request, filename):
        """Sirve una imagen específica"""
        try:
            # Ruta completa al archivo
            images_dir = os.path.join(settings.BASE_DIR, 'gov_images')
            file_path = os.path.join(images_dir, filename)
            
            # Verificar que el archivo existe y está dentro de la carpeta permitida
            if not os.path.exists(file_path):
                raise Http404(f"Image not found: {filename}")
            
            # Verificar que es realmente un archivo dentro de gov_images (seguridad)
            if not os.path.commonpath([file_path, images_dir]) == images_dir:
                raise Http404("Invalid file path")
            
            # Verificar que es una imagen
            allowed_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')
            if not filename.lower().endswith(allowed_extensions):
                raise Http404("File is not an image")
            
            # Detectar tipo MIME
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Servir el archivo
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=mime_type,
                as_attachment=False  # Para mostrar en el navegador, no descargar
            )
            
            # Headers para cache (opcional)
            response['Cache-Control'] = 'public, max-age=3600'  # Cache por 1 hora
            
            return response
            
        except Http404:
            raise
        except Exception as e:
            raise Http404(f"Error serving image: {filename}")

