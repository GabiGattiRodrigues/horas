"""Aba Simulador: monta um pedido e vê quanto o modelo prometeria, comparado com a rota e com a Olist."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horas_app.arvores import dia_nome, grafico_cascata
from horas_app.comum import (lang, AZUL, AZUL_CLARO, CINZA, L, VERDE, VERMELHO, caixa, como_ler, em_uma_frase, kpi, layout,
                             matriz_modelo, metodo, modelo, num, pct, simulador_ref)

PERFIS = {
    "rapido": ("Rápido pra despachar", "Fast to ship"),
    "medio": ("Normal", "Average"),
    "lento": ("Lento pra despachar", "Slow to ship"),
    "novo": ("Novo, sem histórico", "New, no history"),
}
SEGURANCA = {
    "p85": ("Mais curta (P85)", "Shorter (P85)", 0.85),
    "p92": ("Equilibrada (P92)", "Balanced (P92)", 0.92),
    "p96": ("Mais segura (P96)", "Safer (P96)", 0.96),
}


def render():
    M, S = metodo(), simulador_ref()
    ufs = M["categorias"]["customer_state"]
    ufs_vend = M["categorias"]["seller_state"]

    em_uma_frase(
        "monte um pedido e veja quantos dias o modelo prometeria, por que chegou nesse número e quantos pedidos parecidos "
        "chegariam dentro dessa promessa.",
        "build an order and see how many days the model would promise, why it got to that number and how many similar "
        "orders would arrive within that promise.",
    )

    st.markdown("#### " + L("1. Monte o pedido", "1. Build the order"))
    c1, c2, c3 = st.columns(3)
    vend = c1.selectbox(L("De onde sai (UF do vendedor)", "Ships from (seller state)"), ufs_vend,
                        index=ufs_vend.index("SP"), key="sim_vend")
    cli = c1.selectbox(L("Pra onde vai (UF do cliente)", "Ships to (customer state)"), ufs,
                       index=ufs.index("RJ"), key="sim_cli")
    rota = f"{vend}>{cli}"
    ref = S["rotas"].get(rota)
    if ref is None:
        c1.warning(L("Essa rota teve menos de 30 pedidos no treino. Os valores sugeridos são da base inteira.",
                     "This route had fewer than 30 orders in training. Suggested values come from the whole dataset."), icon="⚠️")

    perfil = c2.radio(L("Como é o vendedor?", "What is the seller like?"), list(PERFIS),
                      format_func=lambda k: L(*PERFIS[k]), index=1, key=f"sim_perfil_{lang()}",
                      help=L("Rápido: costuma despachar em 1 dia, até 3 nos piores casos. Normal: uns 2 dias, até 4. Lento: uns 4 dias, até 8. "
                             "Novo: sem pedidos nos 6 meses anteriores.",
                             "Fast: usually ships in 1 day, up to 3 in the worst cases. Average: about 2 days, up to 4. Slow: about 4 days, up to 8. "
                             "New: no orders in the previous 6 months."))
    dia = c2.selectbox(L("Dia da compra", "Purchase day"), list(range(7)), format_func=dia_nome, index=2, key=f"sim_dia_{lang()}")

    km_pad = int(round(ref["km"])) if ref else 600
    frete_pad = float(round(ref["frete"], 2)) if ref else float(S["frete_mediano"])
    peso_pad = int(ref["peso"]) if ref else int(S["peso_mediano"])
    km = c3.number_input(L("Distância vendedor → cliente (km)", "Seller → customer distance (km)"), 0, 4500, km_pad, step=50,
                         key=f"sim_km_{rota}", help=L("Já vem com a distância típica da rota. Pode mudar.",
                                                       "Pre-filled with the route's typical distance. You can change it."))
    peso = c3.number_input(L("Peso do pedido (g)", "Order weight (g)"), 50, 30000, peso_pad, step=100, key=f"sim_peso_{rota}")
    frete = c3.number_input(L("Valor do frete (R$)", "Freight value (R$)"), 0.0, 300.0, frete_pad, step=1.0,
                            key=f"sim_frete_{rota}")
    itens = c3.number_input(L("Itens no pedido", "Items in the order"), 1, 10, 1, key="sim_itens")

    seg = st.radio(L("Quão segura deve ser a promessa?", "How safe should the promise be?"), list(SEGURANCA),
                   format_func=lambda k: L(SEGURANCA[k][0], SEGURANCA[k][1]), index=1, horizontal=True, key=f"sim_seg_{lang()}",
                   help=L("P92 cobre 92 de cada 100 pedidos parecidos. P85 promete menos e erra mais. P96 promete mais e erra menos.",
                          "P92 covers 92 of every 100 similar orders. P85 promises less and misses more. P96 promises more and misses less."))
    q = SEGURANCA[seg][2]

    # ----------------------------------------------------------------- o pedido no formato do modelo
    if perfil == "novo":
        vh = dict(vend_manuseio_mediana=np.nan, vend_manuseio_p90=np.nan, vend_pedidos=np.nan)
    else:
        vh = S["perfis_vendedor"][perfil]
    linha = pd.DataFrame([dict(km=km, seller_state=vend, customer_state=cli, dia_semana=dia, frete=frete, peso=peso,
                               qtd_itens=itens, **vh)])
    X = matriz_modelo(linha)
    bst = modelo(seg)
    bruto = float(bst.predict(X)[0])
    promessa = int(np.ceil(bruto))

    # ----------------------------------------------------------------- resultado
    st.markdown("#### " + L("2. Quanto prometer", "2. How much to promise"))
    hist = np.array(ref["hist"]) if ref else None
    c = st.columns(4)
    kpi(c[0], num(promessa) + L(" dias", " days"), L("é a promessa do modelo pra esse pedido", "is the model's promise for this order"),
        L(SEGURANCA[seg][0], SEGURANCA[seg][1]))
    if ref:
        cobre = hist[: promessa + 1].sum() / hist.sum() if promessa <= 60 else 1.0
        kpi(c[1], pct(cobre, 0), L("dos pedidos dessa rota chegaram em até esse prazo", "of this route's orders arrived within that lead time"),
            L(f"{num(ref['pedidos'])} pedidos de {M['treino_de']} a {M['treino_ate']}", f"{num(ref['pedidos'])} orders from {M['treino_de']} to {M['treino_ate']}"))
        kpi(c[2], num(ref["p92"]) + L(" dias", " days"), L("seria a promessa do jeito simples (P92 da rota)", "would be the simple-way promise (route P92)"),
            L("igual pra todo pedido da rota", "the same for every order on the route"))
        if ref["olist"] is not None:
            kpi(c[3], num(ref["olist"]) + L(" dias", " days"), L("era a promessa típica da Olist nessa rota", "was Olist's typical promise on this route"),
                L(f"mediana em {M['mes']}", f"median in {M['mes']}"))
        else:
            kpi(c[3], "—", L("a Olist não teve pedidos dessa rota no mês", "Olist had no orders on this route that month"))
    else:
        for col in c[1:]:
            kpi(col, "—", L("rota com poucos pedidos pra comparar", "route with too few orders to compare"))

    if ref and ref["olist"] is not None and promessa > ref["olist"] + 5:
        caixa(L(
            "**Por que a Olist prometia bem menos aqui?** Em agosto de 2018 a Olist encurtou bastante a promessa: a média caiu "
            "pra 16 dias, contra 20 a 28 nos meses anteriores. O modelo aprendeu com fevereiro a julho, que teve os atrasos de "
            "fevereiro e março, então fica mais cauteloso nesse mês. No backtest de agosto, o modelo entregou 96% no prazo "
            "e a Olist, 93%. É por isso que a calibração precisa ser refeita todo mês.",
            "**Why was Olist promising much less here?** In August 2018 Olist shortened its promise a lot: the average fell "
            "to 16 days, against 20 to 28 in previous months. The model learned from February to July, which had the February and "
            "March delays, so it is more cautious that month. In the August backtest the model delivered 96% on time and "
            "Olist 93%. That's why calibration has to be redone every month.",
        ), "ambar")

    if ref:
        st.markdown("#### " + L("3. Os pedidos parecidos", "3. The similar orders"))
        dias_ = np.arange(len(hist))
        cores = [AZUL if d <= promessa else VERMELHO for d in dias_]
        fig = go.Figure(go.Bar(x=dias_, y=hist, marker_color=cores,
                               hovertemplate=L("chegaram em %{x} dias", "arrived in %{x} days") + ": %{y} " + L("pedidos", "orders") + "<extra></extra>"))
        # rótulos pra lados opostos, pra não se sobreporem quando as linhas ficam perto
        lado_mod, lado_rota = ("top left", "top right") if promessa <= ref["p92"] else ("top right", "top left")
        fig.add_vline(x=promessa + 0.5, line_color="#10233a", line_width=2,
                      annotation_text=L(f"modelo: {promessa} dias", f"model: {promessa} days"), annotation_position=lado_mod)
        fig.add_vline(x=ref["p92"] + 0.5, line_color=CINZA, line_dash="dash",
                      annotation_text=L(f"P92 da rota: {num(ref['p92'])}", f"route P92: {num(ref['p92'])}"),
                      annotation_position=lado_rota, annotation_font_color=CINZA)
        layout(fig, 360, showlegend=False, xaxis_title=L("dias até chegar (60 = 60 ou mais)", "days to arrive (60 = 60 or more)"),
               yaxis_title=L("pedidos", "orders"), bargap=0.1)
        st.plotly_chart(fig, width="stretch")
        como_ler(
            f"cada barra mostra quantos pedidos da rota {vend} → {cli} chegaram em cada número de dias. **Em azul, os que "
            "chegariam dentro da promessa do modelo; em vermelho, os que atrasariam.** A linha preta é a promessa do modelo "
            "e a tracejada cinza é a promessa do jeito simples.",
            f"each bar shows how many orders on the {vend} → {cli} route arrived in each number of days. **Blue bars would "
            "arrive within the model's promise; red ones would be late.** The black line is the model's promise and the "
            "dashed grey one is the simple-way promise.",
        )
        caixa(L(
            "**Por que o modelo não dá sempre o P92 da rota?** Porque nem todo pedido da rota é igual. O histograma mistura "
            "vendedor rápido e lento, pedido leve e pesado. O modelo olha as características desse pedido. Teste: troque o "
            "vendedor de **Rápido** pra **Lento** e veja a promessa subir.",
            "**Why doesn't the model always give the route P92?** Because not every order on the route is the same. The "
            "histogram mixes fast and slow sellers, light and heavy orders. The model looks at this order's features. Try "
            "it: switch the seller from **Fast** to **Slow** and watch the promise go up.",
        ))

    st.markdown("#### " + L("4. Por que esse número", "4. Why this number"))
    contrib = bst.predict(X, pred_contrib=True)[0]
    base, partes = contrib[-1], pd.Series(contrib[:-1], index=M["variaveis"])

    def valor_legivel(v):
        x = linha.iloc[0][v]
        if v in ("seller_state", "customer_state"):
            return str(x)
        if v == "dia_semana":
            return dia_nome(x)
        if pd.isna(x):
            return L("sem histórico", "no history")
        return num(float(x), 1 if v.startswith("vend_manuseio") else 0)

    st.plotly_chart(grafico_cascata(base, partes, bruto, valor_legivel), width="stretch")
    como_ler(
        f"começa na promessa média do modelo ({num(base, 1)} dias). Cada barra é uma característica do pedido: **vermelho "
        f"soma dias, azul tira**. A última barra é o resultado ({num(bruto, 2)}), que arredondado pra cima vira "
        f"**{promessa} dias**.",
        f"starts at the model's average promise ({num(base, 1)} days). Each bar is a feature of the order: **red adds days, "
        f"blue removes them**. The last bar is the result ({num(bruto, 2)}), which rounded up becomes **{promessa} days**.",
    )
    with st.expander(L("Ideias pra testar no simulador", "Ideas to try in the simulator")):
        st.markdown(L(
            """- **SP → SP com vendedor rápido:** a promessa cai bastante. É onde dá pra prometer menos.
- **SP → CE ou SP → AL:** a promessa sobe, porque esses estados têm muito atraso na cauda.
- **Mesmo pedido, P85 × P96:** veja quanto custa em dias ficar mais seguro.
- **Vendedor novo:** sem histórico de despacho, o modelo segue o caminho que aprendeu pra dado ausente. Compare com um vendedor normal da mesma rota.""",
            """- **SP → SP with a fast seller:** the promise drops a lot. That's where you can promise less.
- **SP → CE or SP → AL:** the promise rises, because those states have many long delays.
- **Same order, P85 × P96:** see how many days it costs to be safer.
- **New seller:** with no shipping history, the model follows the path it learned for missing data. Compare with an average seller on the same route.""",
        ))
