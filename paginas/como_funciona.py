"""Aba Como funciona: o método explicado do zero, com exemplo pequeno, a árvore didática e as árvores do modelo."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horas_app.arvores import dot_arvore
from horas_app.comum import (AZUL, AZUL_CLARO, CINZA, L, VERDE, VERMELHO, arvore_didatica, arvores, caixa, como_ler,
                             dias, em_uma_frase, importancia, layout, metodo, nome_var, num, pct)


def render():
    M = metodo()
    Q = M["q"]

    em_uma_frase(
        "o modelo aprende, com os pedidos que já foram entregues, o prazo que 92 de cada 100 pedidos parecidos cumprem. "
        "As abas abaixo explicam isso do zero, em 5 passos, sempre com números reais da base.",
        "the model learns, from orders already delivered, the lead time that 92 of every 100 similar orders meet. "
        "The tabs below explain it from scratch, in 5 steps, always with real numbers from the data.",
    )

    abas = st.tabs([
        L("1 · A ideia", "1 · The idea"),
        L("2 · Percentil por rota", "2 · Route percentile"),
        L("3 · Uma árvore", "3 · One tree"),
        L("4 · Muitas árvores", "4 · Many trees"),
        L("5 · Como validei", "5 · How I validated it"),
        L("Conceitos", "Concepts"),
    ])


    # --------------------------------------------------------------------------- 1. a ideia
    with abas[0]:
        st.subheader(L("Prometer o prazo que cobre 92% dos pedidos", "Promise the lead time that covers 92% of orders"))
        st.markdown(L(
            "Pegando 13 pedidos reais da rota São Paulo → Rio de Janeiro. Cada barra é um pedido, e a altura é quantos dias ele "
            "levou pra chegar. Mexa no prazo prometido e veja quantos chegariam dentro dele.",
            "Taking 13 real orders on the São Paulo → Rio de Janeiro route. Each bar is an order, and its height is how many "
            "days it took to arrive. Move the promised lead time and see how many would arrive within it.",
        ))
        y = np.array([p["prazo_real"] for p in M["treze_pedidos"]])
        prom = st.slider(L("Prazo prometido (dias)", "Promised lead time (days)"), 1, 45, 14, key="prom_exemplo")
        no_prazo = y <= prom
        atraso = np.clip(y - prom, 0, None).sum()
        folga = np.clip(prom - y, 0, None).sum()
        multa = Q * atraso + (1 - Q) * folga

        fig = go.Figure(go.Bar(x=[f"#{i + 1}" for i in range(len(y))], y=y,
                               marker_color=[AZUL if ok else VERMELHO for ok in no_prazo],
                               hovertemplate="%{x}: %{y} " + L("dias", "days") + "<extra></extra>"))
        fig.add_hline(y=prom, line_color="#10233a", line_dash="dash",
                      annotation_text=L(f"prometido: {prom} dias", f"promised: {prom} days"), annotation_position="top left")
        layout(fig, 340, showlegend=False, yaxis_title=L("dias até chegar", "days to arrive"))
        st.plotly_chart(fig, width="stretch")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(L("No prazo", "On time"), f"{no_prazo.sum()} {L('de', 'of')} {len(y)}", help=pct(no_prazo.mean()))
        c2.metric(L("Dias de atraso somados", "Total days late"), num(atraso))
        c3.metric(L("Dias de folga somados", "Total days of slack"), num(folga))
        c4.metric(L("Multa", "Penalty"), num(multa, 2),
                  help=L("0,92 × dias de atraso + 0,08 × dias de folga", "0.92 × days late + 0.08 × days of slack"))

        st.markdown(L(
            "**A regra da multa.** Imagine que cada dia de atraso custa 92 centavos e cada dia de folga custa 8 centavos. "
            "Atrasar é 11,5 vezes mais caro que sobrar. Então vale prometer um pouco mais, mas não infinitamente mais, porque "
            "folga também custa.",
            "**The penalty rule.** Imagine each day of delay costs 92 cents and each day of slack costs 8 cents. Being late is "
            "11.5 times more expensive than having slack. So it's worth promising a bit more, but not endlessly more, because "
            "slack also costs.",
        ))
        grade = np.arange(1, 46)
        curva = [Q * np.clip(y - g, 0, None).sum() + (1 - Q) * np.clip(g - y, 0, None).sum() for g in grade]
        melhor = int(grade[int(np.argmin(curva))])
        fig = go.Figure(go.Scatter(x=grade, y=curva, mode="lines", line=dict(color=AZUL, width=2.5),
                                   hovertemplate=L("prometer %{x} dias", "promise %{x} days") + "<br>" + L("multa", "penalty") + ": %{y:.2f}<extra></extra>"))
        fig.add_scatter(x=[melhor], y=[min(curva)], mode="markers+text", marker=dict(color=VERDE, size=13),
                        text=[L(f"menor multa: {melhor} dias", f"lowest penalty: {melhor} days")], textposition="top center")
        fig.add_scatter(x=[prom], y=[multa], mode="markers", marker=dict(color="#10233a", size=11, symbol="x"))
        layout(fig, 320, showlegend=False, xaxis_title=L("prazo prometido (dias)", "promised lead time (days)"),
               yaxis_title=L("multa total", "total penalty"))
        st.plotly_chart(fig, width="stretch")
        st.markdown(L(
            f"A multa é menor em **{melhor} dias**, que cobre 12 dos 13 pedidos (92%). Não é coincidência: com essa regra de "
            "92 contra 8, a promessa que deixa a multa menor é sempre o **percentil 92** dos prazos. O pedido de 43 dias fica "
            "de fora. Cobrir ele obrigaria a prometer 43 dias pra todo mundo.",
            f"The penalty is lowest at **{melhor} days**, which covers 12 of the 13 orders (92%). It's no coincidence: with this "
            "92-versus-8 rule, the promise with the lowest penalty is always the **92nd percentile** of lead times. The 43-day "
            "order is left out. Covering it would mean promising 43 days to everyone.",
        ))
        st.info(L(
            "**Por que 92%?** É a pontualidade que a Olist já entrega hoje. Usando o mesmo nível, a comparação fica justa: mesma "
            "taxa no prazo, promessa distribuída de outro jeito. Na aba **Calibração** dá pra testar outros percentis.",
            "**Why 92%?** It's the on-time rate Olist already delivers today. Using the same level keeps the comparison fair: "
            "same on-time rate, promise distributed differently. On the **Calibration** tab you can try other percentiles.",
        ), icon="🎯")
        st.markdown(L(
            "**O resto do método é só isso feito com mais cuidado.** Em vez de um número pra todo mundo, um número pra cada "
            "tipo de pedido. A próxima aba começa pelo jeito mais simples de separar os pedidos: pela rota.",
            "**The rest of the method is just this done more carefully.** Instead of one number for everyone, one number for "
            "each kind of order. The next tab starts with the simplest way to split orders: by route.",
        ))


    # --------------------------------------------------------------------------- 2. percentil por rota
    with abas[1]:
        st.subheader(L("Um P92 pra cada rota", "One P92 per route"))
        st.markdown(L(
            f"O primeiro método faz a conta da aba 1 separado por rota (UF do vendedor → UF do cliente), usando os pedidos "
            f"entregues de {M['treino_de']} a {M['treino_ate']}. Rota com menos de 50 pedidos usa o P92 da UF do cliente.",
            f"The first method does tab 1's calculation separately for each route (seller state → customer state), using "
            f"orders delivered from {M['treino_de']} to {M['treino_ate']}. Routes with fewer than 50 orders use the customer "
            "state's P92.",
        ))
        r = pd.DataFrame(M["p92_por_rota"])
        fig = go.Figure()
        fig.add_bar(y=r.rota.str.replace(">", " → "), x=r.mediana, orientation="h", name=L("prazo mediano", "median lead time"),
                    marker_color=AZUL_CLARO)
        fig.add_bar(y=r.rota.str.replace(">", " → "), x=r.p92, orientation="h", name=L("P92 (a promessa)", "P92 (the promise)"),
                    marker_color=AZUL)
        layout(fig, 420, barmode="group", xaxis_title=L("dias", "days"))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, width="stretch")
        st.caption(L("As 10 rotas com mais pedidos. Repare como o P92 fica longe da mediana em rotas como SP → RJ: a cauda é longa.",
                     "The 10 routes with the most orders. Notice how far the P92 sits from the median on routes like SP → RJ: the tail is long."))

        st.subheader(L("O problema: dentro da mesma rota, os pedidos são diferentes", "The catch: within the same route, orders differ"))
        v = pd.DataFrame(M["vendedor_rapido_lento"])
        nomes = {"rapido": L("rápido (até 1 dia)", "fast (up to 1 day)"), "medio": L("médio (2 a 3 dias)", "average (2–3 days)"),
                 "lento": L("lento (4 dias ou mais)", "slow (4+ days)")}
        v["faixa_nome"] = v.faixa.map(nomes)
        fig = go.Figure(go.Bar(x=v.faixa_nome, y=v.p92, marker_color=[AZUL_CLARO, AZUL, "#0f3d80"], text=v.p92.map(lambda d: dias(d)),
                               textposition="outside", customdata=v.pedidos,
                               hovertemplate="%{x}<br>P92: %{y} " + L("dias", "days") + "<br>" + L("pedidos", "orders") + ": %{customdata:,}<extra></extra>"))
        layout(fig, 340, showlegend=False, yaxis_title=L("P92 do prazo (dias)", "lead-time P92 (days)"),
               xaxis_title=L("quanto o vendedor costuma demorar pra despachar", "how long the seller usually takes to ship"))
        st.plotly_chart(fig, width="stretch")
        rap, len_ = v.set_index("faixa").p92["rapido"], v.set_index("faixa").p92["lento"]
        st.markdown(L(
            f"Na rota SP → RJ, quem compra de um vendedor rápido recebe 92% dos pedidos em {dias(rap)}. De um vendedor lento, "
            f"em {dias(len_)}. O percentil por rota dá a mesma promessa pros dois. Erra pra mais num e pra menos no outro.",
            f"On the SP → RJ route, buying from a fast seller gets 92% of orders delivered within {dias(rap)}. From a slow "
            f"seller, within {dias(len_)}. The route percentile gives both the same promise. Too long for one, too short for the other.",
        ))
        st.markdown(L(
            "Dá pra ir quebrando em mais grupos (rota × vendedor × peso × ...), mas os grupos ficam pequenos rápido e o "
            "percentil de um grupo com 15 pedidos não vale muito. É aí que entra a árvore: ela escolhe sozinha quais "
            "quebras valem a pena.",
            "You could keep splitting into more groups (route × seller × weight × ...), but groups get small fast, and the "
            "percentile of a 15-order group isn't worth much. That's where the tree comes in: it picks on its own which splits are worth it.",
        ))


    # --------------------------------------------------------------------------- 3. uma árvore
    with abas[2]:
        st.subheader(L("Uma árvore é um jogo de perguntas de sim ou não", "A tree is a game of yes-or-no questions"))
        st.markdown(L(
            "A árvore testa todas as perguntas possíveis sobre o pedido (\"o cliente é do Nordeste?\", \"a distância passa de "
            "500 km?\") e escolhe a que melhor separa pedidos rápidos de lentos. Depois repete dentro de cada lado. Em cada "
            "folha, a promessa é o P92 dos pedidos que caíram ali, exatamente a conta da aba 1.",
            "The tree tries every possible question about the order (\"is the customer in the Northeast?\", \"is the distance "
            "over 500 km?\") and picks the one that best separates fast orders from slow ones. Then it repeats inside each side. "
            "In each leaf, the promise is the P92 of the orders that landed there, exactly tab 1's calculation.",
        ))
        st.markdown(L(
            "Esta é uma árvore de verdade, treinada nos mesmos pedidos do modelo, mas limitada a 3 perguntas pra caber na tela:",
            "This is a real tree, trained on the same orders as the model, but limited to 3 questions to fit on screen:",
        ))
        st.graphviz_chart(dot_arvore(arvore_didatica(), None, didatica=True), width="stretch")
        st.markdown(L(
            "**Lendo a árvore:** a primeira pergunta é a região do cliente. Ela sozinha já separa bastante: Sul, Sudeste e "
            "Centro-Oeste de um lado, Norte e Nordeste do outro. Do lado do Sudeste, a segunda pergunta é se o vendedor costuma "
            "demorar muito pra despachar nos piores casos. Repare que a árvore achou sozinha a mesma coisa da aba 2: vendedor "
            "lento pede promessa maior.",
            "**Reading the tree:** the first question is the customer's region. On its own it already separates a lot: South, "
            "Southeast and Center-West on one side, North and Northeast on the other. On the Southeast side, the second question "
            "is whether the seller tends to take very long to ship in the worst cases. Notice the tree found on its own the same "
            "thing as tab 2: a slow seller calls for a longer promise.",
        ))
        st.warning(L(
            "**O limite de uma árvore só:** 4 folhas quer dizer só 4 promessas possíveis pro Brasil inteiro. Dá pra deixar a "
            "árvore mais funda, mas aí ela começa a decorar os pedidos do treino e erra nos pedidos novos. A saída é a próxima aba.",
            "**The limit of a single tree:** 4 leaves means only 4 possible promises for the whole country. You could make the "
            "tree deeper, but then it starts memorizing training orders and fails on new ones. The way out is the next tab.",
        ), icon="🌳")


    # --------------------------------------------------------------------------- 4. muitas árvores
    with abas[3]:
        st.subheader(L("Boosting: árvores que corrigem o erro umas das outras", "Boosting: trees that fix each other's mistakes"))
        st.markdown(L(
            f"""
    O modelo de verdade é um **LightGBM**, da mesma família do XGBoost. Ele funciona em rodadas:

    1. **Ponto de partida:** a promessa começa no P92 de todos os pedidos do treino, {dias(M['p92_treino'])}.
    2. **Árvore 1:** olha onde esse número único erra e faz perguntas pra corrigir. Pedido do Nordeste? Soma uns dias. Rota curta? Tira uns dias.
    3. **Árvore 2:** olha o que ainda ficou errado depois da árvore 1 e corrige mais um pouco.
    4. **E assim por diante** até {M['n_arvores']} árvores. A promessa final é o ponto de partida mais a soma das correções de todas elas.

    Cada árvore só aplica 5% da correção que acha que falta (o *learning rate*). Isso evita que uma árvore exagere e deixa
    as seguintes ajustarem com calma.
    """,
            f"""
    The real model is a **LightGBM**, from the same family as XGBoost. It works in rounds:

    1. **Starting point:** the promise starts at the P92 of all training orders, {dias(M['p92_treino'])}.
    2. **Tree 1:** looks at where that single number goes wrong and asks questions to fix it. Northeast order? Add a few days. Short route? Remove a few days.
    3. **Tree 2:** looks at what is still wrong after tree 1 and fixes a bit more.
    4. **And so on** up to {M['n_arvores']} trees. The final promise is the starting point plus the sum of all their corrections.

    Each tree applies only 5% of the correction it thinks is missing (the *learning rate*). That keeps any single tree from
    overdoing it and lets the next ones adjust gradually.
    """,
        ))
        st.markdown(L(
            "**O que muda em relação a um boosting comum é a multa.** Um boosting normal minimiza o erro quadrático e acaba "
            "estimando o prazo médio. Aqui ele minimiza a multa de 92 contra 8 da aba 1, então estima o P92 do prazo de cada pedido.",
            "**What changes from regular boosting is the penalty.** Regular boosting minimizes squared error and ends up "
            "estimating the average lead time. Here it minimizes tab 1's 92-versus-8 penalty, so it estimates each order's lead-time P92.",
        ))

        st.subheader(L("O que mais pesa na promessa", "What weighs the most on the promise"))
        imp = importancia().sort_values()
        fig = go.Figure(go.Bar(x=imp.values, y=[nome_var(v) for v in imp.index], orientation="h", marker_color=AZUL,
                               hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
        layout(fig, 400, showlegend=False, xaxis_tickformat=".0%", xaxis_title=L("participação no ganho total das divisões", "share of total split gain"))
        st.plotly_chart(fig, width="stretch")
        st.caption(L("Ganho: quanto cada variável ajudou a reduzir a multa, somando todas as perguntas em que ela aparece nas 300 árvores.",
                     "Gain: how much each variable helped reduce the penalty, adding up every question it appears in across the 300 trees."))

        st.subheader(L("Passeando pelas árvores do modelo", "Browsing the model's trees"))
        arv = arvores()
        base = float(arv[(arv.tree_index == 0) & (arv.node_depth == 1)].value.iloc[0])
        ganho = arv.groupby("tree_index").split_gain.sum()
        n = st.slider(L("Árvore nº", "Tree #"), 0, M["n_arvores"] - 1, 0, key="arvore_n")
        t = arv[arv.tree_index == n]
        inteira = st.toggle(L("Mostrar a árvore inteira", "Show the whole tree"), value=False,
                            help=L("Por padrão aparecem as 2 primeiras perguntas e o resto fica resumido. A árvore inteira tem 31 folhas e fica pequena na tela.",
                                   "By default the first 2 questions show and the rest is summarized. The whole tree has 31 leaves and gets small on screen."))
        st.graphviz_chart(dot_arvore(t, base if n == 0 else None, didatica=False, profundidade=None if inteira else 2),
                          width="stretch")
        folhas = t[t.split_feature.isna()]
        vals = folhas.value - (base if n == 0 else 0)
        st.caption(L(
            f"Árvore {n} de {M['n_arvores']}. Cada caixa é uma pergunta: siga **sim** ou **não**. As folhas mostram quantos "
            f"dias essa árvore soma (vermelho) ou tira (azul) dos pedidos que caem ali. Nesta árvore, o ajuste vai de "
            f"{num(vals.min(), 2)} a +{num(vals.max(), 2)} dia."
            + (f" A árvore 0 já carrega o ponto de partida de {dias(base)}, que foi tirado das folhas pra mostrar só o ajuste." if n == 0 else ""),
            f"Tree {n} of {M['n_arvores']}. Each box is a question: follow **yes** or **no**. Leaves show how many days this "
            f"tree adds (red) or removes (blue) for the orders landing there. In this tree, the adjustment ranges from "
            f"{num(vals.min(), 2)} to +{num(vals.max(), 2)} day."
            + (f" Tree 0 already carries the {dias(base)} starting point, which was taken out of the leaves to show only the adjustment." if n == 0 else ""),
        ))
        st.markdown(L(
            "Nenhuma árvore sozinha decide muita coisa: na maioria dos pedidos, cada uma mexe poucas horas, raramente mais de um dia. "
            "É a soma de 300 ajustes pequenos que "
            "dá a promessa. Na aba **Pedido a pedido** dá pra ver essa soma acontecendo num pedido real.",
            "No single tree decides much: for most orders each one moves a few hours, rarely more than a day. "
            "It's the sum of 300 small adjustments that makes the "
            "promise. On the **Order by order** tab you can watch that sum happen on a real order.",
        ))


    # --------------------------------------------------------------------------- 5. backtest
    with abas[4]:
        st.subheader(L("Testando como se fosse produção", "Testing as if it were production"))
        st.markdown(L(
            "Um modelo avaliado nos mesmos pedidos em que aprendeu sempre parece bom. Pra não me enganar, cada mês de 2018 foi "
            "previsto por um modelo que só viu os 6 meses anteriores. É como o modelo funcionaria de verdade, recalibrado todo mês.",
            "A model evaluated on the same orders it learned from always looks good. To avoid fooling myself, each month of 2018 "
            "was predicted by a model that only saw the previous 6 months. That's how it would really run, recalibrated monthly.",
        ))
        meses = pd.period_range("2018-01", "2018-08", freq="M")
        fig = go.Figure()
        for i, m in enumerate(meses):
            ini, fim = (m - 6).start_time, (m - 1).end_time
            fig.add_shape(type="rect", x0=ini, x1=fim, y0=i - 0.35, y1=i + 0.35, fillcolor=AZUL_CLARO, line_width=0)
            fig.add_shape(type="rect", x0=m.start_time, x1=m.end_time, y0=i - 0.35, y1=i + 0.35, fillcolor=AZUL, line_width=0)
        fig.add_scatter(x=[None], y=[None], mode="markers", marker=dict(color=AZUL_CLARO, size=12, symbol="square"),
                        name=L("treino (6 meses anteriores)", "training (previous 6 months)"))
        fig.add_scatter(x=[None], y=[None], mode="markers", marker=dict(color=AZUL, size=12, symbol="square"),
                        name=L("mês previsto", "predicted month"))
        layout(fig, 340, yaxis=dict(tickvals=list(range(len(meses))), ticktext=[str(m) for m in meses], autorange="reversed"),
               xaxis=dict(type="date", range=["2017-07-01", "2018-09-01"]))
        st.plotly_chart(fig, width="stretch")

        b = pd.DataFrame(M["backtest_por_mes"])
        fig = go.Figure()
        fig.add_scatter(x=b.mes, y=b.no_prazo_atual, mode="lines+markers", name=L("promessa atual (Olist)", "current promise (Olist)"),
                        line=dict(color=CINZA, width=2.5))
        fig.add_scatter(x=b.mes, y=b.no_prazo_nova, mode="lines+markers", name=L("promessa calibrada (P92)", "calibrated promise (P92)"),
                        line=dict(color=AZUL, width=2.5))
        fig.add_hline(y=0.92, line_dash="dot", line_color=VERDE)
        layout(fig, 360, yaxis_tickformat=".0%", yaxis_title=L("% no prazo", "% on time"))
        st.plotly_chart(fig, width="stretch")
        st.markdown(L(
            "**Leitura honesta mês a mês:** em janeiro e fevereiro o modelo cobriu menos do que devia, porque os pedidos "
            "desses meses demoraram mais do que os dos meses em que ele aprendeu. A Olist prometia prazos mais longos nessa "
            "época e segurou melhor. A partir de março o treino já tinha esses atrasos e o modelo passou na frente. Isso reforça "
            "a aba **Monitoramento**: a calibração precisa de um alarme pra quando o padrão muda.",
            "**Honest month-by-month reading:** in January and February the model covered less than it should, because orders "
            "in those months took longer than those in the months it learned from. Olist was promising longer lead times then "
            "and held up better. From March on, training already included those delays and the model pulled ahead. That backs "
            "up the **Monitoring** tab: calibration needs an alarm for when the pattern shifts.",
        ))
        with st.expander(L("Ver a tabela mês a mês", "See the month-by-month table")):
            t = b.rename(columns={"mes": L("mês", "month"), "pedidos": L("pedidos", "orders"),
                                  "no_prazo_atual": L("no prazo atual", "on time current"), "no_prazo_nova": L("no prazo calibrada", "on time calibrated"),
                                  "dias_atual": L("dias atual", "days current"), "dias_nova": L("dias calibrada", "days calibrated")})
            st.dataframe(t, hide_index=True, width="stretch", column_config={
                L("no prazo atual", "on time current"): st.column_config.NumberColumn(format="percent"),
                L("no prazo calibrada", "on time calibrated"): st.column_config.NumberColumn(format="percent"),
                L("dias atual", "days current"): st.column_config.NumberColumn(format="%.1f"),
                L("dias calibrada", "days calibrated"): st.column_config.NumberColumn(format="%.1f"),
            })


    # --------------------------------------------------------------------------- conceitos
    CONCEITOS = [
        (L("📦 Promessa, prazo real e folga", "📦 Promise, actual lead time and slack"), L(
            "**Promessa:** quantos dias o site disse que o pedido ia levar, contando do dia da compra.\n\n"
            "**Prazo real:** quantos dias ele levou de verdade.\n\n"
            "**Folga:** promessa menos prazo real. Prometeu 20 e chegou em 8: folga de 12 dias. Folga negativa é atraso.\n\n"
            "**No prazo:** o pedido chegou no dia prometido ou antes.",
            "**Promise:** how many days the site said the order would take, counting from the purchase day.\n\n"
            "**Actual lead time:** how many days it really took.\n\n"
            "**Slack:** promise minus actual lead time. Promised 20 and arrived in 8: 12 days of slack. Negative slack is a delay.\n\n"
            "**On time:** the order arrived on the promised day or earlier.")),
        (L("⭐ Avaliação (1 a 5 estrelas)", "⭐ Review (1 to 5 stars)"), L(
            "**O que é:** a nota que o cliente dá pro pedido na Olist depois da entrega, de 1 a 5 estrelas. **Não é NPS.**\n\n"
            "**Como uso:** a % de avaliações com 1 ou 2 estrelas funciona como taxa de reclamação. 99% dos pedidos entregues "
            "têm avaliação.",
            "**What it is:** the score the customer gives the order on Olist after delivery, from 1 to 5 stars. **It's not NPS.**\n\n"
            "**How I use it:** the share of 1–2 star reviews works as a complaint rate. 99% of delivered orders have a review.")),
        (L("📐 p.p. (pontos percentuais)", "📐 p.p. (percentage points)"), L(
            "**O que é:** a diferença entre duas porcentagens. Sair de 84% pra 89% no prazo é subir 5 p.p. (e não 5%).",
            "**What it is:** the difference between two percentages. Going from 84% to 89% on time is a 5 p.p. rise (not 5%).")),
        (L("🎯 Percentil (P92)", "🎯 Percentile (P92)"), L(
            "**O que é:** ordene os prazos do menor pro maior. O P92 é o prazo que deixa 92% dos pedidos abaixo dele.\n\n"
            "**Exemplo:** numa fila de 100 pedidos ordenados pelo prazo, o P92 é o prazo do 92º. Prometer esse prazo quer dizer "
            "que 92 em cada 100 chegam dentro.",
            "**What it is:** sort lead times from smallest to largest. The P92 is the lead time with 92% of orders below it.\n\n"
            "**Example:** in a line of 100 orders sorted by lead time, the P92 is the 92nd order's lead time. Promising it means "
            "92 out of every 100 arrive within it.")),
        (L("⚖️ Perda quantílica (a multa)", "⚖️ Quantile loss (the penalty)"), L(
            "**O que é:** a regra que o modelo tenta minimizar. Erro pra menos (prometer menos do que levou) custa 0,92 por dia. "
            "Erro pra mais custa 0,08 por dia.\n\n"
            "**Por que funciona:** com essa regra, o número que deixa a multa menor é sempre o P92. Trocando 0,92 por 0,50, a "
            "regra vira a mediana. Também é chamada de *pinball loss*.",
            "**What it is:** the rule the model tries to minimize. Under-promising costs 0.92 per day. Over-promising costs 0.08 per day.\n\n"
            "**Why it works:** with this rule, the number with the lowest penalty is always the P92. Swap 0.92 for 0.50 and the "
            "rule becomes the median. It's also called *pinball loss*.")),
        (L("🚀 Gradient boosting e LightGBM", "🚀 Gradient boosting and LightGBM"), L(
            "**O que é:** um modelo feito de muitas árvores pequenas em sequência, cada uma corrigindo o erro das anteriores. A "
            "resposta é a soma de todas.\n\n"
            "**LightGBM × XGBoost:** a mesma ideia, em bibliotecas diferentes. O LightGBM cresce a árvore pela folha que mais "
            "reduz o erro e aceita variável categórica direto (aqui, as UFs), sem precisar transformar antes.",
            "**What it is:** a model made of many small trees in sequence, each one fixing the previous ones' mistakes. The answer "
            "is the sum of all of them.\n\n"
            "**LightGBM × XGBoost:** the same idea in different libraries. LightGBM grows the tree from the leaf that most reduces "
            "the error and takes categorical variables directly (here, the states), with no prior transformation.")),
        (L("🔍 SHAP (quanto cada variável somou)", "🔍 SHAP (how much each variable added)"), L(
            "**O que é:** reparte a promessa de um pedido entre as variáveis. Parte da promessa média do modelo e mostra quantos "
            "dias cada informação somou ou tirou.\n\n"
            "**Exemplo:** é como explicar a conta de um restaurante item por item. Prato base, mais a bebida, mais a sobremesa, "
            "menos o desconto. Cada item tem seu pedaço no total.",
            "**What it is:** splits one order's promise across the variables. It starts from the model's average promise and shows "
            "how many days each piece of information added or removed.\n\n"
            "**Example:** like explaining a restaurant bill item by item. Base dish, plus the drink, plus dessert, minus the "
            "discount. Each item has its share of the total.")),
        (L("📈 Gráfico de controle (gráfico p)", "📈 Control chart (p-chart)"), L(
            "**O que é:** acompanha uma proporção (aqui, o % no prazo) semana a semana, com uma faixa do quanto ela varia só por "
            "acaso. A faixa é a média ± 3 desvios-padrão, e fica mais larga em semanas com poucos pedidos.\n\n"
            "**Como ler:** ponto dentro da faixa é variação normal. Ponto fora é sinal de que algo mudou de verdade e vale investigar.",
            "**What it is:** tracks a proportion (here, % on time) week by week, with a band of how much it varies by chance "
            "alone. The band is the average ± 3 standard deviations, and it widens in weeks with few orders.\n\n"
            "**How to read it:** a point inside the band is normal variation. A point outside signals something really changed "
            "and is worth investigating.")),
        (L("📏 Intervalo de confiança de Wilson", "📏 Wilson confidence interval"), L(
            "**O que é:** a margem de erro de uma proporção, como o % de notas 1 e 2 numa faixa de atraso. Funciona melhor que "
            "a fórmula comum quando o grupo é pequeno ou a proporção é perto de 0% ou 100%.\n\n"
            "**Como ler:** se os intervalos de duas faixas não se cruzam, a diferença entre elas dificilmente é acaso.",
            "**What it is:** the margin of error of a proportion, like the share of 1–2 star ratings in a delay band. It works "
            "better than the usual formula when the group is small or the proportion is close to 0% or 100%.\n\n"
            "**How to read it:** if two bands' intervals don't overlap, the difference between them is unlikely to be chance.")),
        (L("🔁 Backtest com janela móvel", "🔁 Rolling-window backtest"), L(
            "**O que é:** pra cada mês testado, treina o modelo só com os meses anteriores e mede o acerto no mês seguinte. "
            "Aqui a janela é de 6 meses.\n\n"
            "**Por que importa:** evita que o modelo \"conheça o futuro\" e mostra como ele se sai quando o padrão muda.",
            "**What it is:** for each tested month, trains the model only on previous months and measures accuracy on the next "
            "month. Here the window is 6 months.\n\n"
            "**Why it matters:** keeps the model from \"knowing the future\" and shows how it does when the pattern shifts.")),
        (L("⭐ Avaliação esperada", "⭐ Expected review"), L(
            "**O que é:** uma simulação. Pega a média de estrelas de cada faixa de folga (por exemplo, \"chegou 1 a 3 dias antes\" dá "
            "4,13) e aplica na folga que cada política de promessa geraria.\n\n"
            "**Cuidado:** mostra o sentido do efeito, não o tamanho exato. A relação entre folga e avaliação é observacional.",
            "**What it is:** a simulation. Takes the average stars of each slack band (for example, \"arrived 1–3 days early\" "
            "averages 4.13) and applies it to the slack each promise policy would produce.\n\n"
            "**Caveat:** it shows the direction of the effect, not its exact size. The slack–review relationship is observational.")),
    ]
    with abas[5]:
        st.subheader(L("Os conceitos usados no projeto", "The concepts used in the project"))
        for titulo, corpo in CONCEITOS:
            with st.expander(titulo):
                st.markdown(corpo)
