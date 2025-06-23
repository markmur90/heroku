import json
import uuid
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from jwcrypto import jwk

from api.gpt4.models import ClaveGenerada
from api.configuraciones_api.models import ConfiguracionAPI
from api.gpt4.utils import get_project_path


class Command(BaseCommand):
    help = "Genera clave privada ECDSA P-256, clave pública y JWKS para client_assertion OAuth2"

    def handle(self, *args, **kwargs):
        keys_dir = Path(get_project_path("/home/markmur88/scripts/schemas/keys"))
        logs_dir = Path(get_project_path("/home/markmur88/scripts/schemas/keys/logs"))
        settings_path = Path(get_project_path("/home/markmur88/api_bank_h2/config/settings/base1.py"))
        log_file = Path(get_project_path("/home/markmur88/scripts/schemas/keys/logs/clave_gen.log"))
        usuario_path = Path(get_project_path("/home/markmur88/scripts/schemas/keys/client_id.key"))

        keys_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        if not usuario_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo {usuario_path}")

        usuario = usuario_path.read_text(encoding="utf-8").strip()
        if not usuario:
            raise ValueError("El archivo client_id.key está vacío. No se puede continuar sin un usuario válido.")

        files = {
            "private": keys_dir / "ecdsa_private_key.pem",
            "public": keys_dir / "ecdsa_public_key.pem",
            "jwks": keys_dir / "jwks_public.json"
        }

        try:
            existentes = [f for f in files.values() if f.exists()]
            if existentes:
                self.stdout.write(self.style.WARNING("⚠️  Ya existen los siguientes archivos:"))
                for f in existentes:
                    self.stdout.write(f"  - {f}")
                confirm = input("¿Deseas sobrescribirlos? (sí/no): ").strip().lower()
                if confirm not in ("si", "sí", "s", "yes", "y"):
                    ClaveGenerada.objects.create(usuario=usuario, estado="CANCELADO")
                    self.stdout.write(self.style.NOTICE("🛑 Operación cancelada. Registro creado en la base de datos."))
                    return

            private_key = ec.generate_private_key(ec.SECP256R1())
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            files["private"].write_bytes(private_pem)
            self.stdout.write(self.style.SUCCESS(f"✅ Clave privada: {files['private']}"))

            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            files["public"].write_bytes(public_pem)
            self.stdout.write(self.style.SUCCESS(f"✅ Clave pública: {files['public']}"))

            kid = str(uuid.uuid4())
            jwk_key = jwk.JWK.from_pem(public_pem)
            jwk_key.update({"alg": "ES256", "use": "sig", "kid": kid})
            jwks = {"keys": [json.loads(jwk_key.export(private_key=False))]}
            files["jwks"].write_text(json.dumps(jwks, indent=2))
            self.stdout.write(self.style.SUCCESS(f"✅ JWKS generado con kid={kid}: {files['jwks']}"))

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "usuario": usuario,
                "archivos": {k: str(v) for k, v in files.items()},
                "kid": kid
            }
            with open(log_file, "a", encoding="utf-8") as lf:
                lf.write(json.dumps(log_entry, indent=2) + "\n")
            self.stdout.write(self.style.SUCCESS(f"📝 Log escrito en: {log_file}"))

            # Preparar contenido para guardar
            private_pem_str = private_pem.decode()
            public_pem_str = public_pem.decode()
            jwks_data = json.loads(files["jwks"].read_text(encoding="utf-8"))

            # Guardar en ClaveGenerada
            registro = ClaveGenerada(
                usuario=usuario,
                estado="EXITO",
                kid=kid,
                path_privada=str(files["private"]),
                path_publica=str(files["public"]),
                path_jwks=str(files["jwks"]),
                clave_privada=private_pem_str,
                clave_publica=public_pem_str,
                jwks=jwks_data
            )

            registro.archivo_privado.save(f"priv_{kid}.pem", ContentFile(private_pem))
            registro.archivo_publico.save(f"pub_{kid}.pem", ContentFile(public_pem))
            registro.archivo_jwks.save(f"jwks_{kid}.json", ContentFile(json.dumps(jwks_data, indent=2)))
            registro.save()

            # Guardar variables en ConfiguracionAPI
            def guardar_en_configuracion_api(nombre, valor, entorno='production'):
                ConfiguracionAPI.objects.update_or_create(
                    nombre=nombre,
                    entorno=entorno,
                    defaults={'valor': valor, 'activo': True}
                )

            guardar_en_configuracion_api('PRIVATE_KEY_PATH', str(files["private"]))
            guardar_en_configuracion_api('PRIVATE_KEY_KID', kid)

            # # Actualizar settings/base1.py
            # if settings_path.exists():
            #     with open(settings_path, "r", encoding="utf-8") as f:
            #         lines = f.readlines()

            #     key_path_line = f"PRIVATE_KEY_PATH = os.path.join(BASE_DIR, 'keys', 'ecdsa_private_key.pem')\n"
            #     kid_line = f"PRIVATE_KEY_KID = '{kid}'\n"

            #     found_key_path = any("PRIVATE_KEY_PATH" in l for l in lines)
            #     found_kid = any("PRIVATE_KEY_KID" in l for l in lines)

            #     if found_key_path:
            #         lines = [key_path_line if "PRIVATE_KEY_PATH" in l else l for l in lines]
            #     else:
            #         lines.append("\n" + key_path_line)

            #     if found_kid:
            #         lines = [kid_line if "PRIVATE_KEY_KID" in l else l for l in lines]
            #     else:
            #         lines.append(kid_line)

            #     with open(settings_path, "w", encoding="utf-8") as f:
            #         f.writelines(lines)

            #     self.stdout.write(self.style.SUCCESS(f"🛠️ base1.py actualizado con ruta y KID."))
            # else:
            #     self.stdout.write(self.style.WARNING("⚠️ No se encontró base1.py para actualizar KID."))

        except Exception as e:
            ClaveGenerada.objects.create(usuario=usuario, estado="ERROR", mensaje_error=str(e))
            self.stdout.write(self.style.ERROR(f"❌ Error durante ejecución: {e}"))
            raise

        jwks_data = json.loads(files["jwks"].read_text(encoding="utf-8"))
        jwks_keys = jwks_data.get("keys", [])
        jwks_kids = [k.get("kid") for k in jwks_keys]

        if kid not in jwks_kids:
            raise ValueError(f"❌ El KID '{kid}' no aparece en el JWKS generado.")
        if len(jwks_keys) > 1:
            raise ValueError(f"⚠️ JWKS contiene múltiples claves ({len(jwks_keys)}). Solo debe haber una clave activa.")

        self.stdout.write(self.style.SUCCESS(f"🔐 Verificación JWKS completada: KID único '{kid}' ✅"))
