# Gerando os artefatos que o app lê (pasta artifacts/)
# Roda as funções do notebook, refaz os backtests e salva tudo que o app precisa pra abrir
# rápido e sem a base da Olist: resultados, modelo de agosto/2018, árvores e pedidos de exemplo.
# Também atualiza os números da página estática (site/index.html).
# Uso: python scripts/gerar_artefatos.py

import json
import os
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))
from exportar_pagina import NOTEBOOK, PAGINA, carregar_funcoes_do_notebook, exportar, gravar_na_pagina  # noqa: E402

ART = RAIZ / 'artifacts'
MES_EXEMPLO = pd.Period('2018-08', freq='M')
Q = 0.92


def salvar_json(obj, nome):
    (ART / nome).write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=float), encoding='utf-8')


def treinar_modelo_do_mes(ns, df, mes, q=Q):
    # Treinando o mesmo modelo do backtest pra um mês específico (6 meses anteriores, só entregues)
    treino = df[(df.mes >= mes - ns['JANELA']) & (df.mes < mes) & df.entregue].copy()
    teste = df[df.mes == mes].copy()
    hist = ns['historico_vendedor'](treino)
    treino = treino.join(hist, on='seller_id')
    teste = teste.join(hist, on='seller_id')
    categorias = {}
    for c in ['seller_state', 'customer_state']:
        cats = sorted(df[c].unique())
        categorias[c] = cats
        treino[c] = treino[c].astype(pd.CategoricalDtype(cats))
        teste[c] = teste[c].astype(pd.CategoricalDtype(cats))
    modelo = lgb.LGBMRegressor(objective='quantile', alpha=q, n_estimators=300, learning_rate=.05,
                               num_leaves=31, min_child_samples=50, verbose=-1)
    modelo.fit(treino[ns['VARIAVEIS']], treino.prazo_real)
    teste['promessa_nova'] = np.ceil(modelo.predict(teste[ns['VARIAVEIS']]))
    return modelo, treino, teste, categorias


def arvores_legiveis(booster, categorias):
    # Tabela das árvores com o nome das UFs no lugar do código da categoria
    arv = booster.trees_to_dataframe()
    cols_cat = {'seller_state': categorias['seller_state'], 'customer_state': categorias['customer_state']}

    def traduzir(linha):
        if linha.decision_type == '==' and linha.split_feature in cols_cat:
            nomes = cols_cat[linha.split_feature]
            return ', '.join(nomes[int(k)] for k in str(linha.threshold).split('||'))
        return linha.threshold

    arv['threshold'] = arv.apply(traduzir, axis=1)
    return arv


def arvore_didatica(treino, ns, categorias):
    # Uma árvore só, com 4 folhas, pra mostrar a ideia antes das 300 árvores do modelo de verdade.
    # Com learning_rate=1, cada folha vira o P92 do prazo real dos pedidos que caem nela.
    mini = lgb.LGBMRegressor(objective='quantile', alpha=Q, n_estimators=1, learning_rate=1.0,
                             num_leaves=4, min_child_samples=300, verbose=-1)
    mini.fit(treino[ns['VARIAVEIS']], treino.prazo_real)
    mini.booster_.save_model(str(ART / 'modelo_didatico.txt'))
    return arvores_legiveis(mini.booster_, categorias)


def treze_pedidos(treino):
    # Treze pedidos reais da rota SP>RJ pro exemplo da perda quantílica.
    # Com 13 pedidos, o P92 cai exatamente no 12º: a promessa cobre 12 de 13 (92,3%).
    rota = treino[(treino.rota == 'SP>RJ')]
    amostra = rota.sample(13, random_state=7).sort_values('prazo_real')
    return amostra[['order_id', 'prazo_real']].to_dict('records')


def p92_por_rota(treino, top=10):
    tab = treino.groupby('rota').prazo_real.agg(
        pedidos='size', mediana='median', p92=lambda s: np.ceil(s.quantile(Q)))
    return tab.sort_values('pedidos', ascending=False).head(top).reset_index().to_dict('records')


def vendedor_rapido_lento(treino, rota='SP>RJ'):
    # Mesma rota, vendedores rápidos e lentos pra despachar: o percentil da rota trata todos igual
    t = treino[treino.rota == rota]
    faixas = pd.cut(t.vend_manuseio_mediana, [-1, 1, 3, 999], labels=['rapido', 'medio', 'lento'])
    tab = t.groupby(faixas, observed=True).prazo_real.agg(
        pedidos='size', mediana='median', p92=lambda s: np.ceil(s.quantile(Q)))
    return tab.reset_index().rename(columns={'vend_manuseio_mediana': 'faixa'}).to_dict('records')


def referencias_simulador(treino, teste):
    # O que o simulador precisa pra sugerir valores e comparar: por rota, os valores típicos,
    # o P92 da rota, a promessa típica da Olist em ago/2018 e a distribuição do prazo real
    rotas = {}
    for rota, g in treino.groupby('rota'):
        if len(g) < 30:
            continue
        hist = np.bincount(g.prazo_real.clip(upper=60).astype(int), minlength=61).tolist()
        olist = teste.loc[teste.rota == rota, 'prazo_prometido']
        rotas[rota] = dict(
            pedidos=int(len(g)), km=float(g.km.median()), frete=float(g.frete.median()), peso=float(g.peso.median()),
            p92=float(np.ceil(g.prazo_real.quantile(Q))), mediana=float(g.prazo_real.median()),
            olist=float(olist.median()) if len(olist) else None, hist=hist,
        )
    com_hist = treino[treino.vend_pedidos.notna()]
    perfis = {}
    for nome, q in [('rapido', .10), ('medio', .50), ('lento', .90)]:
        perfis[nome] = dict(
            vend_manuseio_mediana=float(com_hist.vend_manuseio_mediana.quantile(q)),
            vend_manuseio_p90=float(com_hist.vend_manuseio_p90.quantile(q)),
            vend_pedidos=float(com_hist.vend_pedidos.median()),
        )
    return dict(rotas=rotas, perfis_vendedor=perfis, peso_mediano=float(treino.peso.median()),
                frete_mediano=float(treino.frete.median()))


def backtest_por_mes(teste_q):
    tab = teste_q.groupby('mes').agg(
        pedidos=('order_id', 'size'),
        no_prazo_atual=('no_prazo', 'mean'), no_prazo_nova=('no_prazo_nova', 'mean'),
        dias_atual=('prazo_prometido', 'mean'), dias_nova=('promessa_nova', 'mean'))
    tab.index = tab.index.astype(str)
    return tab.reset_index().to_dict('records')


def pedidos_exemplo(teste, ns):
    cols = ['order_id', 'rota', 'seller_state', 'customer_state', 'seller_city', 'customer_city', 'dia_compra',
            'prazo_prometido', 'prazo_real', 'promessa_nova'] + [v for v in ns['VARIAVEIS'] if v not in ('seller_state', 'customer_state')]
    out = teste[cols].copy()
    out['dia_compra'] = out.dia_compra.dt.strftime('%Y-%m-%d')
    out['seller_state'] = out.seller_state.astype(str)
    out['customer_state'] = out.customer_state.astype(str)
    return out


if __name__ == '__main__':
    os.chdir(RAIZ)  # o notebook lê data/ e grava site/ a partir da raiz do projeto
    ART.mkdir(exist_ok=True)
    print('Rodando o notebook e os backtests (leva alguns minutos)...')
    ns = carregar_funcoes_do_notebook(NOTEBOOK)
    df = ns['df']

    dados = exportar(ns)
    gravar_na_pagina(dados, PAGINA)
    salvar_json(dados, 'resultados.json')

    print('Treinando o modelo de agosto/2018 pra aba Como funciona...')
    modelo, treino, teste, categorias = treinar_modelo_do_mes(ns, df, MES_EXEMPLO)
    booster = modelo.booster_
    booster.save_model(str(ART / 'modelo_ago2018.txt'))
    arvores_legiveis(booster, categorias).to_csv(ART / 'arvores.csv', index=False)
    arvore_didatica(treino, ns, categorias).to_csv(ART / 'arvore_didatica.csv', index=False)
    imp = pd.Series(booster.feature_importance('gain'), index=booster.feature_name())
    (imp / imp.sum()).sort_values(ascending=False).rename('ganho').to_csv(ART / 'importancia.csv', index_label='variavel')
    pedidos_exemplo(teste, ns).to_csv(ART / 'pedidos_ago2018.csv', index=False)
    salvar_json(referencias_simulador(treino, teste), 'simulador.json')

    print('Treinando as versões P85 e P96 pro simulador...')
    for q, nome in [(0.85, 'p85'), (0.96, 'p96')]:
        m_q, _, _, _ = treinar_modelo_do_mes(ns, df, MES_EXEMPLO, q=q)
        m_q.booster_.save_model(str(ART / f'modelo_ago2018_{nome}.txt'))

    salvar_json(dict(
        variaveis=ns['VARIAVEIS'],
        categorias=categorias,
        q=Q,
        n_arvores=int(booster.num_trees()),
        treino_de=str(MES_EXEMPLO - ns['JANELA']), treino_ate=str(MES_EXEMPLO - 1), mes=str(MES_EXEMPLO),
        p92_treino=float(np.ceil(treino.prazo_real.quantile(Q))),
        treze_pedidos=treze_pedidos(treino),
        p92_por_rota=p92_por_rota(treino),
        vendedor_rapido_lento=vendedor_rapido_lento(treino),
        backtest_por_mes=backtest_por_mes(ns['teste_q']),
        no_prazo_ago_atual=float(teste.no_prazo.mean()),
        no_prazo_ago_nova=float((teste.prazo_real_ajustado <= teste.promessa_nova).mean()),
    ), 'metodo.json')
    print('Artefatos salvos em', ART)
