"""Gráficos de «O teu ano» e de «Como pagar menos» (Plotly com a paleta do site)."""
import plotly.graph_objects as go

from interface.estilo import paleta
from interface.graficos import tema_plotly
from nucleo.eredes import DIAS_SEMANA

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _mes(d):
    return f"{MESES[d.month - 1]} {d.year % 100:02d}"


def _euros(v):
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def grafico_faturas(periodos_, altura=320):
    """Gasto por dia em cada fatura (barras) e preço de cada kWh, em cêntimos (linha)."""
    p = paleta()
    x = [f"{q.inicio:%d/%m/%y}" if q.inicio else f"fatura {i + 1}" for i, q in enumerate(periodos_)]
    fig = go.Figure()
    fig.add_bar(x=x, y=[q.kwh_dia for q in periodos_], name="Gasto por dia (kWh)", marker_color=p["primary"],
                hovertemplate="%{y:.1f} kWh por dia<extra></extra>")
    precos = [q.preco_kwh for q in periodos_]
    if any(v is not None for v in precos):
        fig.add_scatter(x=x, y=[v * 100 if v is not None else None for v in precos],
                        name="Preço de cada kWh (cêntimos)", yaxis="y2", mode="lines+markers",
                        line=dict(color=p["gold"], width=3),
                        hovertemplate="%{y:.2f} cêntimos por kWh<extra></extra>")
    fig.update_layout(template=tema_plotly(), height=altura, bargap=0.25,
                      yaxis=dict(title="Gasto por dia (kWh)"),
                      yaxis2=dict(title="cêntimos por kWh", overlaying="y", side="right", showgrid=False))
    return fig


def grafico_meses(meses, altura=320):
    """E-REDES: gasto de cada mês (barras) e parte gasta nas horas baratas (linha)."""
    p = paleta()
    x = [_mes(m["mes"]) for m in meses]
    fig = go.Figure()
    fig.add_bar(x=x, y=[m["kwh"] for m in meses], name="Gasto no mês (kWh)", marker_color=p["primary"],
                hovertemplate="%{y:.0f} kWh<extra></extra>")
    fig.add_scatter(x=x, y=[m["pct_vazio"] for m in meses], name="% nas horas baratas", yaxis="y2",
                    mode="lines+markers", line=dict(color=p["gold"], width=3),
                    hovertemplate="%{y:.0f} % nas horas baratas<extra></extra>")
    fig.update_layout(template=tema_plotly(), height=altura, bargap=0.25, yaxis=dict(title="kWh"),
                      yaxis2=dict(title="% nas horas baratas", overlaying="y", side="right", showgrid=False,
                                  range=[0, 100]))
    return fig


def mapa_calor(mapa, altura=360):
    """Gasto médio por dia em cada hora (linhas) e mês (colunas).

    A escala vai da cor do fundo dos cartões ao carmim nos dois temas: «quanto mais vermelho, mais
    gastas» é verdade no claro e no escuro (no escuro, as faixas mais escuras são as de MENOS gasto).
    """
    p = paleta()
    meses = list(mapa)
    z = [[mapa[m][h] for m in meses] for h in range(24)]
    fig = go.Figure(go.Heatmap(
        z=z, x=[_mes(m) for m in meses], y=[f"{h:02d}h" for h in range(24)],
        colorscale=[[0, p["surface-2"]], [0.5, p["bronze"]], [1, p["primary"]]],
        colorbar=dict(title="kWh por dia"), hovertemplate="%{x} · %{y}: %{z:.2f} kWh por dia<extra></extra>"))
    fig.update_layout(template=tema_plotly(), height=altura, yaxis=dict(autorange="reversed"))
    return fig


def grafico_semana(por_dia, altura=260):
    p = paleta()
    cores = [p["bronze"]] * 5 + [p["gold"]] * 2
    fig = go.Figure(go.Bar(x=list(DIAS_SEMANA), y=[v or 0 for v in por_dia], marker_color=cores,
                           hovertemplate="%{x}: %{y:.1f} kWh por dia<extra></extra>"))
    fig.update_layout(template=tema_plotly(), height=altura, yaxis=dict(title="kWh por dia"))
    return fig


def grafico_cenarios(cenarios_, atual=None, altura=None, nomes=None):
    """Custo por mês de cada mudança (barras horizontais com o valor escrito), com o que se paga hoje.

    `nomes` (opcional) traduz o nome de um cenário para o que aparece no eixo.
    """
    p = paleta()
    traduzir = nomes or {}
    nomes = [traduzir.get(c.nome, c.nome) for c in cenarios_][::-1]
    valores = [c.mensal for c in cenarios_][::-1]
    cores = [p["ok"] if atual is not None and v < atual else p["bronze"] for v in valores]
    fig = go.Figure(go.Bar(x=valores, y=nomes, orientation="h", marker_color=cores,
                           text=[f"{_euros(v)} €" for v in valores], textposition="outside", cliponaxis=False,
                           customdata=[c.detalhe for c in cenarios_][::-1],
                           hovertemplate="%{y}: %{x:.2f} € por mês<br>%{customdata}<extra></extra>"))
    if atual is not None:
        fig.add_vline(x=atual, line=dict(color=p["primary"], width=2, dash="dash"),
                      annotation_text="hoje pagas", annotation_position="top")
    maximo = max(valores + ([atual] if atual is not None else []), default=0)
    fig.update_layout(template=tema_plotly(), height=altura or 70 + 38 * len(nomes),
                      xaxis=dict(title="€ por mês, sem IVA", range=[0, maximo * 1.2 if maximo > 0 else 1]))
    return fig
