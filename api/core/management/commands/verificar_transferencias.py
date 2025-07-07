import os
import csv
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from api.gpt4.models import Transfer
from api.gpt4.utils import (
    generar_xml_pain001,
    generar_archivo_aml,
    obtener_ruta_schema_transferencia,
    registrar_log
)

class Command(BaseCommand):
    help = "🔍 Verifica la integridad de transferencias SEPA: archivos XML y logs."

    def add_arguments(self, parser):
        parser.add_argument('-f', '--fix', action='store_true', help='Intentar regenerar los archivos XML y AML faltantes')
        parser.add_argument('-d', '--only-db', action='store_true', help='Verificar solo base de datos (sin archivos)')
        parser.add_argument('-F', '--only-files', action='store_true', help='Verificar solo archivos (sin DB)')
        parser.add_argument('-c', '--csv', action='store_true', help='Exportar resultados a resumen_transferencias.csv')
        parser.add_argument('-j', '--json', action='store_true', help='Exportar resultados a resumen_transferencias.json')

    def handle(self, *args, **options):
        transferencias = Transfer.objects.all()

        if not transferencias.exists():
            self.stdout.write(self.style.WARNING("⚠️  No hay transferencias registradas."))
            self.stdout.write("ℹ️  Usa -h para ver las opciones disponibles.")
            return

        resumen = []
        base_dir = os.path.join("schemas", "transferencias")
        os.makedirs(base_dir, exist_ok=True)

        self.stdout.write(self.style.NOTICE("🔎 Iniciando verificación de transferencias...\n"))

        for idx, t in enumerate(transferencias):
            letra = chr(ord('A') + idx)
            payment_id = str(t.payment_id)
            carpeta = obtener_ruta_schema_transferencia(payment_id)
            faltan = []

            if not options['only-db']:
                xml_path = os.path.join(carpeta, f"pain001_{payment_id}.xml")
                aml_path = os.path.join(carpeta, f"aml_{payment_id}.xml")
                log_path = os.path.join(carpeta, f"transferencia_{payment_id}.log")

                if not os.path.exists(xml_path):
                    faltan.append("pain001")
                    if options['fix']:
                        try:
                            generar_xml_pain001(t, payment_id)
                            self.stdout.write(self.style.SUCCESS(f"✅ [AUTO] XML generado para {payment_id}"))
                        except Exception as e:
                            registrar_log(payment_id, tipo_log='ERROR', error=str(e), extra_info='Fallo regenerando pain001')
                            self.stdout.write(self.style.ERROR(f"❌ Error generando XML para {payment_id}: {e}"))

                if not os.path.exists(aml_path):
                    faltan.append("aml")
                    if options['fix']:
                        try:
                            generar_archivo_aml(t, payment_id)
                            self.stdout.write(self.style.SUCCESS(f"✅ [AUTO] AML generado para {payment_id}"))
                        except Exception as e:
                            registrar_log(payment_id, tipo_log='ERROR', error=str(e), extra_info='Fallo regenerando AML')
                            self.stdout.write(self.style.ERROR(f"❌ Error generando AML para {payment_id}: {e}"))

                if not os.path.exists(log_path):
                    faltan.append("log")

            resumen.append({
                "Letra": letra,
                "Transferencia": payment_id,
                "Faltan": ", ".join(faltan) if faltan else "✅"
            })

        # Mostrar resumen
        self.stdout.write("\n📋 Resumen:")
        for r in resumen:
            self.stdout.write(f"{r['Letra']}. {r['Transferencia']} - {r['Faltan']}")

        if options['csv']:
            csv_path = os.path.join(base_dir, "resumen_transferencias.csv")
            with open(csv_path, "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["Letra", "Transferencia", "Faltan"])
                writer.writeheader()
                writer.writerows(resumen)
            self.stdout.write(self.style.SUCCESS(f"\n📄 CSV generado en {csv_path}"))

        if options['json']:
            json_path = os.path.join(base_dir, "resumen_transferencias.json")
            with open(json_path, "w") as f:
                json.dump(resumen, f, indent=4)
            self.stdout.write(self.style.SUCCESS(f"📄 JSON generado en {json_path}"))

        self.stdout.write(self.style.SUCCESS("\n✅ Verificación completada.\n"))
