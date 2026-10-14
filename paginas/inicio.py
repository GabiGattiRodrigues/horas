"""Aba O caso: o problema, a solução em 4 passos e os números principais."""
import streamlit as st

from horas_app.comum import L, LINKS, caixa, em_uma_frase, kpi, num, passos, pct, resultados


def render():
    R = resultados()
    q92 = R["por_q"]["0.92"]

    em_uma_frase(
        "a promessa de prazo atual acerta na média, mas erra a distribuição. Dá pra prometer menos onde a entrega é "
        "rápida e ser mais honesto onde ela atrasa, sem piorar a pontualidade geral.",
        "the current delivery promise is right on average but wrong in distribution. You can promise less where delivery "
        "is fast and be more honest where it runs late, without hurting overall on-time performance.",
    )

    st.markdown("#### " + L("O problema", "The problem"))
    st.markdown(L(
        """Quando o cliente coloca o CEP no carrinho, o site mostra um prazo: "chega em até 20 dias". Esse número pode errar pros dois lados:

- **Curto demais:** o pedido chega depois do prometido. O cliente reclama, liga no atendimento e dá uma avaliação ruim.
- **Longo demais:** o pedido chega bem antes, mas na hora de comprar o cliente viu um prazo enorme. Pode ter desistido e comprado em outro lugar.

A pergunta do case: **quantos dias prometer pra cada pedido?**""",
        """When the customer enters their ZIP code at checkout, the site shows a lead time: "arrives within 20 days". That number can be wrong in two ways:

- **Too short:** the order arrives after the promised date. The customer complains, calls support and leaves a bad review.
- **Too long:** the order arrives well ahead, but at checkout the customer saw a huge lead time. They may have given up and bought elsewhere.

The case question: **how many days should each order promise?**""",
    ))

    c = st.columns(4)
    kpi(c[0], num(R["resumo"]["pedidos"]), L("pedidos reais da Olist analisados", "real Olist orders analyzed"))
    kpi(c[1], pct(R["resumo"]["no_prazo"]), L("chegam dentro do prazo prometido hoje", "arrive within the promised date today"))
    kpi(c[2], num(R["resumo"]["folga"]) + L(" dias", " days"),
        L("de folga no pedido típico: chega 12 dias antes do prometido", "of slack on the typical order: arrives 12 days early"))
    kpi(c[3], "−" + pct(1 - q92["sd_nova"] / q92["sd_atual"], 0),
        L("na diferença de pontualidade entre estados com a promessa calibrada", "in the on-time gap between states with the calibrated promise"))

    st.markdown("#### " + L("Como a solução foi montada", "How the solution was built"))
    passos([
        (L("1 · Diagnóstico", "1 · Diagnosis"), L("onde sobra e onde falta", "where there's too much and too little"),
         L("Comparei o prazo prometido com o prazo real, estado por estado, e quanto o atraso derruba a avaliação.",
           "Compared promised vs actual lead time, state by state, and how much delays hurt reviews.")),
        (L("2 · Calibração", "2 · Calibration"), L("um prazo pra cada pedido", "one lead time per order"),
         L("Um modelo estima o prazo que 92% dos pedidos parecidos cumprem, olhando rota, distância, peso, frete e vendedor.",
           "A model estimates the lead time 92% of similar orders meet, looking at route, distance, weight, freight and seller.")),
        (L("3 · Monitoramento", "3 · Monitoring"), L("alarme pra semana ruim", "an alarm for bad weeks"),
         L("Um gráfico de controle mostra quando a pontualidade sai do normal e a promessa precisa ser revista.",
           "A control chart shows when on-time performance leaves normal range and the promise needs review.")),
        (L("4 · Teste", "4 · Test"), L("o que a base não responde", "what the data can't answer"),
         L("Se prometer menos vende mais, só um teste A/B mede. A aba Teste de conversão traz o desenho.",
           "Whether promising less sells more only an A/B test can tell. The Conversion test tab has the design.")),
    ])

    st.markdown("#### " + L("O que a análise mostrou", "What the analysis found"))
    st.markdown(L(
        """
1. **No total, a promessa atual já é razoável.** Com a mesma pontualidade, o modelo promete só cerca de 1 dia a menos na média.
2. **O ganho está em como a promessa se distribui.** SP e MG podem prometer 2 dias a menos e continuar acima de 90% no prazo.
   RJ, BA e o Nordeste precisam de uma promessa mais longa e honesta. A diferença de pontualidade entre estados cai pela metade.
3. **Atraso derruba a avaliação, folga a mais não sobe.** Com 8 dias ou mais de atraso, quase 80% das avaliações são de 1 ou 2 estrelas.
   Chegar 8 ou 22 dias antes dá a mesma avaliação.
4. **A base não responde se prometer menos vende mais.** Ela só tem pedido fechado. Por isso a recomendação de encurtar vira um teste A/B.
""",
        """
1. **Overall, the current promise is already reasonable.** At the same on-time rate, the model promises only about 1 day less on average.
2. **The gain is in how the promise is distributed.** São Paulo and Minas Gerais can promise 2 fewer days and stay above 90% on time.
   Rio, Bahia and the Northeast need a longer, more honest promise. The on-time gap between states is cut in half.
3. **Delays sink reviews, extra slack doesn't lift them.** With 8+ days of delay, almost 80% of reviews are 1 or 2 stars.
   Arriving 8 or 22 days early gets the same review.
4. **The data can't say whether promising less sells more.** It only has completed orders. That's why the recommendation to shorten becomes an A/B test.
""",
    ))

    caixa(L(
        "**Por onde começar:** quem quer o resultado, vai em **Diagnóstico** e **Calibração**. Quem quer brincar, vai no "
        "**Simulador**: monta um pedido e vê quanto o modelo prometeria e por quê. Quem quer entender o método do zero, "
        "vai em **Como funciona**.",
        "**Where to start:** for the results, go to **Diagnosis** and **Calibration**. To play with it, go to the "
        "**Simulator**: build an order and see what the model would promise and why. To understand the method from "
        "scratch, go to **How it works**.",
    ), "verde")

    with st.expander(L("De onde veio a ideia", "Where the idea came from")):
        st.markdown(L(
            "Nasceu de uma pergunta que ficou aberta num case de logística: quanto dá pra encurtar a promessa antes de saber o "
            "efeito na venda? Refiz do zero com base pública, sem nenhum dado de empresa. Os CSVs da Olist não ficam no "
            f"repositório. O notebook com toda a análise está no [GitHub]({LINKS['github']}).",
            "It came from a question left open in a logistics case: how much can the promise be shortened before knowing the "
            "effect on sales? I rebuilt it from scratch on public data, with no company data. The Olist CSVs aren't stored in "
            f"the repository. The notebook with the full analysis is on [GitHub]({LINKS['github']}).",
        ))
