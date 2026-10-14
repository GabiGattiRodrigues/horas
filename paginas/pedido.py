"""Aba Pedido a pedido: um pedido real de agosto/2018, a promessa da Olist, a do modelo e o que pesou."""
import numpy as np
import pandas as pd
import streamlit as st

from horas_app.arvores import dia_nome, grafico_cascata, grafico_convergencia
from horas_app.comum import (lang, L, VERDE, VERMELHO, caixa, como_ler, dias, em_uma_frase, kpi, matriz_modelo, metodo, modelo,
                             nome_var, num, pedidos)


def _selecionados(P):
    """Uma lista curta de pedidos que contam a história, mais dois casos de borda."""
    ent = P[P.prazo_real.notna()]
    escolhas, marcas = [], {}
    for rota in ["SP>SP", "SP>RJ", "SP>MG", "SP>BA", "SP>CE", "MG>SP", "PR>RS", "SP>PA"]:
        r = ent[ent.rota == rota]
        if len(r):
            escolhas.append(r.iloc[(r.prazo_real - r.prazo_real.median()).abs().argsort()].index[0])
    olist_atrasou = ent[(ent.prazo_real > ent.prazo_prometido) & (ent.prazo_real <= ent.promessa_nova)].sort_values("order_id")
    modelo_atrasou = ent[(ent.prazo_real <= ent.prazo_prometido) & (ent.prazo_real > ent.promessa_nova)].sort_values("order_id")
    if len(olist_atrasou):
        escolhas.append(olist_atrasou.index[0])
        marcas[olist_atrasou.index[0]] = "olist"
    if len(modelo_atrasou):
        escolhas.append(modelo_atrasou.index[0])
        marcas[modelo_atrasou.index[0]] = "modelo"
    return list(dict.fromkeys(escolhas)), marcas


def render():
    M, P = metodo(), pedidos()
    em_uma_frase(
        "pega um pedido de verdade e compara três números: o que a Olist prometeu, o que o modelo prometeria e quanto ele "
        "realmente levou pra chegar.",
        "takes a real order and compares three numbers: what Olist promised, what the model would promise and how long it "
        "actually took to arrive.",
    )
    st.markdown(L(
        f"São pedidos de agosto de 2018. O modelo aprendeu só com pedidos entregues de {M['treino_de']} a {M['treino_ate']}, "
        "então **nunca viu esses pedidos**. É exatamente o teste da vida real.",
        f"These are August 2018 orders. The model learned only from orders delivered between {M['treino_de']} and "
        f"{M['treino_ate']}, so it **never saw these orders**. It's exactly the real-life test.",
    ))

    opcoes, marcas = _selecionados(P)

    def rotulo(i):
        r = P.loc[i]
        rota = r.rota.replace(">", " → ")
        if pd.isna(r.prazo_real):
            return f"{rota} · {L('não chegou', 'not delivered')}"
        marca = {"olist": L(" · a Olist atrasou, o modelo não", " · Olist was late, the model wasn't"),
                 "modelo": L(" · o modelo atrasaria, a Olist não", " · the model would be late, Olist wasn't")}.get(marcas.get(i), "")
        return f"{rota} · {L('chegou em', 'arrived in')} {dias(r.prazo_real)}{marca}"

    if "pedido_idx" not in st.session_state:
        st.session_state.pedido_idx = int(opcoes[1])
    lista = opcoes if st.session_state.pedido_idx in opcoes else [st.session_state.pedido_idx] + opcoes
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    idx = c1.selectbox(L("Escolha um pedido", "Pick an order"), lista, index=lista.index(st.session_state.pedido_idx),
                       format_func=rotulo, key=f"pedido_select_{lang()}")
    st.session_state.pedido_idx = int(idx)
    if c2.button(L("🎲 Sortear outro pedido", "🎲 Random order"), width="stretch", key="pedido_sortear"):
        st.session_state.pedido_idx = int(np.random.default_rng().choice(P.index))
        st.rerun()

    p = P.loc[st.session_state.pedido_idx]
    X = matriz_modelo(P.loc[[p.name]])
    bruto = float(modelo().predict(X)[0])
    prom = int(np.ceil(bruto))

    c = st.columns(3)
    kpi(c[0], dias(p.prazo_prometido), L("a Olist prometeu", "Olist promised"))
    kpi(c[1], dias(prom), L("o modelo prometeria", "the model would promise"),
        L(f"{num(prom - p.prazo_prometido)} dias em relação à Olist", f"{num(prom - p.prazo_prometido)} days vs Olist"))
    kpi(c[2], L("não chegou", "not delivered") if pd.isna(p.prazo_real) else dias(p.prazo_real), L("levou pra chegar", "it took to arrive"))

    if pd.notna(p.prazo_real):
        ok_o, ok_m = p.prazo_real <= p.prazo_prometido, p.prazo_real <= prom
        txt = {True: L("chegaria no prazo ✅", "would arrive on time ✅"), False: L("atrasaria ❌", "would be late ❌")}
        caixa(L(f"Com a promessa da Olist, esse pedido **{txt[ok_o]}**. Com a do modelo, **{txt[ok_m]}**.",
                f"With Olist's promise, this order **{txt[ok_o]}**. With the model's, it **{txt[ok_m]}**."),
              "verde" if ok_m else "ambar")

    with st.expander(L("Ficha do pedido", "Order details"), expanded=False):
        ficha = pd.DataFrame([
            (L("Rota", "Route"), f"{p.seller_city.title()} ({p.seller_state}) → {p.customer_city.title()} ({p.customer_state})"),
            (L("Compra", "Purchase"), f"{p.dia_compra} ({dia_nome(p.dia_semana)})"),
            (nome_var("km"), num(p.km)),
            (nome_var("frete"), "R$ " + num(p.frete, 2)),
            (nome_var("peso"), num(p.peso)),
            (nome_var("qtd_itens"), num(p.qtd_itens)),
            (nome_var("vend_manuseio_mediana"), "—" if pd.isna(p.vend_manuseio_mediana) else num(p.vend_manuseio_mediana, 1)),
            (nome_var("vend_manuseio_p90"), "—" if pd.isna(p.vend_manuseio_p90) else num(p.vend_manuseio_p90, 1)),
            (nome_var("vend_pedidos"), "—" if pd.isna(p.vend_pedidos) else num(p.vend_pedidos)),
        ], columns=[L("Campo", "Field"), L("Valor", "Value")])
        st.dataframe(ficha, hide_index=True, width="stretch")

    st.markdown("#### " + L("Por que o modelo chegou nesse número", "Why the model got to this number"))
    contrib = modelo().predict(X, pred_contrib=True)[0]
    base, partes = contrib[-1], pd.Series(contrib[:-1], index=M["variaveis"])

    def valor_legivel(v):
        x = p[v]
        if v in ("seller_state", "customer_state"):
            return str(x)
        if v == "dia_semana":
            return dia_nome(x)
        if pd.isna(x):
            return L("sem histórico", "no history")
        return num(x, 1 if v.startswith("vend_manuseio") else 0)

    st.plotly_chart(grafico_cascata(base, partes, bruto, valor_legivel), width="stretch")
    como_ler(
        f"começa na promessa média do modelo ({num(base, 1)} dias). Cada barra é uma característica do pedido: **vermelho "
        f"soma dias, azul tira**. O resultado ({num(bruto, 2)}) arredondado pra cima vira **{prom} dias**, porque não dá "
        "pra prometer meio dia.",
        f"starts at the model's average promise ({num(base, 1)} days). Each bar is a feature of the order: **red adds days, "
        f"blue removes them**. The result ({num(bruto, 2)}) rounded up becomes **{prom} days**, because you can't promise "
        "half a day.",
    )

    st.markdown("#### " + L("A promessa se formando, árvore por árvore", "The promise taking shape, tree by tree"))
    refs = [(p.prazo_prometido, L("Olist prometeu", "Olist promised"), VERMELHO, "top left")]
    if pd.notna(p.prazo_real):
        refs.append((p.prazo_real, L("chegou em", "arrived in"), VERDE, "bottom left"))
    st.plotly_chart(grafico_convergencia(modelo(), X, M["n_arvores"], refs), width="stretch")
    como_ler(
        f"o modelo soma {M['n_arvores']} árvores. A primeira já começa perto do prazo que cobre 92% de todos os pedidos "
        f"({dias(M['p92_treino'])}). Cada árvore seguinte faz um ajuste pequeno, e a linha azul mostra a promessa depois "
        "de somar cada quantidade de árvores. A explicação completa está em **Como funciona**.",
        f"the model adds up {M['n_arvores']} trees. The first one already starts near the lead time covering 92% of all "
        f"orders ({dias(M['p92_treino'])}). Each following tree makes a small adjustment, and the blue line shows the "
        "promise after adding each number of trees. The full explanation is in **How it works**.",
    )
