"""Desenho das árvores do LightGBM, caminho de um pedido dentro delas e gráficos de explicação."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from horas_app.comum import (AZUL, AZUL_FUNDO, CINZA, DIAS_SEMANA, L, VERDE, VERMELHO, lang, layout, nome_var, num)

NOME_CURTO = {
    "km": ("distância", "distance"), "seller_state": ("UF do vendedor", "seller state"),
    "customer_state": ("UF do cliente", "customer state"), "dia_semana": ("dia da compra", "purchase day"),
    "frete": ("frete", "freight"), "peso": ("peso", "weight"), "qtd_itens": ("itens", "items"),
    "vend_manuseio_mediana": ("despacho típico do vendedor", "seller's typical shipping"),
    "vend_manuseio_p90": ("despacho do vendedor (P90)", "seller's shipping (P90)"),
    "vend_pedidos": ("pedidos do vendedor", "seller's orders"),
}


def nome_curto(v: str) -> str:
    pt, en = NOME_CURTO.get(v, (v, v))
    return L(pt, en)


def dia_nome(d) -> str:
    return DIAS_SEMANA[0 if lang() == "pt" else 1][int(d)]


def limiar_legivel(var: str, thr) -> str:
    t = float(thr)
    if var == "km":
        return f"{num(t)} km"
    if var == "frete":
        return f"R$ {num(t, 2)}"
    if var == "peso":
        return f"{num(t)} g"
    if var.startswith("vend_manuseio"):
        return num(t, 1) + L(" dias", " days")
    if var == "dia_semana":
        return dia_nome(np.floor(t))
    return num(t, 1)


def quebrar(lista: str, n: int = 6) -> str:
    itens = [i.strip() for i in str(lista).split(",")]
    return "\\n".join(", ".join(itens[i:i + n]) for i in range(0, len(itens), n))


def caminho_do_pedido(t: pd.DataFrame, folha: int) -> set:
    """Nós do caminho da raiz até a folha onde o pedido caiu (folha vem do predict com pred_leaf=True)."""
    arvore = int(t.tree_index.iloc[0])
    no = f"{arvore}-L{int(folha)}"
    pais = t.set_index("node_index").parent_index
    caminho = {no}
    while pd.notna(pais.get(no)):
        no = pais[no]
        caminho.add(no)
    return caminho


def dot_arvore(t: pd.DataFrame, base: float | None = None, didatica: bool = False,
               profundidade: int | None = None, caminho: set | None = None) -> str:
    """Desenha uma árvore em graphviz.

    - `base`: valor tirado das folhas da 1ª árvore, que carrega o ponto de partida.
    - `profundidade`: desenha só as primeiras perguntas e resume o resto numa caixa.
    - `caminho`: destaca o caminho de um pedido. Fora do caminho, só aparece o lado oposto resumido.
    """
    sim, nao = L("sim", "yes"), L("não", "no")
    ped = L("pedidos", "orders")
    direcao = "TB" if (didatica or profundidade or caminho) else "LR"
    linhas = ['digraph {', f'rankdir={direcao}; nodesep=0.25; ranksep=0.45; bgcolor="transparent";',
              'node [fontname="Helvetica", fontsize=14, style="filled,rounded", shape=box];',
              'edge [fontname="Helvetica", fontsize=12, color="#6b7785"];']
    por_id = t.set_index("node_index")

    def ajuste(valor):
        return valor - base if base is not None else valor

    def folhas_abaixo(no):
        r = por_id.loc[no]
        if pd.isna(r.split_feature):
            return [r]
        return folhas_abaixo(r.left_child) + folhas_abaixo(r.right_child)

    def resumo(no, apagado=False):
        r = por_id.loc[no]
        fs = folhas_abaixo(no)
        vs = [ajuste(f.value) for f in fs]
        n_perg = len(fs) - 1
        if didatica:
            faixa = L(f"promessas de {num(np.ceil(min(vs)))} a {num(np.ceil(max(vs)))} dias",
                      f"promises from {num(np.ceil(min(vs)))} to {num(np.ceil(max(vs)))} days")
        else:
            mx = ("+" if max(vs) > 0 else "") + num(max(vs), 2)
            faixa = L(f"ajuste de {num(min(vs), 2)} a {mx} dia", f"adjustment from {num(min(vs), 2)} to {mx} day")
        lbl = (L(f"mais {n_perg} pergunta" + ("s" if n_perg > 1 else ""), f"{n_perg} more question" + ("s" if n_perg > 1 else ""))
               + f"\\n{faixa}\\n{num(r['count'])} {ped}")
        cor_txt = ', fontcolor="#8a96a3"' if apagado else ""
        return f'"{no}" [label="{lbl}", fillcolor="#f3f6fa", color="#b9c4d0", style="filled,rounded,dashed"{cor_txt}];'

    def folha(r, no_caminho, apagado):
        cont = num(r["count"])
        if didatica:
            lbl = L(f"prometer {num(np.ceil(r.value))} dias", f"promise {num(np.ceil(r.value))} days") + f"\\n{cont} {ped}"
            cor = AZUL_FUNDO
        else:
            v = ajuste(r.value)
            lbl = f"{'+' if v >= 0 else ''}{num(v, 2)} {L('dia', 'day')}\\n{cont} {ped}"
            cor = "#f6c9cf" if v > 0 else "#c9dcf6"
        extra = ', penwidth=3, color="#10233a"' if no_caminho else ', color="#9aa5b1"'
        if apagado:
            cor, extra = "#f3f6fa", ', color="#d7e0ea", fontcolor="#8a96a3"'
        return f'"{r.name}" [label="{lbl}", fillcolor="{cor}", shape=ellipse{extra}];'

    def pergunta(r):
        nome = nome_var(r.split_feature) if didatica else nome_curto(r.split_feature)
        if r.decision_type == "==":
            return f"{nome} {L('é', 'is')}\\n{quebrar(r.threshold, 6 if didatica else 4)}?"
        return f"{nome}\\n≤ {limiar_legivel(r.split_feature, r.threshold)}?"

    # Quais nós desenhar
    if caminho:
        desenhar = set(caminho)
        for no in caminho:
            r = por_id.loc[no]
            if pd.notna(r.split_feature):
                desenhar |= {r.left_child, r.right_child}
    else:
        desenhar = set(por_id.index)

    for no in por_id.index:
        if no not in desenhar:
            continue
        r = por_id.loc[no]
        no_caminho = bool(caminho) and no in caminho
        apagado = bool(caminho) and not no_caminho
        prof = r.node_depth
        if profundidade and not caminho and prof > profundidade + 1:
            continue
        cortado = pd.notna(r.split_feature) and (
            (profundidade and not caminho and prof == profundidade + 1) or (caminho and not no_caminho))
        if cortado:
            linhas.append(resumo(no, apagado))
        elif pd.isna(r.split_feature):
            linhas.append(folha(r, no_caminho, apagado))
        else:
            borda = ', penwidth=3' if no_caminho else ""
            linhas.append(f'"{no}" [label="{pergunta(r)}", fillcolor="#eef3fb", color="{AZUL}"{borda}];')
            for filho, rot in [(r.left_child, sim), (r.right_child, nao)]:
                if caminho and filho in caminho:
                    linhas.append(f'"{no}" -> "{filho}" [label=" {rot}", penwidth=3, color="{AZUL}", fontcolor="{AZUL}"];')
                else:
                    linhas.append(f'"{no}" -> "{filho}" [label=" {rot}"];')
    linhas.append("}")
    return "\n".join(linhas)


def grafico_cascata(base: float, partes: pd.Series, bruto: float, valor_legivel) -> go.Figure:
    """Cascata do SHAP: da promessa média até o resultado do modelo."""
    principais = list(partes.abs().sort_values(ascending=False).index[:6])
    resto = partes.drop(principais).sum()
    rotulos = ([L("promessa média", "average promise")] + [f"{nome_var(v)} = {valor_legivel(v)}" for v in principais]
               + [L("outras variáveis", "other variables"), L("resultado do modelo", "model output")])
    valores = [base] + [partes[v] for v in principais] + [resto, bruto]
    fig = go.Figure(go.Waterfall(
        orientation="h", y=rotulos, x=valores,
        measure=["absolute"] + ["relative"] * (len(principais) + 1) + ["total"],
        text=[num(base, 1)] + [("+" if v > 0 else "") + num(v, 1) for v in valores[1:-1]] + [num(bruto, 1)],
        textposition="outside",
        increasing=dict(marker=dict(color=VERMELHO)), decreasing=dict(marker=dict(color=AZUL)),
        totals=dict(marker=dict(color="#10233a")), connector=dict(line=dict(color=CINZA, width=1)),
    ))
    acumulado = np.cumsum([base] + [partes[v] for v in principais] + [resto])
    layout(fig, 460, showlegend=False, xaxis_title=L("dias", "days"),
           xaxis=dict(range=[0, max(acumulado.max(), bruto) * 1.15]))
    fig.update_yaxes(autorange="reversed")
    return fig


def grafico_convergencia(booster, X, n_arvores: int, linhas_ref=None) -> go.Figure:
    """Promessa depois de k árvores somadas."""
    ks = [1, 2, 3, 5, 10, 15, 20, 30, 40, 50, 75, 100, 125, 150, 200, 250, n_arvores]
    caminho = [float(booster.predict(X, num_iteration=k)[0]) for k in ks]
    fig = go.Figure()
    fig.add_scatter(x=ks, y=caminho, mode="lines+markers", line=dict(color=AZUL, width=2.5),
                    hovertemplate=L("depois de %{x} árvores", "after %{x} trees") + ": %{y:.1f} " + L("dias", "days") + "<extra></extra>")
    for valor, rotulo, cor, pos in (linhas_ref or []):
        fig.add_hline(y=valor, line_dash="dot", line_color=cor, annotation_text=rotulo, annotation_position=pos)
    layout(fig, 360, showlegend=False, xaxis_title=L("quantidade de árvores somadas", "number of trees added"),
           yaxis_title=L("promessa (dias)", "promise (days)"))
    return fig


def tabela_arvore_por_arvore(booster, X, arv: pd.DataFrame, base: float, n: int = 10) -> pd.DataFrame:
    """As primeiras árvores pra um pedido: em que folha caiu e quanto somou."""
    folhas = booster.predict(X, pred_leaf=True)[0]
    linhas, acumulado = [], 0.0
    for k in range(n):
        t = arv[arv.tree_index == k]
        no = f"{k}-L{int(folhas[k])}"
        valor = float(t.set_index("node_index").loc[no, "value"])
        if k == 0:
            acumulado = valor
            ajuste = valor - base
        else:
            acumulado += valor
            ajuste = valor
        # a pergunta que mais pesou no caminho: a primeira (raiz) da árvore
        raiz = t[t.node_depth == 1].iloc[0]
        linhas.append({
            L("árvore", "tree"): k,
            L("primeira pergunta", "first question"): nome_curto(raiz.split_feature),
            L("ajuste (dias)", "adjustment (days)"): round(ajuste, 2),
            L("promessa até aqui", "promise so far"): round(acumulado, 2),
        })
    return pd.DataFrame(linhas)


VERDE_OK = VERDE
