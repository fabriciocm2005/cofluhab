# Analise do Manual FCVS - Impacto no Sistema

Fonte analisada:
- manual/Manual_de_Normas_e_Procedimentos_Operacionais_do_FCVS (1).pdf
- Extracao textual usada na analise: manual/_manual_fcvs_extracted_agent.txt

## Resumo executivo

O manual confirma que o sistema ja esta no caminho certo para leitura de retornos e manejo de RNV/RCV, mas ha lacunas importantes em governanca de prazo, trilha de pendencias CADMUT e regras operacionais de recepcao/retransmissao.

Impacto geral:
- Alto para compliance operacional (prazos e penalidades)
- Medio para parser (causas de rejeicao e situacao contratual)
- Medio para UX operacional (alertas, semaforos e fila de acao)

## Pontos normativos que influenciam o sistema

1. Prazo de recepcao de relatorios e mensagens
- Regra: recepcao em ate 90 dias corridos da disponibilizacao.
- Regra: retransmissao autorizada ate 120 dias da disponibilizacao.
- Referencia: subitens 9.8.2 e 9.8.2.1.

2. Manifestacao apos homologacao (RCV, RNV, RCNP)
- Regra: manifestar ate o ultimo dia util do 3o mes subsequente ao recebimento do termino de analise.
- Regra: sem manifestacao no prazo -> registro automatico em RCNP.
- Regra: RCV e RNV por leiaute especifico da CAIXA.
- Referencia: capitulo XI, itens 11.1, 11.1.1, 11.2.1, 11.2.2.

3. Prazo para recurso/reabertura apos RNV
- Regra: ate o ultimo dia util do 12o mes posterior ao processamento da RNV.
- Excecao: pendencia CADMUT dispensa regra de prazo 11.4.1.
- Referencia: itens 11.4.1 e 11.4.1.2.

4. Causas relevantes de pendencia e rejeicao
- Regra: pendencias de CADMUT (ausencia de registro, erro de critica, indicio de multiplicidade/sinistro) mudam o fluxo e podem negar cobertura.
- Regra: pedido rejeitado pode ser reencaminhado apos adequacao.
- Referencia: itens 9.3, 9.6 e 9.7.

5. Arquivo com erro de leitura
- Regra: em avaliacao atuarial, arquivo com erro de leitura deve ser corrigido em ate 10 dias corridos da comunicacao.
- Penalidade: descumprimento pode impedir ressarcimento de creditos perante FCVS.
- Referencia: itens 17.2.1 e 17.5.

## O que ja existe no sistema (bom nivel de aderencia)

- Parser e consolidacao de retornos S com leitura de RNV/RCV em relatorios e detalhes.
- Geracao de remessa RNV (simplificada e layout 430) e fluxo de envio automatico.
- Tratamento de codigos de retorno e consolidado operacional por lote.

## Gaps encontrados

1. Sem motor de prazos normativos
- Falta calcular e monitorar vencimentos de 90 dias, 120 dias, 3o mes util e 12o mes util.

2. Sem semaforo de risco RCNP
- Falta sinalizar contratos que vao cair em RCNP por ausencia de manifestacao.

3. Sem classificacao normativa de pendencias CADMUT
- Ha leitura de retorno, mas faltam buckets normativos explicitos (ausencia CADMUT, critica CADMUT, multiplicidade/sinistro).

4. Sem trilha operacional para erro de leitura de arquivo
- Falta evento de "arquivo rejeitado por leitura" com SLA interno de correcao (10 dias).

5. Sem painel de compliance de prazos
- Falta visao consolidada por contrato/remessa com status: no prazo, em risco, vencido.

## Backlog recomendado (prioridade)

P1 (imediato)
- Criar modulo de prazos FCVS com calculo de datas limite por contrato/remessa.
- Adicionar alerta de risco RCNP com base no recebimento de termino de analise.
- Persistir datas de referencia no banco: data_recebimento_relatorio, data_processamento_rnv, data_limite_manifestacao.

P2 (curto prazo)
- Classificar automaticamente causas de rejeicao e pendencias CADMUT em categorias normativas.
- Expor no consolidado e no dashboard campos de motivo_normativo e acao_recomendada.

P3 (medio prazo)
- Implementar workflow de retransmissao (90/120 dias) com checkpoints.
- Implementar workflow de erro de leitura com SLA de 10 dias e bloqueio de envio sem acerto.

## Sugestao de campos novos

- prazo_recepcao_relatorio_dias_restantes
- prazo_retransmissao_dias_restantes
- prazo_manifestacao_rcnp_dias_restantes
- prazo_recurso_rnv_dias_restantes
- risco_rcnp (baixo/medio/alto)
- pendencia_cadmut_categoria
- status_compliance_fcvs

## Conclusao

O manual influencia diretamente o sistema, principalmente em prazos obrigatorios, transicoes RCV/RNV/RCNP e tratamento de pendencias CADMUT. O maior ganho agora nao e um parser novo, e sim uma camada de compliance operacional com regras de prazo e alerta preventivo.
