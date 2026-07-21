import os
import csv
import json
import time
import re
import unicodedata
import concurrent.futures
from pathlib import Path
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')

import django

django.setup()

from pypdf import PdfReader, PdfWriter
from principal.models import Contrato, Mutuario
from principal.views import (
    _extrair_lote_ocr_por_pagina,
    _enriquecer_item_com_campos_raw_azure,
    _normalizar_campo_ocr,
    _inferir_numero_do_endereco,
    _ocr_item_sem_dados,
    _limpar_cpf,
    _valor_para_texto,
    _aplicar_complemento_manual_em_dados_ocr,
    _campos_contrato_por_dados_ocr,
    _aplicar_modo_importacao,
    _campos_mutuario_por_dados_ocr,
    _aplicar_modo_mutuario,
    _vincular_contrato_mutuario,
)

PDF_PATH = Path(r'c:\Users\fabri\cofluhab\cofluhab\manual\caixa 1 itaipava.pdf')
EXPORT_DIR = Path(r'c:\Users\fabri\cofluhab\cofluhab\exports')
CHECKPOINT = EXPORT_DIR / 'ocr_itaipava_checkpoint.json'
REPORT_CSV = EXPORT_DIR / f"ocr_itaipava_relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
CONJUNTO_OCR = '13'
MODO_IMPORTACAO = 'complementar_vazios'
CAMPOS_SOBRESCREVER = []

EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _digits(value):
    return re.sub(r'\D+', '', str(value or ''))


def _name_key(value):
    txt = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', txt).strip().lower()


def _resolver_codigo_real_no_conjunto(codigo, dados, conjunto_destino):
    cod = _valor_para_texto(codigo)
    if not cod.startswith('PROV_'):
        return cod

    cpf = _digits(dados.get('cpf', ''))
    if cpf:
        candidatos = Mutuario.objects.filter(conjunto=conjunto_destino).exclude(codigo__startswith='PROV_')
        for m in candidatos:
            cpf_m = _digits(m.cpf)
            if cpf_m and (cpf.startswith(cpf_m) or cpf_m.startswith(cpf)):
                return _valor_para_texto(m.codigo)

    nome = _name_key(dados.get('nome', ''))
    if nome:
        candidatos = Mutuario.objects.filter(conjunto=conjunto_destino).exclude(codigo__startswith='PROV_')
        for m in candidatos:
            if nome == _name_key(m.nome):
                return _valor_para_texto(m.codigo)

    return cod


def _extrair_lote_com_timeout(pdf_path, timeout_s=45):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_extrair_lote_ocr_por_pagina, pdf_path)
    try:
        return future.result(timeout=timeout_s)
    except concurrent.futures.TimeoutError as exc:
        future.cancel()
        raise TimeoutError(f'OCR timeout after {timeout_s}s') from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def load_checkpoint():
    if CHECKPOINT.exists():
        try:
            return json.loads(CHECKPOINT.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_checkpoint(data):
    CHECKPOINT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def process_item(item):
    _enriquecer_item_com_campos_raw_azure(item)
    dados = item.get('dados', {}) or {}
    # Garante que o código resolvido no wrapper também exista no payload de dados.
    if not _valor_para_texto(dados.get('codigo', '')):
        dados['codigo'] = _valor_para_texto(item.get('codigo', ''))
    dados['conjunto'] = CONJUNTO_OCR

    for campo in [
        'nome', 'cpf', 'endereco', 'numero', 'compl', 'bairro', 'cidade',
        'uf', 'cep', 'tipoimovel', 'vlfinanc', 'vlprop', 'prestacao_inicial',
        'prazo', 'ident', 'orgao', 'dtnasc', 'data_primeiro_venc',
        'sa', 'tx_juros', 'cat_prof', 'pr'
    ]:
        dados[campo] = _normalizar_campo_ocr(campo, dados.get(campo, ''))

    if not _valor_para_texto(dados.get('numero', '')):
        dados['numero'] = _inferir_numero_do_endereco(dados.get('endereco', ''))

    _aplicar_complemento_manual_em_dados_ocr(dados)
    item['sem_dados'] = _ocr_item_sem_dados(dados)

    if not item.get('codigo_valido'):
        return 'ignorado_codigo_invalido', None, dados

    conjunto_destino = _valor_para_texto(dados.get('conjunto', ''))
    campos_contrato = _campos_contrato_por_dados_ocr(dados, conjunto_destino)
    if not campos_contrato:
        return 'ignorado_sem_campos', None, dados

    codigo = campos_contrato['codigo']
    codigo_resolvido = _resolver_codigo_real_no_conjunto(codigo, dados, conjunto_destino)
    campos_contrato['codigo'] = codigo_resolvido
    codigo = codigo_resolvido
    contrato = Contrato.objects.filter(codigo=codigo).first()
    if contrato:
        alterado = _aplicar_modo_importacao(contrato, campos_contrato, MODO_IMPORTACAO, CAMPOS_SOBRESCREVER)
        if alterado:
            contrato.save()
            status_contrato = 'atualizado'
        else:
            status_contrato = 'inalterado'
    else:
        contrato = Contrato.objects.create(
            codigo=codigo,
            conjunto=campos_contrato.get('conjunto', ''),
            data_contrato=campos_contrato.get('data_contrato'),
            ocorrencia=campos_contrato.get('ocorrencia', ''),
            cod_imovel=campos_contrato.get('cod_imovel', ''),
            chave=campos_contrato.get('chave', ''),
            lote=campos_contrato.get('lote', ''),
            sinal=campos_contrato.get('sinal', ''),
            vlfinanc=campos_contrato.get('vlfinanc'),
            vlprop=campos_contrato.get('vlprop'),
            prestacao_inicial=campos_contrato.get('prestacao_inicial'),
            prazo=campos_contrato.get('prazo'),
            data_primeiro_venc=campos_contrato.get('data_primeiro_venc'),
            sa=campos_contrato.get('sa', ''),
            tx_juros=campos_contrato.get('tx_juros'),
            cat_prof=campos_contrato.get('cat_prof', ''),
            pr=campos_contrato.get('pr', ''),
        )
        status_contrato = 'criado'

    campos_mut = _campos_mutuario_por_dados_ocr(dados, codigo, conjunto_destino)
    mutuario = Mutuario.objects.filter(codigo=codigo).first()
    if not mutuario:
        mutuario = Mutuario.objects.create(
            codigo=campos_mut['codigo'],
            codimovel=campos_mut.get('codimovel', ''),
            conjunto=campos_mut.get('conjunto', ''),
            conjseg=campos_mut.get('conjseg', ''),
            nome=campos_mut.get('nome', ''),
            ident=campos_mut.get('ident', ''),
            orgao=campos_mut.get('orgao', ''),
            dtnasc=campos_mut.get('dtnasc'),
            cpf=campos_mut.get('cpf', ''),
            renda=0,
            crenda=0,
            endereco=campos_mut.get('endereco', ''),
            numero=campos_mut.get('numero', ''),
            compl=campos_mut.get('compl', ''),
            tipoimovel=campos_mut.get('tipoimovel', ''),
            bairro=campos_mut.get('bairro', ''),
            cidade=campos_mut.get('cidade', ''),
            cep=campos_mut.get('cep', ''),
            uf=campos_mut.get('uf', ''),
        )
    else:
        alterado_mut = _aplicar_modo_mutuario(mutuario, campos_mut, MODO_IMPORTACAO, CAMPOS_SOBRESCREVER)
        if alterado_mut:
            mutuario.save()

    _vincular_contrato_mutuario(contrato.id, mutuario.id)
    return status_contrato, codigo, dados


def main():
    cp = load_checkpoint()
    done = set(cp.get('done_pages', []))
    rows = cp.get('rows', [])

    reader = PdfReader(str(PDF_PATH))
    total = len(reader.pages)
    print(f'INICIO {PDF_PATH.name} paginas={total} ja_processadas={len(done)}')

    for idx in range(total):
        page_no = idx + 1
        if page_no in done:
            continue

        tmp = EXPORT_DIR / f'_tmp_itaipava_page_{page_no:03d}.pdf'
        status = 'falha'
        codigo = ''
        dados_snapshot = {}
        metodo = ''
        erro = ''

        for tentativa in range(3):
            try:
                writer = PdfWriter()
                writer.add_page(reader.pages[idx])
                with open(tmp, 'wb') as f:
                    writer.write(f)

                lote = _extrair_lote_com_timeout(tmp, timeout_s=45)
                if not lote:
                    status = 'sem_retorno'
                    break

                item = lote[0]
                item['pagina'] = page_no
                metodo = _valor_para_texto(item.get('metodo', ''))
                status, codigo, dados_snapshot = process_item(item)
                erro = ''
                break
            except Exception as e:
                erro = str(e)
                if 'timeout' in erro.lower():
                    wait_s = min(120, 30 * (tentativa + 1))
                    print(f'PAG {page_no}: timeout tentativa {tentativa+1}/3, aguardando {wait_s}s')
                    time.sleep(wait_s)
                    continue
                if '429' in erro:
                    wait_s = min(120, 30 * (tentativa + 1))
                    print(f'PAG {page_no}: 429 tentativa {tentativa+1}/3, aguardando {wait_s}s')
                    time.sleep(wait_s)
                    continue
                if 'InvalidContentLength' in erro:
                    status = 'falha_tamanho'
                    break
                status = 'falha'
                break
            finally:
                try:
                    if tmp.exists():
                        tmp.unlink()
                except Exception:
                    pass

        rows.append({
            'pagina': page_no,
            'status': status,
            'codigo': codigo,
            'dados': dados_snapshot,
            'metodo': metodo,
            'erro': erro[:240],
        })
        done.add(page_no)
        save_checkpoint({'done_pages': sorted(done), 'rows': rows})
        print(f'PAG {page_no}/{total}: {status} codigo={codigo}')

        # pacing conservador para reduzir 429 em contas com baixa cota
        time.sleep(12)

    with REPORT_CSV.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['pagina', 'status', 'codigo', 'metodo', 'erro'], delimiter=';')
        w.writeheader()
        for r in rows:
            w.writerow(r)

    criados = sum(1 for r in rows if r['status'] == 'criado')
    atualizados = sum(1 for r in rows if r['status'] == 'atualizado')
    inalterados = sum(1 for r in rows if r['status'] == 'inalterado')
    ignorados = sum(1 for r in rows if r['status'].startswith('ignorado'))
    falhas = sum(1 for r in rows if r['status'].startswith('falha'))

    print('FIM')
    print('CRIADOS', criados)
    print('ATUALIZADOS', atualizados)
    print('INALTERADOS', inalterados)
    print('IGNORADOS', ignorados)
    print('FALHAS', falhas)
    print('REPORT', REPORT_CSV.name)
    print('CHECKPOINT', CHECKPOINT.name)


if __name__ == '__main__':
    main()
