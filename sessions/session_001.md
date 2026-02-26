# Session 001 - Mompox Inteligente (Role ID 8)
**Fecha:** 2026-02-25

## Resumen
Se creó el nuevo rol de Mompox (Gobernación de Bolívar) con role_id 8, siguiendo el patrón existente de gobernacion (role_id 7).

## Estructura creada

### App Django: `apps/mompox/`
- `__init__.py`
- `apps.py` - MompoxConfig
- `models.py` - Vacío por ahora
- `admin.py`
- `tests.py`
- `functions.py` - Funciones de negocio
- `services.py` - `RealtimeMompoxService` con prompt de SABIA
- `migrations/__init__.py`

### API: `api/v1/mompox/`
- `__init__.py`
- `views.py` - Vistas de los endpoints
- `urls.py` - Rutas registradas

### Archivos modificados
- `naia/settings/base.py` - Agregado `apps.mompox` a INSTALLED_APPS
- `api/v1/urls.py` - Agregada ruta `path('mompox/', ...)`
- `apps/roles/services.py` - Importado `RealtimeMompoxService`, registrado role_id 8 y alias `"mompox"` en `RealtimeRoleService`

## Decisiones de arquitectura
- **No se usa router_prompt** en services.py (a diferencia de gobernacion). Solo el prompt de realtime.
- El asistente se llama **SABIA** (Sistema de Atención de Bolívar con Inteligencia Artificial)
- Voz: `shimmer`
- El prompt sigue el mismo patrón extenso de gobernacion (personalidad, tono, acentos, inteligencia visual, preambles, funciones, reglas)

## Endpoints creados

### 1. `POST /api/v1/mompox/about/` - AboutMompoxInteligenteView
- **Función:** `about_mompox_inteligente(user_id, status)`
- **Descripción:** Explica qué es Mompox Inteligente
- **Params requeridos:** `user_id` (int), `status` (string)
- **Response keys:**
  - `graph` - HTML con video autoplay del proyecto
  - `display` - HTML con info textual (letras negras, fondos claros): qué es, premio Smart City Expo 2025, por qué Mompox, qué buscamos, diferenciadores, aliados clave
  - `content_for_answers` - Resumen para TTS
- **Video:** `https://video.wixstatic.com/video/669154_b8b37ed3a2cb4d818b4c054e812803f7/1080p/mp4/file.mp4`
- **Fuente de contenido:** https://mompoxinteligente.bolivar.gov.co/conócenos

### 2. `POST /api/v1/mompox/news/` - GetMompoxNewsView
- **Función:** `get_mompox_news(user_id, status, limit=6)`
- **Descripción:** Obtiene últimas noticias del blog de Mompox Inteligente
- **Params requeridos:** `user_id` (int), `status` (string)
- **Params opcionales:** `limit` (int, default 6)
- **Response keys:**
  - `display` - HTML grid de tarjetas con imagen, título, fecha, excerpt y link a cada artículo
  - `content_for_answers` - Resumen con títulos de las 3 primeras noticias para TTS
- **Cómo funciona:** Scrapea el sitemap XML del blog Wix, toma las N más recientes por lastmod, luego scrapea cada post extrayendo datos del schema ld+json y og tags
- **Fuente:** https://mompoxinteligente.bolivar.gov.co/blog-posts-sitemap.xml

### Endpoints utilitarios
- `GET /api/v1/mompox/health/` - Health check
- `GET /api/v1/mompox/functions/` - Lista funciones disponibles

## Pendiente para próximas sesiones
- Crear más endpoints (turismo, eventos, lugares, etc.)
- Agregar más tools al RealtimeMompoxService
- Actualizar el prompt de SABIA con cada función nueva
- Posible integración con ChromaDB para base de conocimiento local de Mompox
