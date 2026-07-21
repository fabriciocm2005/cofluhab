import os
import re
import unicodedata
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')

import django

django.setup()

from principal.models import Contrato, Mutuario
from principal.views import _aplicar_modo_importacao, _aplicar_modo_mutuario, _vincular_contrato_mutuario

CONJUNTO = '13'
CHECKPOINT = Path(r'c:\Users\fabri\cofluhab\cofluhab\exports\ocr_itaipava_checkpoint.json')


def _digits(value):
    return re.sub(r'\D+', '', str(value or ''))


def _name_key(value):
    txt = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode('ascii')
    txt = re.sub(r'\s+', ' ', txt).strip().lower()
    return txt


def _campos_contrato(contrato):
    return {
        'codigo': contrato.codigo,
        'conjunto': contrato.conjunto,
        'data_contrato': contrato.data_contrato,
        'ocorrencia': contrato.ocorrencia,
        'cod_imovel': contrato.cod_imovel,
        'chave': contrato.chave,
        'lote': contrato.lote,
        'sinal': contrato.sinal,
        'vlfinanc': contrato.vlfinanc,
        'vlprop': contrato.vlprop,
        'prestacao_inicial': contrato.prestacao_inicial,
        'prazo': contrato.prazo,
        'data_primeiro_venc': contrato.data_primeiro_venc,
        'sa': contrato.sa,
        'tx_juros': contrato.tx_juros,
        'cat_prof': contrato.cat_prof,
        'pr': contrato.pr,
    }


def _campos_mutuario(mutuario, codigo_destino):
    return {
        'codigo': codigo_destino,
        'codimovel': mutuario.codimovel,
        'conjunto': mutuario.conjunto,
        'conjseg': mutuario.conjseg,
        'nome': mutuario.nome,
        'ident': mutuario.ident,
        'orgao': mutuario.orgao,
        'dtnasc': mutuario.dtnasc,
        'cpf': mutuario.cpf,
        'endereco': mutuario.endereco,
        'numero': mutuario.numero,
        'compl': mutuario.compl,
        'tipoimovel': mutuario.tipoimovel,
        'bairro': mutuario.bairro,
        'cidade': mutuario.cidade,
        'cep': mutuario.cep,
        'uf': mutuario.uf,
    }


def _buscar_codigo_real(prov_mutuario):
    prov_cpf = _digits(prov_mutuario.cpf)
    prov_name = _name_key(prov_mutuario.nome)

    candidatos = Mutuario.objects.filter(conjunto=CONJUNTO).exclude(codigo__startswith='PROV_')

    for cand in candidatos:
        ccpf = _digits(cand.cpf)
        cname = _name_key(cand.nome)
        cpf_match = bool(prov_cpf and ccpf and (prov_cpf == ccpf or prov_cpf.startswith(ccpf) or ccpf.startswith(prov_cpf)))
        name_match = bool(prov_name and cname and prov_name == cname)
        if cpf_match or name_match:
            return cand.codigo

    return ''


def reconciliar():
    total = 0
    mapping = {}
    for prov_mut in Mutuario.objects.filter(conjunto=CONJUNTO, codigo__startswith='PROV_'):
        codigo_real = _buscar_codigo_real(prov_mut)
        if not codigo_real:
            continue

        contrato_real = Contrato.objects.filter(codigo=codigo_real).first()
        contrato_prov = Contrato.objects.filter(codigo=prov_mut.codigo).first()
        mut_real = Mutuario.objects.filter(codigo=codigo_real).first()

        if not contrato_real or not mut_real:
            continue

        if contrato_prov:
            campos = _campos_contrato(contrato_prov)
            campos['codigo'] = codigo_real
            alterado = _aplicar_modo_importacao(contrato_real, campos, 'complementar_vazios', [])
            if alterado:
                contrato_real.save()

        campos_mut = _campos_mutuario(prov_mut, codigo_real)
        alterado_mut = _aplicar_modo_mutuario(mut_real, campos_mut, 'complementar_vazios', [])
        if alterado_mut:
            mut_real.save()

        _vincular_contrato_mutuario(contrato_real.id, mut_real.id)
        mapping[prov_mut.codigo] = codigo_real

        # Remove duplicata provisoria para nao continuar poluindo listagens e checks.
        if contrato_prov:
            contrato_prov.delete()
        prov_mut.delete()
        total += 1
        print(f'RECONCILIADO: {prov_mut.codigo} -> {codigo_real}')

    if mapping and CHECKPOINT.exists():
        try:
            data = json.loads(CHECKPOINT.read_text(encoding='utf-8'))
            rows = data.get('rows', [])
            for row in rows:
                cod = str(row.get('codigo') or '').strip()
                if cod in mapping:
                    row['codigo'] = mapping[cod]
            CHECKPOINT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'CHECKPOINT_ATUALIZADO: {len(mapping)} codigo(s)')
        except Exception as exc:
            print(f'ERRO_CHECKPOINT: {exc}')

    print(f'TOTAL_RECONCILIADO: {total}')


if __name__ == '__main__':
    reconciliar()
