"""Horas: quanto prometer de prazo de entrega, pedido a pedido. App Streamlit (PT/EN)."""
import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

st.set_page_config(page_title="Horas · quanto prometer de prazo de entrega", page_icon="🕰️", layout="wide")

from horas_app.comum import CSS, L  # noqa: E402
from paginas import (calibracao, como_funciona, diagnostico, inicio, monitoramento, pedido,  # noqa: E402
                     simulador, teste)

st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    _q = str(st.query_params.get("lang", "pt")).lower()
    idioma = st.radio("Idioma / Language", ["PT", "EN"], index=1 if _q == "en" else 0, horizontal=True,
                      label_visibility="collapsed")
    st.session_state.lang = "en" if idioma == "EN" else "pt"
    st.image(str(RAIZ / "assets" / "horas.jpg"), width="stretch")
    st.markdown("### Horas")
    st.caption(L(
        "Quanto prometer de prazo de entrega, pedido a pedido. As Horas eram as deusas gregas da ordem do tempo.",
        "How long a delivery promise should be, order by order. The Horae were the Greek goddesses of the order of time.",
    ))
    st.markdown(L("**Stack:** Python · LightGBM (regressão quantílica) · Plotly · Streamlit",
                  "**Stack:** Python · LightGBM (quantile regression) · Plotly · Streamlit"))
    st.markdown(L("Base pública da Olist, e-commerce brasileiro, com pedidos de 2016 a 2018.",
                  "Public Olist dataset, a Brazilian e-commerce marketplace, with orders from 2016 to 2018."))
    st.markdown("[Portfólio · Gabi Gatti](https://gabigattirodrigues.github.io/)")

st.title(L("Horas · quanto prometer de prazo de entrega?", "Horas · how long should a delivery promise be?"))
st.caption(L(
    "Prometer prazo curto demais atrasa o pedido e derruba a avaliação. Longo demais pode custar a venda. "
    "Aqui, cada pedido ganha uma promessa calibrada com o que já aconteceu com pedidos parecidos.",
    "Promise too short and the order runs late and the review drops. Too long and you may lose the sale. "
    "Here, each order gets a promise calibrated on what already happened to similar orders.",
))

abas = st.tabs([
    L("O caso", "The case"), L("Diagnóstico", "Diagnosis"), L("Calibração", "Calibration"),
    L("Simulador", "Simulator"), L("Pedido a pedido", "Order by order"), L("Monitoramento", "Monitoring"),
    L("Teste de conversão", "Conversion test"), L("Como funciona e glossário", "How it works & glossary"),
])
for aba, pagina in zip(abas, [inicio, diagnostico, calibracao, simulador, pedido, monitoramento, teste, como_funciona]):
    with aba:
        pagina.render()

st.divider()
st.caption(L(
    "Gabriela Gatti Rodrigues · Dados públicos da Olist (CC BY-NC-SA 4.0) · "
    "Pintura: *Horae Serenae*, Edward John Poynter (1894), domínio público.",
    "Gabriela Gatti Rodrigues · Public Olist dataset (CC BY-NC-SA 4.0) · "
    "Painting: *Horae Serenae*, Edward John Poynter (1894), public domain.",
))
