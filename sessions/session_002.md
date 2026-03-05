# Session 002 - Reestructuracion Role 6: Mental Health -> Bienestar Organizacional (BIELA)
**Fecha:** 2026-03-04

## Resumen
Se reestructuro el role_id 6, pasando de ser un rol de Mental Health (salud mental estudiantil) a **Bienestar Organizacional (BIELA)** para el departamento de Gestion Humana de Uninorte. El nuevo agente informa a colaboradores sobre dos beneficios institucionales: **Alternativas Deportivas y Artisticas** y **Medidas de Flexibilidad Laboral**.

## Cambios realizados

### Archivos modificados
- `apps/mental/services.py` - Se agrego `RealtimeBienestarService` (clase nueva) con 3 tools y prompt completo de BIELA. La clase `MentalHealthService` (legacy) se mantuvo sin cambios.
- `apps/mental/functions.py` - Se agregaron 3 funciones nuevas: `get_alternativas_deportivas`, `get_catalogo_actividades`, `get_flexibilidad_info` + constante `ACTIVIDADES_BIENESTAR` con 34 actividades hardcodeadas.
- `api/v1/mental/views.py` - Se agregaron 3 vistas nuevas: `GetAlternativasDeportivasView`, `GetCatalogoActividadesView`, `GetFlexibilidadInfoView` + endpoints utilitarios `health_check` y `get_available_functions`.
- `api/v1/mental/urls.py` - Se registraron las nuevas rutas bajo `/api/v1/mental/`.
- `api/v1/urls.py` - Se agrego la ruta `mental/` (no estaba registrada antes).
- `apps/roles/services.py` - Se cambio el import de `RealtimeBienestarService`, se registro role_id 6 con alias `"biela"` en `RealtimeRoleService`.

### Lo que se mantuvo (legacy)
- `MentalHealthService` (rol de chat no-realtime) sigue funcionando para el flujo antiguo de salud mental con screening, CAE info y wellness plans.
- `MentalAnalysisView` en `/api/v1/mental/form/analysis/` sigue activa.

## Nuevo servicio: RealtimeBienestarService

### Identidad
- **Nombre:** NAIA - Asistente de Bienestar Organizacional
- **Departamento:** Gestion Humana, Universidad del Norte
- **Voz:** shimmer
- **Alias en roles:** `"biela"` / role_id 6

### Contacto de Bienestar Organizacional (embebido en prompt)
- Extension: 4597
- Celular/WhatsApp: 3114129772
- Correo: bienestarorg@uninorte.edu.co
- Telefono: 605-3509509
- Extension Flexibilidad: 3208

## Endpoints creados

### 1. `POST /api/v1/mental/alternativas/` - GetAlternativasDeportivasView
- **Funcion:** `get_alternativas_deportivas(user_id, status)`
- **Descripcion:** Info general del beneficio de Alternativas Deportivas y Artisticas
- **Response keys:** `display` (HTML con descripcion, publico, requisitos, condiciones, inscripcion, FAQs, contacto), `content_for_answers` (resumen TTS)
- **Datos:** Hardcodeados - beneficio para colaboradores de planta, catedraticos y familiares de Combarranquilla. Sin costo, cupos limitados, febrero a noviembre.

### 2. `POST /api/v1/mental/catalogo/` - GetCatalogoActividadesView
- **Funcion:** `get_catalogo_actividades(user_id, status)`
- **Descripcion:** Catalogo visual de TODAS las alternativas deportivas y artisticas con imagenes reales, horarios, ubicaciones y botones de inscripcion directa
- **Response keys:** `display` (HTML grid de tarjetas con imagenes reales del portal), `content_for_answers` (resumen TTS)
- **34 actividades incluidas:** voleibol, yoga, tenis, taekwondo, running, natacion, futbol, rumba, danza, musica, patinaje, gimnasia, percusion, orquesta, club de caminantes, club de cocina, club de lectura, entre otras
- **Imagenes:** URLs reales del portal de Gestion Humana de Uninorte
- **Links:** Cada tarjeta tiene boton de inscripcion directa al portal

### 3. `POST /api/v1/mental/flexibilidad/` - GetFlexibilidadInfoView
- **Funcion:** `get_flexibilidad_info(user_id, status)`
- **Descripcion:** Info completa de las 3 medidas de Flexibilidad Laboral
- **Response keys:** `display` (HTML con las 3 modalidades), `content_for_answers` (resumen TTS)
- **Modalidades:**
  - **Flexiacademia** (Docentes): max 1.5 dias/semana fuera campus (TC), media jornada (MT). Contrato indefinido o fijo >3 meses.
  - **Flexiespacio** (Administrativos): 4 dias/mes (directivos), 3 dias/mes (coordinadores/analistas). Registro en Agatha. No aplica cargos tecnicos.
  - **Flexitiempo** (Horarios alternativos): Flexi1-5, registro en Agatha, vigencia trimestral. Bono de Tiempo (Flexi4) solo tecnicos/auxiliares.

### Endpoints utilitarios
- `GET /api/v1/mental/health/` - Health check del servicio BIELA
- `GET /api/v1/mental/functions/` - Lista funciones disponibles

## Decisiones de arquitectura
- **Se reutilizo la app `mental`** en vez de crear una app nueva, ya que el role_id 6 es el mismo
- **Legacy coexiste:** `MentalHealthService` (chat) sigue activo, `RealtimeBienestarService` (realtime) es el nuevo
- **Datos hardcodeados** para respuesta instantanea (34 actividades con imagenes reales del portal)
- **Conocimiento embebido en el prompt** sobre requisitos de flexibilidad y alternativas deportivas (extraido de PDFs institucionales)
- **No usa ChromaDB** - todo el conocimiento esta en el prompt y las funciones

## Fuentes de datos
- PDF "Alternativas Deportivas y Artisticas" de Gestion Humana
- PDF "Medidas de Flexibilidad Laboral" de Gestion Humana
- Portal de Gestion Humana de Uninorte (imagenes y links de inscripcion)
