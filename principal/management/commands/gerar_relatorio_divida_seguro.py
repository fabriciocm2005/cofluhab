from __future__ import annotations

import os
import subprocess
import sys

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Gera relatorio de divida/seguro consolidado ou por ano"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ano",
            type=int,
            default=None,
            help="Ano especifico (ex: 1992). Omitido = consolidado historico completo (1992+)",
        )
        parser.add_argument(
            "--tipo",
            choices=["ALL", "CAD", "RIE", "RMO"],
            default="ALL",
            help="Processa apenas um tipo de relatorio",
        )
        parser.add_argument(
            "--max-pdfs",
            type=int,
            default=None,
            help="Limite de PDFs por tipo (debug/performance)",
        )

    def handle(self, *args, **options):
        ano = options.get("ano")
        tipo = options.get("tipo")
        max_pdfs = options.get("max_pdfs")

        app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        script_path = os.path.join(app_root, "scripts", "gerar_relatorio_divida_seguro_v2.py")
        preferred_python = os.path.abspath(os.path.join(app_root, "..", "venv_django", "Scripts", "python.exe"))
        python_exec = preferred_python if os.path.isfile(preferred_python) else sys.executable

        if not os.path.isfile(script_path):
            raise CommandError(f"Script nao encontrado: {script_path}")

        cmd = [python_exec, script_path]
        if ano:
            cmd.extend(["--ano", str(ano)])
        if tipo:
            cmd.extend(["--tipo", tipo])
        if max_pdfs:
            cmd.extend(["--max-pdfs", str(max_pdfs)])

        self.stdout.write(self.style.NOTICE("Executando gerador de relatorio de divida/seguro..."))
        run = subprocess.run(cmd, cwd=app_root, capture_output=True, text=True, check=False)

        if run.stdout:
            self.stdout.write(run.stdout)
        if run.stderr:
            self.stderr.write(run.stderr)

        if run.returncode != 0:
            raise CommandError(f"Geracao falhou (codigo {run.returncode})")

        self.stdout.write(self.style.SUCCESS("Relatorio gerado com sucesso."))
