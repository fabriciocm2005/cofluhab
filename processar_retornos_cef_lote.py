"""
Processador em lote de retornos CEF (CADMUT1, M3026xx, Sxxxxxx)

Objetivo:
- Detectar codigo do arquivo pelo nome
- Aplicar parser adequado
- Gerar consolidado unico (CSV + Markdown)
- Comparar remessas por hash de conteudo

Uso:
  python processar_retornos_cef_lote.py --dir manual/00044
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from principal.ficha_return_interpreter import interpretar_retorno_cadmut, interpretar_retorno_fcvs
from principal.ficha_p3026_parser_v2 import ParserP3026


def detectar_codigo(nome_arquivo: str) -> str:
    m = re.search(r"MICP\.FCVS\.([^.]+)\.A", (nome_arquivo or "").upper())
    return m.group(1) if m else "DESCONHECIDO"


def detectar_data_remessa(nome_arquivo: str) -> str:
    m = re.search(r"\.D(\d{6})\.H", nome_arquivo.upper())
    if not m:
        return ""
    txt = m.group(1)  # DDMMAA
    try:
        return datetime.strptime(txt, "%d%m%y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def hash_arquivo(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def processar_s_textual(path: Path) -> Dict[str, int]:
    linhas_total = 0
    totalizadores = 0
    with path.open("r", encoding="latin-1", errors="ignore") as f:
        for ln in f:
            linhas_total += 1
            if re.search(r"\bTOTAL\b|\bTOTAIS\b|\bTOTALIZ", ln, re.IGNORECASE):
                totalizadores += 1
    return {
        "linhas_total": linhas_total,
        "totalizadores_encontrados": totalizadores,
    }


def processar_arquivo(path: Path, parser_p3026: ParserP3026) -> Dict[str, str]:
    nome = path.name
    codigo = detectar_codigo(nome)
    data_remessa = detectar_data_remessa(nome)
    h = hash_arquivo(path)

    base = {
        "arquivo": nome,
        "codigo": codigo,
        "data_remessa": data_remessa,
        "hash_sha256": h,
        "tipo_detectado": "",
        "layout_usado": "manual_atual",
        "status": "OK",
        "linhas_total": "",
        "movimentos": "",
        "rejeitados": "",
        "totalizadores_encontrados": "",
        "registros_p3026": "",
        "avisos_parser": "",
        "primeiro_aviso": "",
    }

    try:
        if codigo == "CADMUT1":
            rel = interpretar_retorno_cadmut(str(path))
            resumo = rel.get("resumo", {})
            base.update(
                {
                    "tipo_detectado": "CADMUT1",
                    "linhas_total": str(resumo.get("total_registros", 0)),
                    "movimentos": str(resumo.get("movimentos", 0)),
                    "rejeitados": str(resumo.get("registros_rejeitados", 0)),
                }
            )

        elif codigo.startswith("M3026"):
            arq, erros = parser_p3026.parse_arquivo(str(path))
            base.update(
                {
                    "tipo_detectado": "M3026xx/P3026",
                    "registros_p3026": str(len(arq.registros) if arq else 0),
                    "avisos_parser": str(len(erros)),
                    "primeiro_aviso": erros[0] if erros else "",
                }
            )

        elif codigo.startswith("S"):
            txt = processar_s_textual(path)
            base.update(
                {
                    "tipo_detectado": "Sxxxxxx/relatorio_textual",
                    "linhas_total": str(txt["linhas_total"]),
                    "totalizadores_encontrados": str(txt["totalizadores_encontrados"]),
                }
            )

        else:
            rel = interpretar_retorno_fcvs(str(path))
            resumo = rel.get("resumo", {})
            base.update(
                {
                    "tipo_detectado": "FCVS_fallback",
                    "linhas_total": str(resumo.get("total_registros", 0)),
                    "movimentos": str(resumo.get("movimentos", 0)),
                    "rejeitados": str(resumo.get("registros_rejeitados", 0)),
                    "layout_usado": "fallback_generico",
                }
            )

    except Exception as exc:
        base["status"] = "ERRO"
        base["primeiro_aviso"] = str(exc)

    return base


def comparar_remessas(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    por_codigo = defaultdict(list)
    for r in rows:
        por_codigo[r["codigo"]].append(r)

    comparativos: List[Dict[str, str]] = []
    for codigo, itens in sorted(por_codigo.items()):
        if len(itens) < 2:
            comparativos.append(
                {
                    "codigo": codigo,
                    "qtd_arquivos": str(len(itens)),
                    "conteudo": "sem_comparacao",
                    "datas": ", ".join(sorted(set(i.get("data_remessa", "") for i in itens if i.get("data_remessa")))),
                }
            )
            continue

        hashes = {i["hash_sha256"] for i in itens}
        comparativos.append(
            {
                "codigo": codigo,
                "qtd_arquivos": str(len(itens)),
                "conteudo": "igual" if len(hashes) == 1 else "diferente",
                "datas": ", ".join(sorted(set(i.get("data_remessa", "") for i in itens if i.get("data_remessa")))),
            }
        )

    return comparativos


def escrever_csv(path: Path, rows: List[Dict[str, str]], campos: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in campos})


def escrever_relatorio_md(path: Path, rows: List[Dict[str, str]], comp: List[Dict[str, str]], pasta: str) -> None:
    total = len(rows)
    por_tipo = defaultdict(int)
    for r in rows:
        por_tipo[r.get("tipo_detectado", "")] += 1

    linhas = []
    linhas.append("# Relatorio consolidado de retornos CEF")
    linhas.append("")
    linhas.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    linhas.append(f"Pasta analisada: {pasta}")
    linhas.append(f"Total de arquivos: {total}")
    linhas.append("")
    linhas.append("## Inventario por tipo detectado")
    for tipo, qtd in sorted(por_tipo.items()):
        linhas.append(f"- {tipo}: {qtd}")

    linhas.append("")
    linhas.append("## Comparacao entre remessas por codigo")
    for c in comp:
        linhas.append(
            f"- {c['codigo']}: {c['conteudo']} (arquivos={c['qtd_arquivos']}, datas={c['datas']})"
        )

    linhas.append("")
    linhas.append("## Observacoes")
    linhas.append("- M3026xx: utilizar parser P3026 v2 (nao parser generico FCVS).")
    linhas.append("- Sxxxxxx: leitura textual com totalizadores; parser semantico por codigo pode evoluir.")
    linhas.append("- Layout usado por movimento fica marcado no consolidado CSV.")

    path.write_text("\n".join(linhas), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="manual/00044", help="Pasta de retornos")
    ap.add_argument("--out", default="manual/00044", help="Pasta de saida")
    args = ap.parse_args()

    pasta = Path(args.dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if not pasta.exists():
        raise FileNotFoundError(f"Pasta nao encontrada: {pasta}")

    parser_p3026 = ParserP3026()
    arquivos = [p for p in sorted(pasta.iterdir()) if p.is_file() and not p.name.lower().endswith(".md")]

    rows: List[Dict[str, str]] = []
    for p in arquivos:
        rows.append(processar_arquivo(p, parser_p3026))

    comp = comparar_remessas(rows)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_consolidado = out / f"CONSOLIDADO_RETORNOS_CEF_{ts}.csv"
    csv_comparacao = out / f"COMPARACAO_REMESSAS_CEF_{ts}.csv"
    md_relatorio = out / f"RELATORIO_CONSOLIDADO_CEF_{ts}.md"

    campos_consolidado = [
        "arquivo", "codigo", "data_remessa", "hash_sha256", "tipo_detectado", "layout_usado", "status",
        "linhas_total", "movimentos", "rejeitados", "totalizadores_encontrados", "registros_p3026",
        "avisos_parser", "primeiro_aviso",
    ]
    escrever_csv(csv_consolidado, rows, campos_consolidado)
    escrever_csv(csv_comparacao, comp, ["codigo", "qtd_arquivos", "conteudo", "datas"])
    escrever_relatorio_md(md_relatorio, rows, comp, str(pasta).replace("\\", "/"))

    print(f"OK: {csv_consolidado}")
    print(f"OK: {csv_comparacao}")
    print(f"OK: {md_relatorio}")


if __name__ == "__main__":
    main()
