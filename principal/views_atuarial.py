from django.http import HttpResponse
from django.shortcuts import render
from decimal import Decimal
from datetime import date
from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile
import csv
import json
from pathlib import Path
from django.db.models import OuterRef, Subquery

from .atuarial import LAYOUTS, analyze_file, build_liquidated_line, build_summary_line, parse_line
from .models import Contrato, Mutuario, ParcelaContrato


MAX_UPLOAD_SIZE = 20 * 1024 * 1024


def _digits(value):
    return "".join(char for char in str(value or "") if char.isdigit())


def _date_text(value, fallback="00000000"):
    return value.strftime("%Y%m%d") if value else fallback


def _municipality_map():
    result = {}
    path = Path(__file__).resolve().parent.parent / "manual" / "Cadmut 00044 COFLUHAB.csv"
    if not path.exists():
        return result
    with path.open(encoding="latin-1", newline="") as handle:
        for row in csv.reader(handle, delimiter=";"):
            if len(row) > 9:
                contract = _digits(row[9])
                municipality = _digits(row[6])
                if contract and municipality:
                    result[str(int(contract))] = municipality.zfill(5)
    return result


def _historical_lq(upload):
    if not upload:
        return {}
    records = {}
    for line in upload.read().decode("latin-1").splitlines():
        values, errors = parse_line(line.rstrip("\r"), "LQ")
        contract = _digits(values.get("numero_contrato")) if not errors else ""
        if contract:
            records[str(int(contract))] = values
    return records


def _fcvs_residual_cache():
    path = Path(__file__).resolve().parent.parent / "fcvs_dashboard_cache.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {
        int(item["id"]): Decimal(str(item.get("fcvs_residual", 0)))
        for item in data.get("contratos", [])
        if item.get("id") is not None
    }


def _generate_lq_package(request):
    position = f"{request.POST.get('ano', '2026')}06"
    matricula = _digits(request.POST.get("matricula", "000442"))[-6:].zfill(6)
    fgts = request.POST.get("fgts", "2")
    hipoteca = request.POST.get("hipoteca", "1")
    lei = request.POST.get("lei_10150", "2")
    historical = _historical_lq(request.FILES.get("historico_lq"))
    residual_cache = _fcvs_residual_cache()
    municipality_map = _municipality_map()
    mutuarios = {str(m.codimovel).strip(): m for m in Mutuario.objects.all() if m.codimovel}
    latest_parcela = ParcelaContrato.objects.filter(
        contrato_id=OuterRef("pk")
    ).order_by("-nmens")
    contracts = Contrato.objects.annotate(
        atuarial_sddev=Subquery(latest_parcela.values("sddev")[:1]),
        atuarial_dtpgto=Subquery(latest_parcela.values("dtpgto")[:1]),
        atuarial_dtvenc=Subquery(latest_parcela.values("dtvenc")[:1]),
    ).order_by("id")

    lines = []
    exceptions = []
    for contract in contracts:
        key_digits = _digits(contract.codigo)
        key = str(int(key_digits)) if key_digits else ""
        old = historical.get(key, {})
        mutuario = mutuarios.get(str(contract.cod_imovel).strip())
        dtpgto = contract.atuarial_dtpgto
        dtvenc = contract.atuarial_dtvenc
        event_date = dtpgto if dtpgto and dtpgto.year > 1900 else dtvenc
        if not event_date:
            event_date = contract.data_contrato
            exceptions.append((contract.codigo, "data_evento", "sem pagamento/vencimento; usado data do contrato"))
        saldo = residual_cache.get(contract.id)
        if saldo is None:
            saldo = Decimal("0")
            exceptions.append((contract.codigo, "sd_pos_cont", "residuo FCVS ausente na cache da Carteira FCVS; gerado como zero"))
        elif saldo <= Decimal("100"):
            exceptions.append((contract.codigo, "sd_pos_cont", "residuo FCVS abaixo do corte de R$ 100 da Carteira FCVS; gerado como zero"))
            saldo = Decimal("0")
        if saldo < 0:
            exceptions.append((contract.codigo, "sd_pos_cont", f"saldo original negativo {saldo}; convertido para positivo"))
        saldo_para_arquivo = abs(saldo)
        saldo_escalado = int((saldo_para_arquivo * Decimal("100")).quantize(Decimal("1")))
        if len(str(saldo_escalado)) > 9:
            exceptions.append((contract.codigo, "sd_pos_cont", f"saldo positivo {saldo_para_arquivo} excede o campo LQ; marcado como ERRO"))
            saldo_para_arquivo = str(saldo_escalado)[:5] + "ERRO"
        municipality = municipality_map.get(key) or old.get("codigo_municipio", "")
        if not municipality:
            exceptions.append((contract.codigo, "codigo_municipio", "nao localizado"))
        cpf = _digits(mutuario.cpf if mutuario else old.get("cpf", ""))
        if not cpf:
            exceptions.append((contract.codigo, "cpf", "nao localizado"))
        values = {
            "data_posicao": position,
            "matricula_af": matricula,
            "fgts": fgts,
            "tipo_evento": (contract.ocorrencia or old.get("tipo_evento") or "LIQ")[:3],
            "data_evento": _date_text(event_date),
            "numero_contrato": key_digits or old.get("numero_contrato", "0"),
            "hipoteca": hipoteca,
            "sd_pos_cont": saldo_para_arquivo,
            "sd_fcvs_lei_10150": lei,
            "taxa_juros": contract.tx_juros if contract.tx_juros is not None else Decimal(old.get("taxa_juros", "0")) / Decimal("10000"),
            "uf": (mutuario.uf if mutuario else old.get("uf", "")),
            "codigo_municipio": municipality or "0",
            "data_contrato": _date_text(contract.data_contrato) if contract.data_contrato else old.get("data_contrato", "0"),
            "cpf": cpf or "0",
        }
        lines.append(build_liquidated_line(values))

    summary = build_summary_line(position, matricula, "L", len(lines)) + "\n"
    package = BytesIO()
    with ZipFile(package, "w", ZIP_DEFLATED) as archive:
        archive.writestr(f"{matricula}LQ.TXT", "\n".join(lines) + "\n")
        archive.writestr(f"{matricula}RR.TXT", summary)
        issue_file = StringIO()
        writer = csv.writer(issue_file, delimiter=";")
        writer.writerow(("contrato", "campo", "observacao"))
        writer.writerows(exceptions)
        archive.writestr(f"{matricula}_EXCECOES.csv", issue_file.getvalue())
        archive.writestr(
            "LEIA-ME.txt",
            "Pacote preliminar de avaliacao atuarial FCVS. "
            "Conferir o arquivo de excecoes antes do envio a CAIXA.\n",
        )
    response = HttpResponse(package.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{matricula}_ATUARIAL_2026.zip"'
    return response


def relatorio_atuarial_fcvs(request):
    analyses = []
    upload_error = None

    if request.method == "POST":
        if request.POST.get("acao") == "gerar_lq":
            return _generate_lq_package(request)
        arquivos = request.FILES.getlist("arquivos")
        if not arquivos:
            upload_error = "Selecione pelo menos um arquivo TXT."
        else:
            for arquivo in arquivos:
                if arquivo.size > MAX_UPLOAD_SIZE:
                    analyses.append({
                        "filename": arquivo.name,
                        "layout": None,
                        "label": "Arquivo rejeitado",
                        "total_lines": 0,
                        "valid_lines": 0,
                        "invalid_lines": 0,
                        "records": [],
                        "errors": [{
                            "line": 0,
                            "messages": ["arquivo maior que 20 MB"],
                        }],
                        "warnings": [],
                    })
                    continue
                analyses.append(analyze_file(arquivo.name, arquivo.read()))

    total_sd_pos_cont = sum(
        (result.get("total_sd_pos_cont", Decimal("0")) for result in analyses),
        Decimal("0"),
    )

    return render(request, "principal/relatorio_atuarial_fcvs.html", {
        "analyses": analyses,
        "upload_error": upload_error,
        "layouts": LAYOUTS,
        "total_sd_pos_cont": total_sd_pos_cont,
    })
