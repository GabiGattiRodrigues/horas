# Exportando os resultados do notebook pra página (site/index.html)
# Roda o código do notebook, refaz os backtests pra cada percentil e grava os números
# dentro do bloco DADOS-INICIO ... DADOS-FIM da página. Uso: python scripts/exportar_pagina.py

import json
import re
import nbformat

NOTEBOOK = 'horas_promessa_de_entrega.ipynb'
PAGINA = 'site/index.html'
QS_ROTA = [.80, .85, .90, .93, .95, .97]
QS_QUANTILICA = [.85, .88, .90, .92, .94, .96]


def carregar_funcoes_do_notebook(caminho):
    # Executando as células do notebook sem os gráficos e sem as contas mais pesadas
    ns = {}
    nb = nbformat.read(caminho, as_version=4)
    for celula in nb.cells:
        if celula.cell_type != 'code':
            continue
        pular = ('grafico_', 'curva = curva_de_troca', 'curva.round', 'dias_para_mesma_taxa(curva)')
        linhas = [l for l in celula.source.split('\n')
                  if not l.startswith(pular) and 'renderers.default' not in l]
        exec('\n'.join(linhas), ns)
    return ns


def exportar(ns):
    df = ns['df']
    entregues = df[df.entregue]
    saida = {}
    saida['resumo'] = dict(
        pedidos=int(len(df)), no_prazo=float(df.no_prazo.mean()),
        prometido=float(df.prazo_prometido.median()), real=float(entregues.prazo_real.median()),
        folga=float(entregues.folga.median()), p95=float(entregues.prazo_real.quantile(.95)),
    )

    por_uf = ns['por_uf'].reset_index()
    saida['por_uf'] = por_uf[['customer_state', 'pedidos', 'no_prazo', 'folga_mediana',
                              'prometido_mediana', 'real_mediana']].to_dict('records')

    notas = ns['notas'].reset_index()
    notas['faixa'] = notas.faixa.astype(str)
    saida['notas'] = notas.to_dict('records')

    semanas = ns['semanas'].reset_index()
    semanas['dia_compra'] = semanas.dia_compra.dt.strftime('%Y-%m-%d')
    saida['semanas'] = semanas.to_dict('records')
    saida['p_barra'] = float(ns['p_barra'])

    curva, por_q = [], {}
    for q in QS_ROTA:
        t = ns['backtest'](df, ns['promessa_percentil_rota'], q)
        curva.append(dict(metodo='rota', q=q, no_prazo=float(t.no_prazo_nova.mean()), dias=float(t.promessa_nova.mean())))
    for q in QS_QUANTILICA:
        t = ns['backtest'](df, ns['promessa_quantilica'], q)
        curva.append(dict(metodo='quantilica', q=q, no_prazo=float(t.no_prazo_nova.mean()), dias=float(t.promessa_nova.mean())))
        comp = ns['comparar_por_uf'](t).reset_index()
        nota_atual, nota_nova = ns['nota_esperada'](t, ns['notas'])
        por_q[f'{q:.2f}'] = dict(
            geral_atual=float(t.no_prazo.mean()), geral_nova=float(t.no_prazo_nova.mean()),
            dias_atual=float(t.prazo_prometido.mean()), dias_nova=float(t.promessa_nova.mean()),
            sd_atual=float(comp.no_prazo_atual.std()), sd_nova=float(comp.no_prazo_nova.std()),
            nota_atual=float(nota_atual), nota_nova=float(nota_nova), ufs=comp.to_dict('records'),
        )
    olist = df[df.mes.isin(ns['MESES_TESTE'])]
    curva.append(dict(metodo='olist', q=None, no_prazo=float(olist.no_prazo.mean()), dias=float(olist.prazo_prometido.mean())))
    saida['curva'] = curva
    saida['por_q'] = por_q
    saida['n_teste'] = int(len(olist))
    return saida


def gravar_na_pagina(dados, caminho):
    pagina = open(caminho, encoding='utf-8').read()
    bloco = json.dumps(dados, ensure_ascii=False, separators=(',', ':'), default=float)
    nova = re.sub(r'/\*DADOS-INICIO\*/.*?/\*DADOS-FIM\*/',
                  lambda _: '/*DADOS-INICIO*/' + bloco + '/*DADOS-FIM*/', pagina, flags=re.S)
    open(caminho, 'w', encoding='utf-8').write(nova)
    json.dump(dados, open('site/dados.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)


if __name__ == '__main__':
    ns = carregar_funcoes_do_notebook(NOTEBOOK)
    dados = exportar(ns)
    gravar_na_pagina(dados, PAGINA)
    print('Página atualizada:', PAGINA)
