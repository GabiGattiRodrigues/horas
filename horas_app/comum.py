"""Coisas que todas as páginas usam: idioma, cores, leitura dos artefatos e formatação."""
import json
from pathlib import Path

import lightgbm as lgb
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
ART = RAIZ / "artifacts"
ASSETS = RAIZ / "assets"

AZUL = "#1f5fbf"
AZUL_CLARO = "#9dbbe6"
AZUL_FUNDO = "#e8f0fb"
CINZA = "#8a96a3"
CINZA_CLARO = "#d7e0ea"
VERMELHO = "#c0392b"
VERDE = "#1b7a47"
TINTA = "#10233a"

LINKS = {
    "davinci": "https://testeabdesenho.streamlit.app",
    "michelangelo": "https://testeabmensuracao.streamlit.app",
    "dashboard": "https://dashboardinteligente.streamlit.app",
    "github": "https://github.com/GabiGattiRodrigues/horas",
    "notebook": "https://nbviewer.org/github/GabiGattiRodrigues/horas/blob/main/horas_promessa_de_entrega.ipynb",
}


def L(pt: str, en: str) -> str:
    """Texto em português ou inglês, conforme o idioma escolhido na barra lateral."""
    return en if st.session_state.get("lang") == "en" else pt


def lang() -> str:
    return st.session_state.get("lang", "pt")


def pct(v: float, casas: int = 1) -> str:
    s = f"{v * 100:.{casas}f}%"
    return s if lang() == "en" else s.replace(".", ",")


def num(v: float, casas: int = 0) -> str:
    s = f"{v:,.{casas}f}"
    if lang() == "en":
        return s
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def dias(v: float, casas: int = 0) -> str:
    return num(v, casas) + (" days" if lang() == "en" else " dias")


VARIAVEIS_NOME = {
    "km": ("distância vendedor → cliente (km)", "seller → customer distance (km)"),
    "seller_state": ("UF do vendedor", "seller state"),
    "customer_state": ("UF do cliente", "customer state"),
    "dia_semana": ("dia da semana da compra", "purchase weekday"),
    "frete": ("valor do frete (R$)", "freight value (R$)"),
    "peso": ("peso do pedido (g)", "order weight (g)"),
    "qtd_itens": ("itens no pedido", "items in the order"),
    "vend_manuseio_mediana": ("dias que o vendedor costuma levar pra despachar", "days the seller usually takes to ship"),
    "vend_manuseio_p90": ("dias de despacho do vendedor nos piores casos (P90)", "seller's shipping days in the worst cases (P90)"),
    "vend_pedidos": ("pedidos do vendedor no histórico", "seller's orders in history"),
}

DIAS_SEMANA = (["seg", "ter", "qua", "qui", "sex", "sáb", "dom"], ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])


def nome_var(v: str) -> str:
    pt, en = VARIAVEIS_NOME.get(v, (v, v))
    return L(pt, en)


@st.cache_data
def resultados() -> dict:
    return json.loads((ART / "resultados.json").read_text(encoding="utf-8"))


@st.cache_data
def metodo() -> dict:
    return json.loads((ART / "metodo.json").read_text(encoding="utf-8"))


@st.cache_data
def arvores() -> pd.DataFrame:
    return pd.read_csv(ART / "arvores.csv")


@st.cache_data
def arvore_didatica() -> pd.DataFrame:
    return pd.read_csv(ART / "arvore_didatica.csv")


@st.cache_data
def importancia() -> pd.Series:
    return pd.read_csv(ART / "importancia.csv", index_col=0)["ganho"]


@st.cache_data
def pedidos() -> pd.DataFrame:
    return pd.read_csv(ART / "pedidos_ago2018.csv")


@st.cache_data
def simulador_ref() -> dict:
    return json.loads((ART / "simulador.json").read_text(encoding="utf-8"))


@st.cache_resource
def modelo(q: str = "p92") -> lgb.Booster:
    """Modelo de agosto/2018. p92 é o principal; p85 e p96 existem só pro simulador."""
    arquivo = "modelo_ago2018.txt" if q == "p92" else f"modelo_ago2018_{q}.txt"
    return lgb.Booster(model_file=str(ART / arquivo))


@st.cache_resource
def modelo_didatico() -> lgb.Booster:
    return lgb.Booster(model_file=str(ART / "modelo_didatico.txt"))


def matriz_modelo(linhas: pd.DataFrame) -> pd.DataFrame:
    """Monta as variáveis no formato que o modelo espera (UFs como categoria, na mesma ordem do treino)."""
    m = metodo()
    X = linhas[m["variaveis"]].copy()
    for c in ["seller_state", "customer_state"]:
        X[c] = X[c].astype(pd.CategoricalDtype(m["categorias"][c]))
    return X


def layout(fig, altura: int = 420, **kw):
    """Visual padrão dos gráficos: fundo branco, fonte da página, legenda em cima."""
    padrao = dict(
        template="plotly_white", height=altura, paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="sans-serif", size=13, color=TINTA),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_layout(**{**padrao, **kw})
    return fig


CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
.kpi {border:1px solid #E2E8F0; border-radius:12px; padding:14px 16px; background:#F8FAFC; height:100%;}
.kpi .v {font-size:1.7rem; font-weight:700; color:#10233a; line-height:1.2;}
.kpi .l {font-size:.84rem; color:#475569;}
.kpi .d {font-size:.78rem; color:#1f5fbf; margin-top:2px;}
.caixa {border-left:4px solid #1f5fbf; background:#EEF4FC; padding:12px 16px; border-radius:6px; margin:6px 0 16px;}
.caixa.verde {border-left-color:#1b7a47; background:#EEF7F1;}
.caixa.ambar {border-left-color:#b7791f; background:#FDF6EC;}
.passo {border:1px solid #c9dcf6; border-radius:12px; padding:14px; background:#F8FAFC; height:100%;}
.passo h4 {margin:0 0 6px; color:#1f5fbf; font-size:1rem;}
.lerg {font-size:.86rem; color:#475569; background:#F8FAFC; border:1px dashed #c9d6e6; border-radius:8px;
       padding:8px 12px; margin:-4px 0 14px;}
</style>
"""


def kpi(col, valor: str, rotulo: str, detalhe: str = ""):
    """Cartão de número: valor grande, rótulo embaixo e, se tiver, uma linha de comparação."""
    d = f'<div class="d">{detalhe}</div>' if detalhe else ""
    col.markdown(f'<div class="kpi"><div class="v">{valor}</div><div class="l">{rotulo}</div>{d}</div>',
                 unsafe_allow_html=True)


def caixa(texto_md: str, tom: str = ""):
    """Caixa de destaque. Aceita **negrito** simples do markdown."""
    import re
    html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto_md)
    st.markdown(f'<div class="caixa {tom}">{html}</div>', unsafe_allow_html=True)


def em_uma_frase(pt: str, en: str):
    caixa(L("**Em uma frase:** ", "**In one sentence:** ") + L(pt, en))


def como_ler(pt: str, en: str):
    """Instrução curta embaixo de um gráfico, dizendo como ler."""
    import re
    texto = L("👀 <b>Como ler:</b> ", "👀 <b>How to read it:</b> ") + re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", L(pt, en))
    st.markdown(f'<div class="lerg">{texto}</div>', unsafe_allow_html=True)


def passos(itens):
    """Linha de cartões numerados: [(titulo, subtitulo, texto), ...]."""
    cols = st.columns(len(itens))
    for col, (t, sub, d) in zip(cols, itens):
        col.markdown(f'<div class="passo"><h4>{t}</h4><b>{sub}</b><br>{d}</div>', unsafe_allow_html=True)


NOTA_PT = "avaliação de 1 a 5 estrelas"
NOTA_EN = "1-to-5-star review"


def rodape():
    st.divider()
    st.caption(L(
        "Gabriela Gatti Rodrigues · Dados públicos da Olist (CC BY-NC-SA 4.0) · "
        "Pintura: *Horae Serenae*, Edward John Poynter (1894), domínio público.",
        "Gabriela Gatti Rodrigues · Public Olist dataset (CC BY-NC-SA 4.0) · "
        "Painting: *Horae Serenae*, Edward John Poynter (1894), public domain.",
    ))
