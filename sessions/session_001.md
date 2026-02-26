# Session 001 - Mompox Inteligente (Role ID 8)
**Fecha inicio:** 2026-02-25
**Última actualización:** 2026-02-26

## Resumen
Se creó el nuevo rol de Mompox (Gobernación de Bolívar) con role_id 8, siguiendo el patrón existente de gobernacion (role_id 7). En la segunda sesión se agregaron funciones de turismo y restaurantes, se corrigió el bug del parser XML y se mejoró el prompt para que SABIA llame las funciones inmediatamente.

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
- `requirements.txt` - Agregado `lxml==6.0.2` para parser XML del sitemap

## Decisiones de arquitectura
- **No se usa router_prompt** en services.py (a diferencia de gobernacion). Solo el prompt de realtime.
- El asistente se llama **SABIA** (Sistema de Atención de Bolívar con Inteligencia Artificial)
- Voz: `shimmer`
- El prompt sigue el mismo patrón extenso de gobernacion (personalidad, tono, acentos, inteligencia visual, preambles, funciones, reglas)
- **Turismo y restaurantes hardcodeados** para respuesta instantánea (datos de TripAdvisor)
- **Noticias dinámicas** via scraping del sitemap XML del blog Wix

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
- **Dependencia:** Requiere `lxml` para parsear XML

### 3. `POST /api/v1/mompox/tourism/` - GetMompoxTourismView
- **Función:** `get_mompox_tourism(user_id, status)`
- **Descripción:** Muestra los 9 principales sitios turísticos de Mompox
- **Params requeridos:** `user_id` (int), `status` (string)
- **Response keys:**
  - `display` - HTML grid de tarjetas con foto, ícono, nombre, categoría, descripción y dato destacado
  - `content_for_answers` - Resumen para TTS
- **Datos hardcodeados** (respuesta instantánea) con fotos de TripAdvisor
- **Sitios incluidos:**
  1. Centro Histórico de Santa Cruz de Mompox (UNESCO 1995)
  2. Iglesia de Santa Bárbara (1733, torre barroca octogonal)
  3. Plaza de Mercado (gastronomía y artesanías)
  4. Iglesia de la Inmaculada Concepción (1541, catedral)
  5. Iglesia de San Francisco (1564, retablos policromados)
  6. Casa del Diablo (leyenda momposina)
  7. La Piedra de Bolívar ("Si a Caracas debo la vida, a Mompox debo la gloria")
  8. Casa Museo Luis Guillermo Trespalacios (filigrana momposina)
  9. Casa Germán de Ribón (Casa de la Cultura, siglo XVIII)

### 4. `POST /api/v1/mompox/restaurants/` - GetMompoxRestaurantsView
- **Función:** `get_mompox_restaurants(user_id, status)`
- **Descripción:** Muestra los 6 mejores restaurantes de Mompox
- **Params requeridos:** `user_id` (int), `status` (string)
- **Response keys:**
  - `display` - HTML grid de tarjetas con foto, nombre, tipo de cocina, descripción, dato destacado y rango de precios
  - `content_for_answers` - Resumen para TTS
- **Datos hardcodeados** (respuesta instantánea) con fotos de TripAdvisor
- **Restaurantes incluidos:**
  1. Ambrosía Restaurante-Bar (Caribeña/Colombiana, $20.000-$30.000 COP)
  2. El Fuerte San Anselmo (Italiana/Mediterránea, pizzas al horno de leña, solo efectivo)
  3. Santa Coa Restaurante Bar (Caribeña/Internacional, vista al río)
  4. Comedor Costeño (Colombiana tradicional, Lomo Momposino)
  5. Café 1700 (Café y fusión, mejor café de Mompox)
  6. Verde Oliva Restaurant (Italiana/Colombiana, Plaza Fundacional)

### Endpoints utilitarios
- `GET /api/v1/mompox/health/` - Health check
- `GET /api/v1/mompox/functions/` - Lista funciones disponibles

## Bugs corregidos
- **Parser XML**: La función `get_mompox_news` fallaba con "Couldn't find a tree builder with the features you requested: xml". Solución: instalar `lxml` y agregarlo a `requirements.txt`.
- **Tool calling diferido**: SABIA decía "voy a mostrarte" pero no llamaba la función hasta el siguiente turno. Solución: se reforzó el prompt con instrucciones explícitas de llamar la función en el MISMO turno que el preamble.

## Pendiente para próximas sesiones
- Hospedaje / hoteles en Mompox
- ¿Cómo llegar a Mompox? (rutas desde Cartagena, Barranquilla, Bogotá)
- Contactos y líneas de emergencia
- Eventos en Mompox (festivales, Semana Santa, Jazz Festival)
- Posible integración con ChromaDB para base de conocimiento local de Mompox
