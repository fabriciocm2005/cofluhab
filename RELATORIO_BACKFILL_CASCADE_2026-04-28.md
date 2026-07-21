# Relatorio de Execucao - Backfill em Cascata (2026-04-28)

## Fontes usadas (ordem)
1. CADBAK.DBF
2. CAD1.DBF
3. CAD2.DBF
4. cad1012.dbf
5. CADMUT270204.DBF
6. CADMUT2.DBF
7. cadmutbk.dbf
8. CADMUT_2.DBF
9. CADOK.DBF
10. CADMUT__BK.DBF
11. cofluhab.dbf

## Antes
- Contratos: 3134
- Mutuarios: 3128
- Contrato faltando campos criticos:
  - data_contrato: 3
  - data_primeiro_venc: 549
  - sa: 549
  - tx_juros: 549
  - prazo: 549
  - cat_prof: 548
  - pr: 547
- Mutuario faltando endereco:
  - endereco: 471
  - numero: 653
  - cidade: 471
  - cep: 471
  - uf: 1

## Execucao
- Contratos atualizados: 547
- Mutuarios atualizados: 471
- Fonte efetiva dos updates nesta rodada: cofluhab.dbf

## Depois
- Contrato faltando campos criticos:
  - data_contrato: 2
  - data_primeiro_venc: 549
  - sa: 2
  - tx_juros: 2
  - prazo: 2
  - cat_prof: 548
  - pr: 0
- Mutuario faltando endereco:
  - endereco: 0
  - numero: 653
  - cidade: 0
  - cep: 0
  - uf: 0

## Reducao de faltantes
- Contrato:
  - data_contrato: -1
  - data_primeiro_venc: 0
  - sa: -547
  - tx_juros: -547
  - prazo: -547
  - cat_prof: 0
  - pr: -547
- Mutuario:
  - endereco: -471
  - numero: 0
  - cidade: -471
  - cep: -471
  - uf: -1

## Precheck FH1 (snapshot apos backfill)
- total_registros: 3132
- status: REPROVADO
- total_erros: 15661
- total_avisos: 1
- aviso principal: UFS no HEADER difere do esperado (19 != 33)
- erros recorrentes: CODIGO MUNICIPIO zerado, VALOR GARANTIA zerado, RR zerado, OR/CO zerado, ST=0

## Observacoes
- O backfill resolveu os faltantes de endereco (exceto numero) e quase todos os faltantes de sa/tx_juros/prazo/pr.
- Persistem lacunas estruturais para data_primeiro_venc e cat_prof (nao disponiveis nas fontes usadas para os contratos faltantes).
- A reprova do precheck FH1 agora esta concentrada em campos de layout/negocio nao cobertos apenas por backfill cadastral.
