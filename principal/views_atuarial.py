from django.shortcuts import render
from decimal import Decimal

from .atuarial import LAYOUTS, analyze_file


MAX_UPLOAD_SIZE = 20 * 1024 * 1024


def relatorio_atuarial_fcvs(request):
    analyses = []
    upload_error = None

    if request.method == "POST":
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
