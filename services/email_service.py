from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, Any

class EmailService:
    def __init__(self):
        self.from_email = f"NAIA Uninorte <{settings.DEFAULT_FROM_EMAIL}>"
        self.templates = {
            'welcome': {
                'subject': '🎓 ¡Bienvenido a NAIA Uninorte! - Tu Asistente Académico Inteligente',
                'message': '''¡Hola {name}!

¡Te damos la más cordial bienvenida a NAIA Uninorte! 🎉

Nos complace informarte que tu registro ha sido exitoso y ahora formas parte de nuestra comunidad académica digital.

🤖 ¿Qué es NAIA Uninorte?
NAIA (Navegador de Asistencia Inteligente Académica) es tu asistente virtual especializado en la Universidad del Norte, diseñado para acompañarte durante toda tu experiencia universitaria.

✨ Con NAIA puedes:
• Obtener información académica y administrativa
• Consultar horarios y calendarios universitarios
• Recibir orientación sobre trámites y procedimientos
• Acceder a recursos y servicios del campus
• Resolver dudas sobre la vida universitaria

🚀 Próximos pasos:
1. Explora las funcionalidades disponibles
2. Realiza tu primera consulta
3. Personaliza tu experiencia según tus necesidades

💡 Recuerda que NAIA está disponible 24/7 para ayudarte en tu camino académico.

Si tienes alguna pregunta o necesitas asistencia, no dudes en contactarnos.

¡Bienvenido a la familia NAIA Uninorte!

---
🏛️ Universidad del Norte
🤖 NAIA - Tu Asistente Académico Inteligente
📧 Equipo NAIA Uninorte'''
            },
            'reset_password': {
                'subject': 'NAIA Uninorte - Recuperación de Contraseña',
                'message': '''¡Hola!

Has solicitado recuperar tu contraseña para acceder a NAIA Uninorte.

'''
            },
            'verification': {
                'subject': 'NAIA Uninorte - Verifica tu Cuenta',
                'message': '''Por favor verifica tu cuenta para continuar.'''
            }
        }

    def send_email(self, recipient_email: str, template_type: str, name: str = None) -> Dict[str, Any]:
        try:
            if template_type not in self.templates:
                raise ValueError(f"Template type '{template_type}' not found")

            template = self.templates[template_type]
            message = template['message']
            
            if name:
                message = message.format(name=name)
            
            send_mail(
                subject=template['subject'],
                message=message,
                from_email=self.from_email,
                recipient_list=[recipient_email],
                fail_silently=False
            )
            
            return {
                "status": "success",
                "message": "Correo enviado exitosamente"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error al enviar el correo: {str(e)}"
            }