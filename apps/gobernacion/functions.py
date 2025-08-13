from openai import OpenAI
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Dict
import os
from apps.status.services import set_status
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import os
load_dotenv()


OPENAI_API_KEY = os.getenv("open_ai")
client = OpenAI(api_key=OPENAI_API_KEY)



def frequently_asked_questions(user_id: int, question: str, status: str) -> Dict:
    """
    This functions handles the answers for frequently asked questions.
    An 'AI agent' reads the question and selects the most relevant link in the knowledge base to provide an answer.
    """

    agent_prompt = """
    Eres un agente especializado en seleccionar los link necesarios para poder dar respuesta a las preguntas realizadas por el usuario.
    Tu tarea es analizar la pregunta del usuario y respodner unicamente con un array que contenga los links relevantes para dar respuesta a las preguntas del usuario.
    Ejemplos de respuesta son:
    '["https://www.example.com/faq1", "https://www.example.com/faq2"]'

    ESTA PROHIBIDO QUE AGREGUES TEXTO MAS ALLA DEL ARRAY. ESTA PROHIBIDO QUE SALUDES O DESPIDAS AL USUARIO.

    En caso de que no encuentres un link relevante, responde con un array vacio: '[]'. NUEVAMENTE ESTA PROHIBIDO QUE AGREGUES TEXTO MAS ALLA DEL ARRAY.

    La base de datos de links para responder la pregunta son los siguientes:

    Links de la gobernación


LINKS SOBRE JURIDICA
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14868-como-procede-la-gobernacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14867-donde-recibe-la-gobernacion-del-atlantico-las-notificaciones-sobre-los-procesos-judiciales
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14866-que-es-una-accion-de-nulidad-y-restablecimiento-del-derecho
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14865-que-es-una-accion-popular
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14864-que-es-una-accion-de-grupo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14863-que-es-la-notificacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14862-que-es-una-excepcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14861-que-se-entiende-por-pretensiones
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14860-que-es-un-acto-administrativo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14859-que-es-un-derecho-de-peticion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14858-cual-es-el-marco-normativo-de-la-accion-de-tutela
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14857-que-procedimiento-realiza-la-gobernacion-del-atlantico-cuando-se-presentan-acciones-de-tutelas-en-contra-de-esta-entidad
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14856-que-debo-tener-en-cuenta-al-presentar-una-accion-de-tutela
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14854-puedo-presentar-accion-de-tutela-en-la-gobernacion-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14853-quien-puede-instaurar-accion-de-tutela
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14851-que-es-la-accion-de-tutela
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14850-que-requisitos-debe-cumplir-una-demanda
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14849-que-es-una-demanda
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14848-que-es-la-competencia
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14847-que-es-una-jurisdiccion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/416-juridica12/14846-que-son-los-procesos-judiciales


LINKS SOBRE PREGUNTAS QUEJAS Y CONTROL DISCIPLINARIO
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/675-preguntas-quejas-y-control-disciplinario/15017-cuando-se-designa-a-un-defensor-de-oficio-en-el-proceso-disciplinario
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/675-preguntas-quejas-y-control-disciplinario/15016-es-obligatorio-que-el-sujeto-procesal-contrate-los-servicios-de-un-abogado-para-que-lo-represente-en-el-proceso-disciplinario
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/675-preguntas-quejas-y-control-disciplinario/15015-que-es-un-poder
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/675-preguntas-quejas-y-control-disciplinario/15014-que-es-un-auto-de-tramite
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/675-preguntas-quejas-y-control-disciplinario/15013-cuales-son-las-etapas-procesales-en-una-actuacion-disciplinaria


LINKS SOBRE PREGUNTAS AGUA POTABLE
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/605-preguntas-agua-potable/14688-que-contiene-el-plan-de-aseguramiento-de-la-prestacion-de-los-servicios-del-pda-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/605-preguntas-agua-potable/14687-que-busca-el-plan-de-gestion-social-del-pda-del-departamento-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/605-preguntas-agua-potable/14686-cuantos-municipios-del-departamento-del-atlantico-pertenecen-al-pda-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/605-preguntas-agua-potable/14648-en-que-consiste-el-mecanismo-de-viabilizacion-de-proyectos
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/605-preguntas-agua-potable/14647-quienes-son-los-participantes-de-los-pda
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/605-preguntas-agua-potable/14624-como-se-financian-los-pda-los-recursos-disponibles-para-la-formulacion-e-implementacion-de-los-pda-podran-provenir-entre-otras-fuentes-de-las-siguientes
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/605-preguntas-agua-potable/14621-que-son-los-planes-departamentales-de-agua-pda


LINKS SOBRE PREGUNTAS CAPITAL SOCIAL
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14467-que-son-las-plataformas-de-las-juventud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14468-que-funcion-cumplen-las-plataformas-de-juventud-en-los-municipios
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14470-se-cuenta-con-un-formulario-unico-para-el-registro-de-plataformas-de-juventud-en-las-personerias-municipales
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14471-donde-deben-registrarse-las-plataformas-de-las-juventudes
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14473-es-posible-reglamentar-las-plataformas-de-las-juventudes-cuando-no-se-tiene-consejo-de-juventud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14474-dentro-de-la-metodologia-de-trabajo-de-la-plataforma-es-viable-conformar-grupos-de-trabajo-segun-las-funciones-que-le-asigna-la-ley-a-estas-instancias-de-participacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14475-que-es-una-agenda-juvenil
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14476-cual-es-la-diferencia-entre-una-plataforma-de-las-juventudes-y-una-asamblea-de-juventudes
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14477-cuanto-es-la-duracion-maxima-de-una-plataforma-de-las-juventudes
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14478-cuales-son-los-derechos-de-las-plataformas-de-las-juventudes
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14479-que-son-los-consejos-de-juventud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14481-quien-convoca-la-eleccion-de-los-consejos-de-juventud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14482-donde-se-eligen-los-consejos-de-juventud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14483-cuales-son-los-documentos-para-ejercer-el-derecho-al-voto-para-los-consejos-de-juventud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14484-cuales-son-los-requisitos-para-ser-candidato-a-los-consejos-de-juventud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/415-capital-social/14485-como-quedara-conformado-el-consejo-de-juventud


LINKS SOBRE PREGUNTAS CIUDADELA 
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/421-ciudadela9/14733-quienes-conforman-la-junta-especial-ciudadela-universitaria
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/421-ciudadela9/14732-quien-recauda-y-maneja-los-recursos-derivados-del-cobro-de-la-estampilla-ciudadela-universitaria-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/421-ciudadela9/14731-que-actos-o-contratos-se-encuentran-gravados-por-la-estampilla-ciudadela-universitaria-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/421-ciudadela9/14730-que-es-la-estampilla-ciudadela-universitaria-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/421-ciudadela9/14727-que-una-estampilla


LINKS SOBRE PREGUNTAS CONTROL INTERNO
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/14715-cuales-son-las-funciones-del-comite-institucional-de-coordinacion-de-control-interno
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/14714-que-es-el-comite-institucional-de-gestion-y-desempeno
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/14713-cuales-son-los-comites-que-acorde-con-el-decreto-1499-de-2017-se-deben-conformar-en-el-orden-territorial
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/14712-cual-es-el-plazo-para-actualizar-mipg-en-las-entidades
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/14711-cual-es-el-fundamento-del-modelo-integrado-de-planeacion-y-gestion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/14710-que-es-modelo-integrado-de-planeacion-y-gestion-mipg
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/14709-cuales-son-los-roles-de-la-secretaria-de-control-interno
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/4347-puede-la-oficina-de-control-interno-participar-en-decisiones-administrativas-en-la-entidad
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/4346-que-diferencia-hay-entre-control-interno-de-gestion-y-control-interno-disciplinario
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/4345-que-es-un-plan-de-mejoramiento
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/4344-cuales-son-los-fundamentos-del-sistema-de-control-interno
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/4343-quienes-ejercen-el-control-interno
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/417-control-interno11/4342-cual-es-la-funcion-de-la-secretaria-de-control-interno


LINKS SOBRE PREGUNTAS CULTURA
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2965-ique-es-concertacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2964-que-es-atlantico-teatral
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2963-que-es-el-sistema-general-de-participacion-sgp
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2962-que-es-la-estampilla-procultura
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2961-que-son-los-vigias-del-patrimonio-cultural-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2960-que-es-la-red-departamental-de-museos
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2958-que-es-la-red-departamental-de-bibliotecas-publicas
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2956-que-es-el-consejo-departamental-de-patrimonio-cultural
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2955-ien-que-consiste-el-consejo-departamental-de-cultura
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2953-ique-es-el-sinic
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/402-cultura/2954-icomo-ingresar-los-datos-en-el-sinic


LINKS SOBRE PREGUNTAS DESARROLLO
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15220-en-cuanto-tiempo-debe-la-administracion-responder-mi-peticion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15219-cuales-son-los-beneficios-de-la-formalizacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15218-que-es-la-formalizacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15217-quienes-pueden-participar-en-las-ferias-que-organiza-la-subsecretaria-de-gestion-empresarial-de-la-secretaria-de-desarrollo-economico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15216-que-es-una-unidad-productiva
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15215-que-es-emprendimiento-por-necesidad
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15214-que-es-emprendimiento-por-oportunidad
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15213-que-es-emprendimiento
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15212-quien-es-un-emprendedor
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15211-como-acceder-a-los-programas-de-la-subsecretaria-de-gestion-empresarial
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15210-cuales-son-los-programas-de-la-subsecretaria-de-gestion-empresarial
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15209-quienes-pueden-acceder-a-los-programas-de-la-subsecretaria-de-gestion-empresarial
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15208-cuales-son-los-proyectos-prioritarios-de-infraestructura-turistica
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15207-cuales-son-las-iniciativas-de-turismo-comunitario
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15206-que-son-colegios-amigos-del-turismo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15205-que-es-el-cluster-de-turismo-de-naturaleza
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15204-cuantos-ecohoteles-hay-en-el-departamento
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15203-cuantas-areas-protegidas-tenemos-en-el-departamento-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15202-cuales-son-las-cifras-de-alojamiento-en-el-departamento
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15201-en-que-playas-puedo-realizar-deportes-nauticos-en-el-departamento
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/404-desarrollo/15200-que-parques-tematicos-tenemos-en-el-departamento



LINKS SOBRE PREGUNTAS EDUCACIÓN
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/19533-que-tramites-se-surten-desde-el-area-de-isnpeccion-y-vigilancia-de-la-secretaria-de-educacion-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/19532-cual-es-la-funcion-del-area-de-inspeccion-y-vigilancia-de-la-secretaria-de-educacion-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/17481-cual-es-el-costo-por-licencias-de-funcionamiento-de-educacion-formal
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/17480-por-que-la-secretaria-de-educacion-del-atlantico-no-atiende-el-distrito-de-barranquilla-soledad-y-malambo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/17479-cuales-municipios-atiende-la-secretaria-de-educacion-del-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/17477-que-es-escuela-en-casa
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/17476-cual-es-el-costo-y-procedimiento-para-solicitar-certificado-laboral-para-tramite-personal
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/17474-como-puedo-recuperar-clave-sac-y-de-humano-en-linea
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/8338-formatos-bienestar
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/5824-es-posible-para-un-estudiante-egresado-aplicar-las-pruebas-saber-11-de-manera-individual
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/5823-con-que-frecuencia-se-realizan-las-pruebas-saber-3-5-y-9-grado
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/5822-como-se-puede-hacer-para-la-inscripcion-el-las-pruebas-del-estado-icfes
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/5821-cuales-beneficios-trae-para-la-institucion-educativa-la-evaluacion-de-desempeno
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/5819-cuales-son-los-procedimientos-para-adopcion-e-incorporacion-de-la-planta-definitiva-y-se-requiere-posesion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/423-educacion7/5818-es-competente-el-municipio-certificado-para-homologar-o-nivelar-los-salarios-del-personal-administrativo-que-recibe-y-puede-hacerlo-con-recursos-del-sgp


LINKS SOBRE PREGUNTAS HACIENDA
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/412-hacienda14/16454-que-debo-hacer-para-realizar-el-tramite-de-desembargo-por-concepto-de-impuesto-vehicular
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/412-hacienda14/16453-que-debo-hacer-para-cancelar-mi-impuesto-vehicular-2021


LINKS SOBRE PREGUNTAS SECRETARIA GENERAL
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/15031-14-cuando-envio-los-documentos-escaneados-por-correo-electronico-para-agilizar-el-tramite-de-revision-y-verificacion-de-cumplimiento-de-los-requisitos-ya-no-necesito-presentarlos-el-dia-de-la-cita
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/15030-13-una-vez-agendada-la-cita-por-internet-puedo-enviar-los-documentos-para-agilizar-el-tramite-de-revision
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/15029-12-como-se-solicita-la-cita-por-internet-para-el-tramite-de-pasaporte
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/15027-11-como-se-consigue-informacion-sobre-los-requisitos-para-el-tramite-de-pasaporte
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/15026-10-2-como-puede-comunicarse-para-realizar-consultas-sobre-el-tramite-de-pasaporte
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/15025-9-como-se-envia-un-documento-o-peticion-sobre-el-tramite-de-pasaporte
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/14965-8-que-es-un-bono-pensional-cuando-tengo-derecho-a-el-y-quien-tiene-la-legitimidad-para-solicitarlo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/14964-7-como-solicito-copia-de-mi-historia-laboral
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/14928-6-como-solicito-mi-certificado-de-tiempos-laborados-plataforma-cetil
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/14908-que-requisitos-debo-cumplir-para-obtener-una-sustitucion-pensional
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/14897-que-se-necesita-para-reclamar-un-auxilio-funerario-de-un-pensionado
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/14871-4-como-solicitar-un-certificado-de-pensionado-o-no-pensionado
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/14745-2-como-se-solicita-un-certificado-laboral-funcionario-contratista
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/424-general6/14741-1-como-se-radica-un-documento-o-solicitud



LINKS SOBRE PREGUNTAS SECRETARIA DE PLANEACION
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14549-que-es-un-banco-de-proyectos-y-para-que-sirve
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14548-que-marco-normativo-soporta-la-rendicion-de-cuentas
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14547-cuando-se-rinde-cuentas
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14546-que-es-la-rendicion-cuentas
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14545-a-quien-aplica-el-mipg
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14544-cuales-son-los-objetivos-del-mipg
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14543-que-es-el-mipg
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14542-a-quienes-beneficia-el-contar-con-una-ley-de-transparencia-y-del-derecho-de-acceso-a-la-informacion-publica
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14541-que-es-el-derecho-de-acceso-a-la-informacion-publica
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14540-que-es-la-transparencia
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14539-que-se-entiende-por-causas-en-los-riesgos-de-corrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14538-en-todos-los-procesos-o-procedimientos-de-la-entidad-se-deben-formular-riesgos-de-corrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14537-se-debe-realizar-un-mapa-de-riesgos-por-todos-los-procesos-de-la-entidad-o-uno-por-cada-proceso
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14536-como-se-define-un-riesgo-de-corrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14535-el-plan-anticorrupcion-y-de-atencion-al-ciudadano-y-el-mapa-de-riesgos-de-corrupcion-debe-ser-socializado
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14534-la-no-elaboracion-del-plan-genera-alguna-responsabilidad
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14533-despues-de-publicado-es-posible-ajustar-y-modificar-el-plan-anticorrupcion-y-de-atencion-al-ciudadano-del-mapa-de-riesgos-de-corrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14531-donde-debe-publicarse-el-plan
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14530-quien-debe-realizar-seguimiento-al-plan-anticorrupcion-y-de-atencion-al-ciudadano-en-la-entidad
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14529-se-debe-realizar-seguimiento-al-plan-anticorrupcion-y-de-atencion-al-ciudadano-y-a-los-riesgos-de-corrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14528-quien-debe-elaborar-el-plan-anticorrupcion-y-de-atencion-al-ciudadano-al-interior-de-cada-entidad
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14527-hay-un-formato-o-estructura-para-la-presentacion-del-plan-anticorrupcion-y-de-atencion-al-ciudadano
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14526-los-cinco-componentes-son-los-unicos-que-debe-contener-el-plan-anticorrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14525-cuales-son-los-componentes-de-la-politica-anticorrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14524-es-necesario-realizar-alguna-actividad-preliminar-antes-de-formular-el-plan-anticorrupcion-y-de-atencion-al-ciudadano
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14522-cual-es-el-plazo-para-elaborar-el-plan-anticorrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14521-que-entidades-deben-elaborar-el-plan-anticorrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14520-el-plan-anticorrupcion-es-independiente-del-modelo-integrado-de-planeacion-y-gestion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14518-que-es-el-plan-anticorrupcion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14517-cuales-son-las-funciones-de-la-subsecretaria-de-fortalecimiento-institucional
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14515-cuales-son-las-funciones-de-la-subsecretaria-de-sistemas-de-informacion-y-proyectos
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14514-cuales-son-las-funciones-de-la-subsecretaria-de-direccionamiento-estrategico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/14512-cuales-son-las-funciones-de-la-secretaria-de-planeacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/6409-construyendo-el-plan-de-desarrollo-atlantico-lider
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/417-ique-pasa-si-un-concejo-o-una-asamblea-no-aprueba-el-plan-de-desarrollo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/416-iun-plan-de-desarrollo-se-considera-valido-sin-el-concepto-del-consejo-territorial-de-planeacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/415-ies-posible-modificar-una-vez-aprobado-el-plan-de-desarrollo-de-una-entidad-territorial-y-en-caso-afirmativo-cual-es-la-fecha-limite
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/414-icual-es-el-procedimiento-para-modificar-el-plan-de-desarrollo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/413-icuando-hay-elecciones-atipicas-en-una-entidad-territorial-que-terminos-tiene-el-alcalde-o-gobernador-para-presentar-el-plan-de-desarrollo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/412-icuales-metas-deben-ponderarse
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/411-que-pasa-en-el-caso-de-una-meta-que-se-haya-cumplido-en-vigencias-anteriores-y-que-en-el-momento-de-evaluarse-continua-sobre-ejecutandose
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/410-ique-es-una-meta-de-mantenimiento
http://atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/409-ies-posible-introducir-modificaciones-a-los-proyectos-de-ordenanza-o-acuerdo-aprobatorios-de-los-planes-de-desarrollo-territoriales
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/408-ique-es-un-plan-de-accion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/405-ique-es-un-plan-de-ordenamiento-territorial-pot
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/404-icuales-son-los-rangos-para-el-desarrollo-de-un-plan-de-ordenamiento-territorial-pot
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/103-secretaria-de-planeacion/403-ique-es-el-sicep



LINKS SOBRE PREGUNTAS SECRETARÍA DE SALUD
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14844-como-puedo-hacer-un-traslado-territorial
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14843-que-es-portabilidad-nacional
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14842-que-es-movilidad-entre-regimenes
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14841-como-se-aplica-el-principio-de-la-continuidad-en-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14840-que-sucede-con-las-personas-sin-capacidad-de-pago
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14839-cuales-son-los-tipos-de-afiliacion-en-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14838-que-es-la-seguridad-social-integral
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14837-que-es-el-sistema-de-seguridad-social-integral-y-como-esta-conformado
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14836-de-que-manera-la-afiliacion-me-puede-garantizar-el-acceso-a-los-servicios-de-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14835-que-es-la-seguridad-social
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14833-cual-es-la-normatividad-que-rige-a-las-asociaciones-de-usuarios
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14832-que-soporta-la-legalidad-de-una-asociacion-de-usuarios
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14831-que-determina-ser-miembro-de-una-asociacion-alianza-de-usuario
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14830-para-que-sirven-las-asociaciones-de-usuarios
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14829-en-donde-deben-constituirse-una-asociacion-de-usuarios
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14828-quienes-pueden-pertenecer-a-una-asociacion-de-usuarios
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14827-que-es-una-asociacion-de-usuarios
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14826-que-clase-de-novedades-deben-reportar-en-el-registro-especial-de-prestadores-reps-los-prestadores-de-servicios-de-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14825-en-que-casos-se-requiere-visita-de-verificacion-previa-para-la-habilitacion-de-servicios
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14824-cuales-serian-los-tipos-de-sanciones-que-le-aplicarian-a-los-prestadores-de-servicios-de-salud-segun-la-ley-09-de-1979
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14823-cual-es-la-vigencia-de-la-habilitacion-en-el-registro-especial-de-prestadores-de-servicios-de-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14822-cual-es-el-objetivo-del-distintivo-de-habilitacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14821-de-acuerdo-a-la-normatividad-vigente-quienes-deben-realizar-las-visitas-de-verificacion-de-habilitacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14820-quien-realiza-la-inspeccion-vigilancia-y-control-del-contenido-calidad-y-reporte-de-la-informacion-que-conforma-el-sistema-de-informacion-para-la-calidad-del-sistema-obligatorio-de-garantia-de-calidad-de-la-atencion-de-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14819-las-instituciones-prestadoras-de-servicios-de-salud-tienen-la-obligacion-de-establecer-un-programa-de-auditoria
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14818-quien-vigila-el-cumplimiento-del-desarrollo-de-los-procesos-de-auditoria-para-el-mejoramiento-de-la-calidad-de-la-atencion-en-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14818-quien-vigila-el-cumplimiento-del-desarrollo-de-los-procesos-de-auditoria-para-el-mejoramiento-de-la-calidad-de-la-atencion-en-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14817-cuales-son-los-componentes-del-sistema-obligatorio-de-garantia-de-calidad-de-atencion-en-salud-del-sistema-general-de-seguridad-social-en-salud-sogc
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14816-que-es-el-sistema-obligatorio-de-garantia-de-calidad-de-atencion-en-salud-del-sistema-general-de-seguridad-social-en-salud-sogcs
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14815-cual-es-el-procedimiento-de-entrega-del-registro-como-profesional-en-caso-de-ser-exonerado-del-servicio-social-obligatorio
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14814-como-se-realiza-la-inscripcion-al-proceso-de-asignacion-convocado-por-el-ministerio-de-salud-y-proteccion-social
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14813-como-se-realiza-la-asignacion-de-plazas-de-sso-que-convoca-el-ministerio-de-salud-y-proteccion-social
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14812-como-se-pueden-inscribir-los-profesionales-al-proceso-de-asignacion
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14811-como-se-asignan-las-plazas-de-servicio-social-obligatorio
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14810-a-que-entidad-le-corresponde-brindar-el-curso-de-induccion-a-los-profesionales-que-van-a-hacer-el-servicio-social-obligatorio
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14809-quienes-deben-cumplir-con-el-servicio-social-obligatorio
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14808-que-es-el-servicio-social-obligatorio-sso
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14773-cuales-son-los-sintomas-del-covid-19
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14772-que-hago-para-evitar-que-me-de-coronavirus
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14771-como-se-trata-el-covid-19
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14770-como-se-transmite-el-covid-19
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14769-que-es-el-covid-19
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14768-que-es-un-coronavirus
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14767-como-reportar-los-eventos-adversos-dentro-del-proceso-de-tecnovigilancia
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14765-que-es-la-tecnovigilancia
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14766-cual-es-el-objetivo-principal-de-la-tecnovigilancia
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14764-como-reporto-una-reaccion-adversa-a-los-medicamentos
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14763-que-es-la-farmacovigilancia
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14762-si-no-me-encuentro-inscrito-a-en-el-rethus-habiendo-obtenido-su-resolucion-del-ejercicio-profesional-o-tarjeta-profesional-antes-de-que-el-colegio-profesional-asumiera-funciones-publicas-donde-tengo-que-solicitar-la-inscripcion-a-rethus
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14761-si-me-encuentro-inscrito-en-el-rethus-y-mis-datos-presentan-inconsistencias-que-debo-hacer-para-que-se-corrija
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14760-si-no-me-encuentro-inscrito-a-en-el-rethus-y-tengo-resolucion-de-autorizacion-del-ejercicio-expedida-antes-de-la-entrada-en-operacion-del-rethus-que-debo-hacer-para-inscribirme
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14759-como-puedo-consultar-si-me-encuentro-inscrito-en-el-rethus
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14758-quienes-deben-inscribirse-en-el-rethus
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14757-a-que-perfiles-profesionales-u-ocupacionales-va-dirigido-el-registro-de-titulos-y-la-inscripcion-en-el-rethus
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14756-que-es-el-rethus
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14755-si-perdi-mi-resolucion-de-autorizacion-del-ejercicio-profesional-u-ocupacional-en-salud-donde-puedo-solicitarla
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14754-para-trabajar-en-un-departamento-diferente-al-de-la-secretaria-de-salud-que-expidio-la-resolucion-de-autorizacion-del-ejercicio-profesional-debo-solicitar-la-inscripcion-en-dicho-departamento
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14753-si-el-correo-electronico-que-deje-registrado-cuando-hice-la-solicitud-no-esta-activo-o-esta-bloqueado-como-hago-para-que-me-envien-la-resolucion-de-autorizacion-de-mi-ejercicio-profesional
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14752-como-hago-para-que-me-entreguen-la-resolucion-de-autorizacion-de-mi-ejercicio-profesional-la-cual-solicite-y-aun-no-he-ido-por-ella-tengo-que-dirigirme-hasta-las-instalaciones-de-la-secretaria-de-salud-a-buscarla
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14751-donde-realizo-la-solicitud-de-resolucion-de-autorizacion-del-ejercicio-profesional-u-ocupacional-si-soy-egresado-de-una-entidad-formadora-en-el-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14750-que-es-la-resolucion-de-autorizacion-del-ejercicio-profesional-u-ocupacional
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14749-que-es-el-registro-de-titulos
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/14082-preguntas-frecuentes-en-el-proceso-de-registro-de-titulos-del-talento-humano-en-salud
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2608-idonde-busco-las-alertas-sanitarias
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2607-ipara-que-sirve-una-alerta-sanitaria
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2606-ique-son-las-alertas-sanitarias
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2554-ilos-equipos-biomedicos-tambien-se-reportan
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2553-iquien-puede-reportar
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2552-ique-es-incidente-adverso-no-serio
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2551-ique-es-incidente-adverso-serio
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2550-ique-es-evento-adverso-no-serio
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/607-preguntas-secretaria-de-salud/2549-ique-es-evento-adverso-serio


LINKS SOBRE PREGUNTAS SECRETARÍA DE TIC
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/25882-que-es-peti
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14959-que-son-las-zonas-wi-fi
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14956-como-funciona-la-conectividad-wifi
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14955-que-es-una-red-wifi-y-como-funciona
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14953-que-se-necesita-para-jugar-un-videojuego
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14951-que-es-el-videojuego
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14937-como-evitar-caer-en-noticias-falsas
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14935-cuales-son-los-retos-y-oportunidades-de-las-tic-en-el-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14905-cual-es-el-rol-estrategico-de-las-tic-en-el-atlantico
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14904-consejos-para-comenzar-a-trabajar-en-la-industria-de-videojuegos
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14902-que-aportan-los-videojuegos-al-sector-educativo
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14737-que-entidades-deben-aplicar-la-politica-de-gobierno-digital
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14736-que-instrumentos-apoyan-la-politica-de-gobierno-en-digital
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/14735-que-es-y-cual-es-el-objetivo-del-gobierno-digital-en-el-departamento
https://www.atlantico.gov.co/index.php/preguntas-frecuentes/785-secretaria-de-tic/4326-que-es-vive-digital
"""


    set_status(user_id, status, 7)



    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "developer", "content": agent_prompt},
            {"role": "user", "content": question}
        ]
    )

    array_str = response.choices[0].message.content
    array = eval(array_str)
    answer_divs = []
    link_titles = []


    for item in array:
        response = requests.get(item, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        first_h1 = soup.find('h1', attrs={'itemprop': 'headline'})
        soup_divs = soup.find_all('div', attrs={'itemprop': 'articleBody'})
        
        # CORRECCIÓN: Convertir los objetos Tag a strings
        div_contents = []
        for div in soup_divs:
            div_contents.append(str(div))  
        
        answer_divs.append(div_contents)
        
        title = first_h1.text.strip() if first_h1 else "Información adicional"
        link_titles.append(title)

    if array:  
            cards_html = ""
            for link, title in zip(array, link_titles):
                cards_html += f'''
                <a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; transition: all 0.3s ease; transform: translateY(0);" 
                onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 15px 35px rgba(255,255,255,0.2)'" 
                onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 25px rgba(255,255,255,0.1)'">
                    
                    <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 20px; box-shadow: 0 8px 25px rgba(255,255,255,0.1);">
                        
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="background: rgba(255, 255, 255, 0.2); border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin-right: 15px;">
                                <span style="font-size: 18px;">🏛️</span>
                            </div>
                            <div style="flex: 1;">
                                <div style="background: rgba(255, 255, 255, 0.2); height: 2px; border-radius: 1px; margin-bottom: 5px;"></div>
                                <div style="background: rgba(255, 255, 255, 0.1); height: 1px; border-radius: 1px; width: 70%;"></div>
                            </div>
                        </div>
                        
                        <h4 style="color: #ffffff; font-size: 16px; font-weight: 600; margin: 0; line-height: 1.4; text-shadow: 0 1px 3px rgba(0,0,0,0.3);">
                            {title}
                        </h4>
                        
                        <div style="display: flex; align-items: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.2);">
                            <span style="color: #e2e8f0; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
                                Ver más información
                            </span>
                            <span style="color: #ffffff; margin-left: auto; font-size: 16px; transition: transform 0.3s ease;">→</span>
                        </div>
                    </div>
                </a>
                '''
            
            pretty_links = f'''
            <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(30, 58, 138, 0.3); margin: 20px 0;">
                <div style="text-align: center; margin-bottom: 25px;">
                    <h3 style="color: #ffffff; font-size: 24px; font-weight: bold; margin: 0; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                        📚 Enlaces de Interés - Gobernación del Atlántico
                    </h3>
                    <p style="color: #e2e8f0; margin: 8px 0 0 0; font-size: 14px;">
                        Explora más información oficial sobre tu consulta
                    </p>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                    {cards_html}
                </div>
                
                <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255, 255, 255, 0.2);">
                    <p style="color: #cbd5e1; font-size: 12px; margin: 0;">
                        🇨🇴 Información oficial de la Gobernación del Atlántico
                    </p>
                </div>
            </div>
            '''
    else:
        pretty_links = None

    return {"content_for_answers": answer_divs, "display": pretty_links}

def extraer_informacion_multas(soup):
    """
    Extrae la información específica del div de resultados de multas
    
    Returns:
        dict: Información estructurada sobre las multas
    """
    resultado = {
        "tiene_multas": False,
        "mensaje_principal": "",
        "servicios_disponibles": [],
        "div_resultado": ""
    }
    
    # Buscar el div específico de resultados
    div_resultado = soup.find("div", class_="input_search_header")
    
    if div_resultado:
        # Guardar el div completo
        resultado["div_resultado"] = str(div_resultado)
        
        # Extraer mensaje principal
        mensaje_bold = div_resultado.find("p", class_="font-weight-bold")
        if mensaje_bold:
            resultado["mensaje_principal"] = mensaje_bold.get_text(strip=True)
            
            # Determinar si tiene multas
            if "no presenta ninguna multa" in resultado["mensaje_principal"].lower():
                resultado["tiene_multas"] = False
            else:
                resultado["tiene_multas"] = True
        
        # Extraer lista de servicios
        lista_servicios = div_resultado.find("ul")
        if lista_servicios:
            for li in lista_servicios.find_all("li"):
                servicio = li.get_text(strip=True)
                if servicio:
                    resultado["servicios_disponibles"].append(servicio)
    
    return resultado

def consultar_multas_transito_atlantico(documento_placa):
    """
    Consulta multas en el portal de Tránsito del Atlántico
    
    Args:
        documento_placa (str): Número de identificación o placa del vehículo
        
    Returns:
        dict: Resultado de la consulta con información estructurada
    """
    
    # Configuración del navegador optimizada
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-logging')
    options.add_argument('--disable-web-security')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    driver = None
    
    try:
        # Inicializar driver
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        url = "https://digital.transitodelatlantico.gov.co/portal-servicios/#/public"
        print(f"Navegando a: {url}")
        driver.get(url)
        
        # Esperar a que cargue la página completamente
        print("Esperando a que cargue la página...")
        wait = WebDriverWait(driver, 20)
        
        # Esperar más tiempo para Angular
        time.sleep(5)
        print("Esperando a que Angular termine de cargar...")
        
        # Cerrar cualquier modal o overlay que pueda interferir
        try:
            close_buttons = driver.find_elements(By.CSS_SELECTOR, ".close, .modal-close, .btn-close")
            for btn in close_buttons:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(1)
                    print("Modal/overlay cerrado")
        except:
            pass
        
        # Buscar el campo de input por ID y esperar que sea interactuable
        input_field = wait.until(
            EC.element_to_be_clickable((By.ID, "busqueda"))
        )
        print("Campo de búsqueda encontrado y listo para interactuar")
        
        # Limpiar el campo y escribir el documento/placa
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
            time.sleep(1)
            
            input_field.clear()
            time.sleep(1)
            input_field.send_keys(documento_placa)
            print(f"Documento/placa ingresado: {documento_placa}")
        except Exception as e:
            print(f"Error al escribir en el campo: {e}")
            raise
        
        # Buscar y hacer clic en el botón de búsqueda
        try:
            search_button = wait.until(
                EC.element_to_be_clickable((By.ID, "btnBuscar"))
            )
            print("Botón de búsqueda encontrado y clickeable")
            
            driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(1)
            
            try:
                search_button.click()
                print("Botón clickeado con método normal")
            except Exception as click_error:
                print(f"Clic normal falló: {click_error}")
                print("Intentando clic con JavaScript...")
                driver.execute_script("arguments[0].click();", search_button)
                print("Botón clickeado con JavaScript")
                
        except Exception as e:
            print(f"Error al hacer clic en el botón: {e}")
            raise
        
        # Esperar a que se procese la búsqueda
        print("Esperando resultados...")
        time.sleep(10)
        
        # Esperar a que aparezca algún contenido de resultados
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            print("Página completamente cargada después de la búsqueda")
        except:
            print("Timeout esperando cambios, continuando...")
        
        # Capturar el HTML resultante
        try:
            page_source = driver.page_source
            print("HTML capturado exitosamente")
        except Exception as e:
            print(f"Error al capturar HTML: {e}")
            raise
        
        # Parsear con BeautifulSoup para extraer información relevante
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            print("BeautifulSoup parseado exitosamente")
        except Exception as e:
            print(f"Error al parsear con BeautifulSoup: {e}")
            raise
        
        # Extraer información específica de multas
        info_multas = extraer_informacion_multas(soup)
        print(f"Información extraída - Tiene multas: {info_multas['tiene_multas']}")
        
        return {
            "status": "success",
            "documento_placa": documento_placa,
            "tiene_multas": info_multas["tiene_multas"],
            "mensaje_principal": info_multas["mensaje_principal"],
            "servicios_disponibles": info_multas["servicios_disponibles"],
            "div_resultado": info_multas["div_resultado"],
            "mensaje": "Consulta realizada exitosamente"
        }
        
    except TimeoutException as e:
        return {
            "status": "error",
            "documento_placa": documento_placa,
            "tiene_multas": False,
            "mensaje_principal": "",
            "servicios_disponibles": [],
            "div_resultado": "",
            "error": f"Timeout: La página tardó demasiado en cargar - {str(e)}",
            "mensaje": "Error de tiempo de espera"
        }
        
    except NoSuchElementException as e:
        return {
            "status": "error",
            "documento_placa": documento_placa,
            "tiene_multas": False,
            "mensaje_principal": "",
            "servicios_disponibles": [],
            "div_resultado": "",
            "error": f"Elemento no encontrado: {str(e)}",
            "mensaje": "Error en la estructura de la página"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "documento_placa": documento_placa,
            "tiene_multas": False,
            "mensaje_principal": "",
            "servicios_disponibles": [],
            "div_resultado": "",
            "error": f"Error inesperado: {str(e)}",
            "mensaje": "Error general en la consulta"
        }
        
    finally:
        if driver:
            driver.quit()
            print("Navegador cerrado")

def generar_html_respuesta(resultado):
    """
    Genera HTML bonito para mostrar el resultado de la consulta de multas
    
    Returns:
        str: HTML formateado y responsivo
    """
    if resultado['status'] != 'success':
        return f"""
        <div class="alert alert-danger border-danger" style="border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle text-danger me-3" style="font-size: 24px;"></i>
                <div>
                    <h5 class="mb-1 text-danger">❌ Error en la consulta</h5>
                    <p class="mb-0">No fue posible consultar las multas para <strong>{resultado['documento_placa']}</strong></p>
                    <small class="text-muted">{resultado.get('error', 'Error desconocido')}</small>
                </div>
            </div>
        </div>
        """
    
    # Determinar el estilo según si tiene multas o no
    if resultado['tiene_multas']:
        alert_class = "alert-warning border-warning"
        icon = "🚨"
        icon_class = "fas fa-exclamation-triangle text-warning"
        title = "Multas pendientes encontradas"
        status_text = "SÍ tiene multas pendientes"
        bg_color = "#fff3cd"
    else:
        alert_class = "alert-success border-success"
        icon = "✅"
        icon_class = "fas fa-check-circle text-success"
        title = "Sin multas pendientes"
        status_text = "NO tiene multas pendientes"
        bg_color = "#d1edff"
    
    # Construir HTML
    html = f"""
    <div class="card border-0" style="border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); overflow: hidden;">
        <!-- Header -->
        <div class="card-header text-center" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 20px;">
            <h4 class="mb-2" style="font-weight: 600;">
                <i class="fas fa-car me-2"></i>
                Consulta de Multas - Tránsito Atlántico
            </h4>
            <p class="mb-0 opacity-75">Documento/Placa: <strong>{resultado['documento_placa']}</strong></p>
        </div>
        
        <!-- Resultado principal -->
        <div class="card-body p-0">
            <div class="alert {alert_class} m-3" style="border-radius: 10px; background-color: {bg_color}; border-width: 2px;">
                <div class="d-flex align-items-center">
                    <i class="{icon_class} me-3" style="font-size: 28px;"></i>
                    <div class="flex-grow-1">
                        <h5 class="mb-1" style="font-weight: 600;">{icon} {title}</h5>
                        <p class="mb-1">El vehículo/conductor <strong>{status_text}</strong></p>
                        {f'<p class="mb-0 text-muted" style="font-size: 14px;">{resultado["mensaje_principal"]}</p>' if resultado["mensaje_principal"] else ''}
                    </div>
                </div>
            </div>
    """
    
    # Agregar servicios disponibles si existen
    if resultado['servicios_disponibles']:
        html += f"""
            <div class="mx-3 mb-3">
                <div class="card border-light" style="border-radius: 10px; background-color: #f8f9fa;">
                    <div class="card-body p-3">
                        <h6 class="mb-3" style="color: #495057; font-weight: 600;">
                            <i class="fas fa-tools text-primary me-2"></i>
                            Servicios disponibles en el portal:
                        </h6>
                        <div class="row">
        """
        
        # Mostrar servicios en columnas
        for i, servicio in enumerate(resultado['servicios_disponibles'][:6]):  # Máximo 6 servicios
            html += f"""
                            <div class="col-md-6 mb-2">
                                <small class="d-flex align-items-start">
                                    <i class="fas fa-check-circle text-success me-2 mt-1" style="font-size: 12px;"></i>
                                    {servicio}
                                </small>
                            </div>
            """
        
        if len(resultado['servicios_disponibles']) > 6:
            html += f"""
                            <div class="col-12">
                                <small class="text-muted">
                                    <i class="fas fa-plus-circle me-1"></i>
                                    Y {len(resultado['servicios_disponibles']) - 6} servicios más disponibles...
                                </small>
                            </div>
            """
        
        html += """
                        </div>
                    </div>
                </div>
            </div>
        """
    
    # Footer con enlace al portal
    html += f"""
        </div>
        
        <!-- Footer -->
        <div class="card-footer text-center border-0" style="background-color: #f8f9fa; padding: 15px;">
            <a href="https://digital.transitodelatlantico.gov.co/portal-servicios/#/public" 
               target="_blank" 
               class="btn btn-primary btn-sm"
               style="border-radius: 20px; padding: 8px 20px; font-weight: 500; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none;">
                <i class="fas fa-external-link-alt me-2"></i>
                Visitar Portal Oficial
            </a>
            <div class="mt-2">
                <small class="text-muted">
                    <i class="fas fa-info-circle me-1"></i>
                    Consulta realizada el {time.strftime('%d/%m/%Y a las %H:%M', time.localtime())}
                </small>
            </div>
        </div>
    </div>
    
    <style>
        @media (max-width: 768px) {{
            .card {{
                margin: 0 5px;
            }}
            .alert {{
                margin: 15px !important;
            }}
            .card-header h4 {{
                font-size: 18px;
            }}
        }}
    </style>
    """
    
    return html

def search_traffic_fines(documento_placa: int, user_id: int, status: str) -> Dict:
    """
    Función principal para NAIA que retorna JSON con HTML display
    
    Args:
        documento_placa (str): Número de identificación o placa del vehículo
        
    Returns:
        dict: JSON con llave "display" conteniendo HTML bonito
    """
    try:
        # Realizar la consulta
        set_status(user_id, status, 7)
        resultado = consultar_multas_transito_atlantico(documento_placa)
        
        # Generar HTML bonito
        html_display = generar_html_respuesta(resultado)
        
        # Retornar en formato JSON para NAIA
        return {
            "display": html_display,
            "status": resultado['status'],
            "tiene_multas": resultado.get('tiene_multas', False),
            "documento_placa": documento_placa
        }
        
    except Exception as e:
        # HTML de error
        error_html = f"""
        <div class="alert alert-danger border-danger" style="border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle text-danger me-3" style="font-size: 24px;"></i>
                <div>
                    <h5 class="mb-1 text-danger">❌ Error en la consulta</h5>
                    <p class="mb-0">No fue posible consultar las multas para <strong>{documento_placa}</strong></p>
                    <small class="text-muted">Error: {str(e)}</small>
                </div>
            </div>
        </div>
        """
        
        return {
            "display": error_html,
            "status": "error",
            "tiene_multas": False,
            "documento_placa": documento_placa
        }
  
