from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, Any

class EmailService:
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.templates = {
            'welcome': {
                'subject': 'Bienvenido a Nuestro Servicio!',
                'message': 'Hola {name} Gracias por registrarte. ¡Nos alegra tenerte con nosotros!'
            },
            'reset_password': {
                'subject': 'Recuperación de Contraseña',
                'message': 'Has solicitado un cambio de contraseña.'
            },
            'verification': {
                'subject': 'Verifica tu Cuenta',
                'message': 'Por favor verifica tu cuenta para continuar.'
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