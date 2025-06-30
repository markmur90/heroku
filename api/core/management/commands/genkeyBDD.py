import json
import uuid
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from jwcrypto import jwk

from api.gpt4.models import ClaveGenerada
from api.configuraciones_api.models import ConfiguracionAPI

class Command(BaseCommand):
    help = "Genera clave privada ECDSA P-256, clave pública y JWKS para client_assertion OAuth2, solo en base de datos"

    def handle(self, *args, **kwargs):
        try:
            usuario = self.obtener_usuario()

            private_key = ec.generate_private_key(ec.SECP256R1())
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            kid = str(uuid.uuid4())
            jwk_key = jwk.JWK.from_pem(public_pem)
            jwk_key.update({"alg": "ES256", "use": "sig", "kid": kid})
            jwks = {"keys": [json.loads(jwk_key.export(private_key=False))]}

            # Guardar en base de datos
            registro = ClaveGenerada(
                usuario=usuario,
                estado="EXITO",
                kid=kid,
                clave_privada=private_pem.decode(),
                clave_publica=public_pem.decode(),
                jwks=jwks
            )
            registro.archivo_privado.save(f"priv_{kid}.pem", ContentFile(private_pem))
            registro.archivo_publico.save(f"pub_{kid}.pem", ContentFile(public_pem))
            registro.archivo_jwks.save(f"jwks_{kid}.json", ContentFile(json.dumps(jwks, indent=2)))
            registro.save()

            self.guardar_en_configuracion_api('PRIVATE_KEY_KID', kid)

            self.stdout.write(self.style.SUCCESS(f"🔐 Claves generadas y guardadas en base de datos para '{usuario}' con KID '{kid}'"))

        except Exception as e:
            ClaveGenerada.objects.create(usuario=usuario, estado="ERROR", mensaje_error=str(e))
            self.stdout.write(self.style.ERROR(f"❌ Error durante ejecución: {e}"))
            raise

    def obtener_usuario(self):
        # Aquí puedes reemplazar por una fuente válida de usuario
        from django.conf import settings
        return getattr(settings, "DEFAULT_USUARIO", "usuario_desconocido")

    def guardar_en_configuracion_api(self, nombre, valor, entorno='production'):
        ConfiguracionAPI.objects.update_or_create(
            nombre=nombre,
            entorno=entorno,
            defaults={'valor': valor, 'activo': True}
        )
