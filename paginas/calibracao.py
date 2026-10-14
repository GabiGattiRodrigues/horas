"""Aba Calibração: o teste das três promessas, a curva de troca e o antes × depois por estado."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horas_app.comum import (AZUL, CINZA, CINZA_CLARO, L, VERDE, VERMELHO, caixa, como_ler, em_uma_frase, kpi, layout,
                             num, passos, pct, resultados)

QS = ["0.85", "0.88", "0.90", "0.92", "0.94", "0.96"]


def _pp(v):
    return ("+" if v > 0 else "") + num(v * 100, 1) + " p.p."


def render():
    R = resultados()
    cv = pd.DataFrame(R["curva"])
    olist = cv[cv.metodo == "olist"].iloc[0]

    em_uma_frase(
        "o modelo acerta o mesmo tanto que a Olist prometendo quase os mesmos dias no total. O ganho é outro: ele tira dias "
        "de quem recebe rápido e dá pra quem costuma atrasar.",
        "the model hits the same on-time rate as Olist with almost the same days in total. The gain is elsewhere: it takes "
        "days away from fast deliveries and gives them to the ones that tend to run late.",
    )

    # ----------------------------------------------------------------- passo 1
    st.markdown("#### " + L("1. As três promessas que comparei", "1. The three promises I compared"))
    passos([
        (L("Promessa atual", "Current promise"), L("o que a Olist mostrava", "what Olist showed"),
         L("O prazo que aparecia pro cliente na hora da compra. É a régua de comparação.",
           "The lead time the customer saw at checkout. It's the benchmark.")),
        (L("Percentil por rota", "Route percentile"), L("o jeito simples", "the simple way"),
         L("Olha os pedidos passados da mesma rota (ex.: SP → RJ) e promete o prazo que 92% deles cumpriram.",
           "Looks at past orders on the same route (e.g. SP → RJ) and promises the lead time 92% of them met.")),
        (L("Modelo (LightGBM)", "Model (LightGBM)"), L("o jeito calibrado", "the calibrated way"),
         L("Faz a mesma conta, mas olhando também distância, peso, frete, dia da compra e se o vendedor costuma demorar.",
           "Does the same, but also looks at distance, weight, freight, purchase day and whether the seller tends to be slow.")),
    ])

    # ----------------------------------------------------------------- passo 2
    st.markdown("#### " + L("2. Como testei", "2. How I tested it"))
    st.markdown(L(
        """Simulei como se cada promessa estivesse em uso de **janeiro a agosto de 2018**. Em cada mês, o método só podia
aprender com os **6 meses anteriores**, como seria na vida real. Depois comparei com o que aconteceu de verdade.

Medi duas coisas:
- **% no prazo:** quantos pedidos chegaram dentro do que foi prometido. Quanto maior, melhor.
- **Promessa média:** quantos dias, em média, foram prometidos. Quanto menor, melhor pro cliente na hora de comprar.

As duas brigam entre si: **pra acertar mais, tem que prometer mais dias.** Então a pergunta certa é: quem acerta mais
prometendo o mesmo tanto?""",
        """I simulated each promise being in use from **January to August 2018**. Each month, the method could only learn
from the **previous 6 months**, as in real life. Then I compared it with what actually happened.

I measured two things:
- **% on time:** how many orders arrived within the promise. Higher is better.
- **Average promise:** how many days were promised on average. Lower is better for the customer at checkout.

The two pull against each other: **to hit more, you have to promise more days.** So the right question is: who hits
more while promising the same?""",
    ))

    # ----------------------------------------------------------------- passo 3
    st.markdown("#### " + L("3. No total, quase empate", "3. Overall, nearly a tie"))
    fig = go.Figure()
    for metodo_, nome, cor in [("rota", L("Percentil por rota", "Route percentile"), CINZA),
                               ("quantilica", L("Modelo (LightGBM)", "Model (LightGBM)"), AZUL)]:
        c = cv[cv.metodo == metodo_]
        fig.add_scatter(x=c.dias, y=c.no_prazo, mode="lines+markers+text", name=nome, line=dict(color=cor, width=2.5),
                        marker=dict(size=9), text=[f"P{round(q * 100)}" for q in c.q], textposition="top left",
                        textfont=dict(size=10, color=cor),
                        hovertemplate="%{text}<br>%{x:.1f} " + L("dias", "days") + "<br>%{y:.1%}<extra>" + nome + "</extra>")
    fig.add_scatter(x=[olist.dias], y=[olist.no_prazo], mode="markers", name=L("Promessa atual (Olist)", "Current promise (Olist)"),
                    marker=dict(color=VERMELHO, size=16, symbol="diamond"),
                    hovertemplate="Olist<br>%{x:.1f} " + L("dias", "days") + "<br>%{y:.1%}<extra></extra>")
    fig.add_annotation(x=olist.dias, y=olist.no_prazo, ax=60, ay=45, showarrow=True, arrowcolor=VERMELHO,
                       text=L(f"Olist: {num(olist.dias, 1)} dias, {pct(olist.no_prazo)} no prazo",
                              f"Olist: {num(olist.dias, 1)} days, {pct(olist.no_prazo)} on time"), font=dict(color=VERMELHO))
    p92 = cv[(cv.metodo == "quantilica") & (cv.q.round(2) == 0.92)].iloc[0]
    fig.add_annotation(x=p92.dias, y=p92.no_prazo, ax=-90, ay=-45, showarrow=True, arrowcolor=AZUL,
                       text=L(f"Modelo P92: {num(p92.dias, 1)} dias, {pct(p92.no_prazo)}",
                              f"Model P92: {num(p92.dias, 1)} days, {pct(p92.no_prazo)}"), font=dict(color=AZUL))
    layout(fig, 460, xaxis_title=L("promessa média (dias)", "average promise (days)"), yaxis_title=L("% no prazo", "% on time"),
           yaxis_tickformat=".0%")
    st.plotly_chart(fig, width="stretch")
    como_ler(
        "cada bolinha é uma versão do método com um percentil diferente (P85, P90, P92...). Indo pra direita, a promessa "
        "fica mais longa e mais pedidos chegam no prazo. **Uma linha acima da outra é melhor:** com os mesmos dias, mais "
        "pedidos no prazo. O modelo (azul) fica um pouco acima do percentil por rota (cinza), e o losango da Olist fica "
        "quase em cima das duas linhas.",
        "each dot is a version of the method with a different percentile (P85, P90, P92...). Moving right, the promise gets "
        "longer and more orders arrive on time. **A line above the other is better:** same days, more orders on time. The "
        "model (blue) sits slightly above the route percentile (grey), and Olist's diamond sits almost on top of both lines.",
    )
    q_mod = cv[cv.metodo == "quantilica"].sort_values("no_prazo")
    dias_mesma_taxa = float(np.interp(olist.no_prazo, q_mod.no_prazo, q_mod.dias))
    caixa(L(
        f"**Resultado:** pra entregar os mesmos {pct(olist.no_prazo)} no prazo da Olist, o modelo promete "
        f"{num(dias_mesma_taxa, 1)} dias em média, contra {num(olist.dias, 1)} da Olist. **Menos de 1 dia de diferença.** "
        "A promessa da Olist já era razoável no total.",
        f"**Result:** to deliver the same {pct(olist.no_prazo)} on time as Olist, the model promises "
        f"{num(dias_mesma_taxa, 1)} days on average, versus Olist's {num(olist.dias, 1)}. **Less than 1 day apart.** "
        "Olist's promise was already reasonable overall.",
    ))

    # ----------------------------------------------------------------- passo 4
    st.markdown("#### " + L("4. Onde o modelo ganha: estado por estado", "4. Where the model wins: state by state"))
    st.markdown(L(
        "No total quase não muda, mas olhando por estado muda bastante. O modelo **tira dias de onde a entrega é rápida** "
        "e **dá pra onde ela costuma atrasar**. Os dias que saem de SP entram no RJ, na BA e no Nordeste, e no total as "
        "contas quase se anulam.",
        "Overall it barely changes, but by state it changes a lot. The model **takes days away where delivery is fast** "
        "and **gives them where it tends to run late**. The days removed from SP go to RJ, BA and the Northeast, and in "
        "total they nearly cancel out.",
    ))
    q = st.select_slider(
        L("Escolha o percentil da promessa calibrada", "Choose the percentile of the calibrated promise"), options=QS,
        value="0.92", format_func=lambda v: f"P{round(float(v) * 100)}", key="calib_q",
        help=L("P92 = prometer o prazo que 92 de cada 100 pedidos parecidos cumprem. Subir o percentil deixa a promessa mais "
               "segura e mais longa. O P92 é o que empata com a pontualidade atual da Olist.",
               "P92 = promising the lead time that 92 of every 100 similar orders meet. A higher percentile makes the promise "
               "safer and longer. P92 is the one that matches Olist's current on-time rate."),
    )
    d = R["por_q"][q]
    c = st.columns(4)
    kpi(c[0], pct(d["geral_nova"]), L("chegam no prazo", "arrive on time"),
        L(f"hoje: {pct(d['geral_atual'])} ({_pp(d['geral_nova'] - d['geral_atual'])})",
          f"today: {pct(d['geral_atual'])} ({_pp(d['geral_nova'] - d['geral_atual'])})"))
    kpi(c[1], num(d["dias_nova"], 1) + L(" dias", " days"), L("de promessa média", "average promise"),
        L(f"hoje: {num(d['dias_atual'], 1)} dias", f"today: {num(d['dias_atual'], 1)} days"))
    kpi(c[2], num(d["sd_nova"] * 100, 1) + " p.p.", L("de diferença de pontualidade entre estados", "on-time gap between states"),
        L(f"hoje: {num(d['sd_atual'] * 100, 1)} p.p.", f"today: {num(d['sd_atual'] * 100, 1)} p.p."))
    kpi(c[3], num(d["nota_nova"], 2) + " ★", L("de avaliação média esperada (1 a 5)", "expected average review (1 to 5)"),
        L(f"hoje: {num(d['nota_atual'], 2)} ★", f"today: {num(d['nota_atual'], 2)} ★"))
    with st.expander(L("O que é cada número desses?", "What is each of these numbers?")):
        st.markdown(L(
            """- **Chegam no prazo:** % dos pedidos de jan a ago/2018 que chegariam dentro da promessa calibrada.
- **Promessa média:** quantos dias, em média, a promessa calibrada mostraria pro cliente.
- **Diferença de pontualidade entre estados:** o desvio-padrão do % no prazo entre os estados. Quanto menor, mais parecida
  é a experiência de quem compra de SP e de quem compra do CE. Hoje, entre o melhor e o pior estado, a diferença passa de 15 pontos.
- **Avaliação média esperada:** uma simulação. Pega a média de estrelas que cada faixa de atraso ou folga teve no
  Diagnóstico e aplica na folga que a promessa calibrada geraria. Mostra pra que lado vai, não é efeito medido.""",
            """- **Arrive on time:** % of Jan–Aug 2018 orders that would arrive within the calibrated promise.
- **Average promise:** how many days, on average, the calibrated promise would show the customer.
- **On-time gap between states:** the standard deviation of on-time rate across states. Lower means buying in SP and in
  CE feels more alike. Today the best and worst states are more than 15 points apart.
- **Expected average review:** a simulation. It takes the average stars each delay or slack band had in the Diagnosis
  and applies them to the slack the calibrated promise would produce. It shows the direction, not a measured effect.""",
        ))

    u = pd.DataFrame(d["ufs"]).sort_values("no_prazo_atual")
    fig = go.Figure()
    for _, r in u.iterrows():
        fig.add_shape(type="line", x0=r.no_prazo_atual, x1=r.no_prazo_nova, y0=r.customer_state, y1=r.customer_state,
                      line=dict(color=CINZA_CLARO, width=4), layer="below")
    fig.add_scatter(x=u.no_prazo_atual, y=u.customer_state, mode="markers", name=L("Promessa atual (Olist)", "Current promise (Olist)"),
                    marker=dict(color=CINZA, size=13), customdata=u.promessa_atual,
                    hovertemplate="%{y}: %{x:.1%}<br>" + L("promessa típica", "typical promise") + ": %{customdata} " + L("dias", "days") + "<extra></extra>")
    fig.add_scatter(x=u.no_prazo_nova, y=u.customer_state, mode="markers", name=L("Promessa calibrada", "Calibrated promise"),
                    marker=dict(color=AZUL, size=13), customdata=u.promessa_nova,
                    hovertemplate="%{y}: %{x:.1%}<br>" + L("promessa típica", "typical promise") + ": %{customdata} " + L("dias", "days") + "<extra></extra>")
    for _, r in u.iterrows():
        dd = r.dif_dias
        fig.add_annotation(x=1.0, xref="paper", y=r.customer_state, xanchor="left", showarrow=False,
                           text=(f"{dd:+.0f} " + (L("dia", "day") if abs(dd) == 1 else L("dias", "days")) if dd else "±0"),
                           font=dict(color=VERDE if dd < 0 else "#4c6179", size=12))
    fig.add_vline(x=0.90, line_dash="dash", line_color=VERDE, annotation_text="90%", annotation_position="top")
    layout(fig, 520, xaxis_tickformat=".0%", xaxis_title=L("% no prazo", "% on time"), margin=dict(l=10, r=80, t=40, b=10))
    st.plotly_chart(fig, width="stretch")
    como_ler(
        "cada linha é um estado do cliente. A bolinha **cinza** é a pontualidade hoje, a **azul** é com a promessa "
        "calibrada. O número à direita é quanto a promessa típica muda: **verde é promessa menor**, cinza é maior. A linha "
        "verde tracejada marca 90% no prazo.",
        "each row is a customer state. The **grey** dot is today's on-time rate, the **blue** one is with the calibrated "
        "promise. The number on the right is how much the typical promise changes: **green is a shorter promise**, grey is "
        "longer. The dashed green line marks 90% on time.",
    )

    ex = u.set_index("customer_state")
    frases = []
    for uf in ["SP", "RJ", "BA"]:
        if uf in ex.index:
            r = ex.loc[uf]
            sentido = L("cai", "drops") if r.promessa_nova < r.promessa_atual else L("sobe", "rises")
            frases.append(L(
                f"- **{uf}:** a promessa típica {sentido} de {num(r.promessa_atual)} pra {num(r.promessa_nova)} dias, "
                f"e o no prazo vai de {pct(r.no_prazo_atual)} pra {pct(r.no_prazo_nova)}.",
                f"- **{uf}:** the typical promise {sentido} from {num(r.promessa_atual)} to {num(r.promessa_nova)} days, "
                f"and on-time goes from {pct(r.no_prazo_atual)} to {pct(r.no_prazo_nova)}.",
            ))
    st.markdown(L("**Três exemplos com o percentil escolhido:**", "**Three examples with the chosen percentile:**") + "\n" + "\n".join(frases))

    # ----------------------------------------------------------------- passo 5
    st.markdown("#### " + L("5. Qual percentil usar?", "5. Which percentile to use?"))
    linhas = []
    for qq in QS:
        dd = R["por_q"][qq]
        linhas.append({
            L("percentil", "percentile"): f"P{round(float(qq) * 100)}",
            L("chegam no prazo", "arrive on time"): dd["geral_nova"] * 100,
            L("promessa média (dias)", "average promise (days)"): round(dd["dias_nova"], 1),
            L("diferença entre estados (p.p.)", "gap between states (p.p.)"): round(dd["sd_nova"] * 100, 1),
            L("avaliação esperada", "expected review"): round(dd["nota_nova"], 2),
        })
    linhas.append({
        L("percentil", "percentile"): L("Olist hoje", "Olist today"),
        L("chegam no prazo", "arrive on time"): R["por_q"]["0.92"]["geral_atual"] * 100,
        L("promessa média (dias)", "average promise (days)"): round(R["por_q"]["0.92"]["dias_atual"], 1),
        L("diferença entre estados (p.p.)", "gap between states (p.p.)"): round(R["por_q"]["0.92"]["sd_atual"] * 100, 1),
        L("avaliação esperada", "expected review"): round(R["por_q"]["0.92"]["nota_atual"], 2),
    })
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch",
                 column_config={L("chegam no prazo", "arrive on time"): st.column_config.NumberColumn(format="%.1f%%"),
                                L("avaliação esperada", "expected review"): st.column_config.NumberColumn(format="%.2f ★"),
                                L("promessa média (dias)", "average promise (days)"): st.column_config.NumberColumn(format="%.1f"),
                                L("diferença entre estados (p.p.)", "gap between states (p.p.)"): st.column_config.NumberColumn(format="%.1f")})
    caixa(L(
        "**Escolhi o P92** porque ele empata com a pontualidade que a Olist já entrega. Assim a comparação fica justa: "
        "mesma taxa no prazo, promessa distribuída de outro jeito. Se o negócio quiser errar menos, sobe pra P94 ou P96 e "
        "aceita prometer uns dias a mais. A decisão é de negócio, a tabela mostra o preço de cada opção.",
        "**I chose P92** because it matches the on-time rate Olist already delivers. That keeps the comparison fair: same "
        "on-time rate, promise distributed differently. If the business wants fewer misses, it can go to P94 or P96 and "
        "accept promising a few more days. It's a business decision; the table shows the price of each option.",
    ), "verde")
