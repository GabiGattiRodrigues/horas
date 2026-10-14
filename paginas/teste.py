"""Teste de conversão: o que a base não responde e o desenho do teste A/B."""
import pandas as pd
import streamlit as st

from horas_app.comum import em_uma_frase, como_ler, caixa, L, LINKS, pct, resultados


def render():
    em_uma_frase(
        "a base não diz se prometer menos vende mais. Isso só um teste A/B mede, e aqui está o desenho dele.",
        "the data cannot say whether promising less sells more. Only an A/B test measures that, and here is its design.",
    )
    R = resultados()
    ufs = pd.DataFrame(R["por_q"]["0.92"]["ufs"])
    share = ufs[ufs.customer_state.isin(["SP", "MG"])].pedidos.sum() / R["n_teste"]

    st.markdown("#### " + L("Impacto do prazo prometido na conversão", "Impact of the promised lead time on conversion"))
    st.markdown(L(
        "A base só tem pedido fechado. Não tem sessão, carrinho nem desistência, então não dá pra estimar quanto de venda se "
        "ganha prometendo menos. Por isso a recomendação de encurtar começa com um teste, e não com uma estimativa de receita.",
        "The data only has completed orders. There are no sessions, carts or drop-offs, so there's no way to estimate how much "
        "revenue a shorter promise brings. That's why the recommendation to shorten starts with a test, not a revenue estimate.",
    ))
    st.markdown(L(
        "O que a análise já entrega pro teste: **onde encurtar, quanto encurtar e qual piso de pontualidade não pode ser furado.**",
        "What the analysis already gives the test: **where to shorten, by how much, and which on-time floor must not be breached.**",
    ))

    c1, c2 = st.columns(2)
    with c1.container(border=True):
        st.markdown(L("**HIPÓTESE · Prometer menos converte mais**", "**HYPOTHESIS · A shorter promise converts better**"))
        st.markdown(L(
            f"Mostrar **2 dias a menos** de prazo em SP e MG aumenta a conversão sem derrubar o % no prazo. Os dois estados somam "
            f"**{pct(share, 0)}** dos pedidos.",
            f"Showing **2 fewer days** of lead time in SP and MG increases conversion without hurting the on-time rate. Both "
            f"states account for **{pct(share, 0)}** of orders.",
        ))
    with c2.container(border=True):
        st.markdown(L("**BRAÇOS · Promessa atual × calibrada**", "**ARMS · Current × calibrated promise**"))
        st.markdown(L(
            "Controle vê a promessa de hoje. Tratamento vê a promessa calibrada no P92. A divisão é por cliente, pra mesma pessoa "
            "não ver dois prazos diferentes.",
            "Control sees today's promise. Treatment sees the promise calibrated at P92. Split by customer, so the same person "
            "never sees two different lead times.",
        ))
    c3, c4 = st.columns(2)
    with c3.container(border=True):
        st.markdown(L("**MÉTRICA PRINCIPAL · Conversão de quem calculou o frete**", "**PRIMARY METRIC · Conversion after shipping quote**"))
        st.markdown(L(
            "Sessões que informaram o CEP e viram o prazo, divididas pelas que viraram pedido. É o momento em que a promessa pesa na decisão.",
            "Sessions that entered a ZIP code and saw the lead time, over those that became an order. That's the moment the "
            "promise weighs on the decision.",
        ))
    with c4.container(border=True):
        st.markdown("**GUARDRAILS · " + L("O que não pode piorar**", "What must not get worse**"))
        st.markdown(L(
            "% no prazo de pelo menos **90% por UF**, % de avaliações de 1 e 2 estrelas e contatos no atendimento por atraso. Se a semana do "
            "tratamento sair do limite do gráfico de controle, o teste pausa.",
            "On-time rate of at least **90% per state**, share of 1–2 star ratings, and delay-related support contacts. If the "
            "treatment's week falls outside the control chart limit, the test pauses.",
        ))
    with st.container(border=True):
        st.markdown(L("**AMOSTRA E LEITURA · Desenho no DaVinci, leitura no Michelangelo**",
                      "**SAMPLE AND READOUT · Design in DaVinci, readout in Michelangelo**"))
        st.markdown(L(
            "O tamanho de amostra e a duração saem da conversão de base da loja e do menor ganho que vale a pena, calculados no "
            f"[DaVinci]({LINKS['davinci']}). A leitura do resultado é bayesiana, no [Michelangelo]({LINKS['michelangelo']}): "
            "chance de o tratamento converter mais e quanto se ganha.",
            "Sample size and duration come from the store's baseline conversion and the smallest gain worth detecting, "
            f"calculated in [DaVinci]({LINKS['davinci']}). The readout is Bayesian, in [Michelangelo]({LINKS['michelangelo']}): "
            "the probability that treatment converts better and by how much.",
        ))

    st.markdown("#### " + L("O que este projeto não afirma", "What this project does not claim"))
    st.markdown(L(
        """
    - O ganho de conversão com promessa mais curta é hipótese até o teste medir.
    - A relação entre folga e avaliação é observacional. A avaliação esperada mostra o sentido, não o tamanho exato do efeito.
    - A política de estimativa da Olist muda ao longo do tempo, então a comparação é sempre com a promessa que existia em cada mês.
    - Pedidos de agosto de 2018 têm menos tempo de observação até o corte da base.
    """,
        """
    - The conversion gain from a shorter promise is a hypothesis until the test measures it.
    - The slack–rating relationship is observational. The expected rating shows direction, not the exact effect size.
    - Olist's estimation policy changes over time, so the comparison is always against the promise in place each month.
    - August 2018 orders have less observation time before the data cut-off.
    """,
    ))
