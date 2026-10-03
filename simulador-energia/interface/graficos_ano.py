"""Gráficos de "O teu ano" e de "Explorar possibilidades" (Plotly com a paleta do site)."""
import plotly.graph_objects as go

from interface.estilo import paleta
from interface.graficos import tema_plotly
from nucleo.eredes import DIAS_SEMANA

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _mes(d):
    return f"{MESES[d.month - 1]} {d.year % 100:02d}"


def grafico_faturas(periodos_, altura=320):
    """Consumo por dia em cada fatura (barras) e preço médio da energia (linha)."""
    p = paleta()
    x = [f"{q.inicio:%d/%m/%y}" if q.inicio else f"fatura {i + 1}" for i, q in enumerate(periodos_)]
    fig = go.Figure()
    fig.add_bar(x=x, y=[q.kwh_dia for q in periodos_], name="kWh por dia", marker_color=p["primary"],
                hovertemplate="%{y:.1f} kWh/dia<extra></extra>")
    precos = [q.preco_kwh for q in periodos_]
    if any(v is not None for v in precos):
        fig.add_scatter(x=x, y=[v * 100 if v is not None else None for v in precos], name="Preço (c€/kWh)",
                        yaxis="y2", mode="lines+markers", line=dict(color=p["gold"], width=3),
                        hovertemplate="%{y:.2f} c€/kWh<extra></extra>")
    fig.update_layout(template=tema_plotly(), height=altura, bargap=0.25,
                      yaxis=dict(title="kWh por dia"),
                      yaxis2=dict(title="c€/kWh", overlaying="y", side="right", showgrid=False))
    return fig


def grafico_meses(meses, altura=320):
    """E-REDES: consumo de cada mês (barras) e % em vazio (linha)."""
    p = paleta()
    x = [_mes(m["mes"]) for m in meses]
    fig = go.Figure()
    fig.add_bar(x=x, y=[m["kwh"] for m in meses], name="kWh no mês", marker_color=p["primary"],
                hovertemplate="%{y:.0f} kWh<extra></extra>")
    fig.add_scatter(x=x, y=[m["pct_vazio"] for m in meses], name="% em vazio", yaxis="y2",
                    mode="lines+markers", line=dict(color=p["gold"], width=3),
                    hovertemplate="%{y:.0f} % em vazio<extra></extra>")
    fig.update_layout(template=tema_plotly(), height=altura, bargap=0.25, yaxis=dict(title="kWh"),
                      yaxis2=dict(title="% vazio", overlaying="y", side="right", showgrid=False,
                                  range=[0, 100]))
    return fig


def mapa_calor(mapa, altura=360):
    """Consumo médio por dia em cada hora (linhas) e mês (colunas)."""
    p = paleta()
    meses = list(mapa)
    z = [[mapa[m][h] for m in meses] for h in range(24)]
    fig = go.Figure(go.Heatmap(
        z=z, x=[_mes(m) for m in meses], y=[f"{h:02d}h" for h in range(24)],
        colorscale=[[0, p["surface-2"]], [0.5, p["bronze"]], [1, p["primary"]]],
        colorbar=dict(title="kWh"), hovertemplate="%{x} · %{y}: %{z:.2f} kWh<extra></extra>"))
    fig.update_layout(template=tema_plotly(), height=altura, yaxis=dict(autorange="reversed"))
    return fig


def grafico_semana(por_dia, altura=260):
    p = paleta()
    cores = [p["bronze"]] * 5 + [p["gold"]] * 2
    fig = go.Figure(go.Bar(x=list(DIAS_SEMANA), y=[v or 0 for v in por_dia], marker_color=cores,
                           hovertemplate="%{x}: %{y:.1f} kWh<extra></extra>"))
    fig.update_layout(template=tema_plotly(), height=altura, yaxis=dict(title="kWh por dia"))
    return fig


def grafico_cenarios(cenarios_, atual=None, altura=None):
    """Custo por mês de cada cenário (barras horizontais), com o contrato atual como referência."""
    p = paleta()
    nomes = [c.nome for c in cenarios_][::-1]
    valores = [c.mensal for c in cenarios_][::-1]
    cores = [p["ok"] if atual is not None and v < atual else p["bronze"] for v in valores]
    fig = go.Figure(go.Bar(x=valores, y=nomes, orientation="h", marker_color=cores,
                           customdata=[c.detalhe for c in cenarios_][::-1],
                           hovertemplate="%{y}: %{x:.2f} €/mês<br>%{customdata}<extra></extra>"))
    if atual is not None:
        fig.add_vline(x=atual, line=dict(color=p["primary"], width=2, dash="dash"),
                      annotation_text="o teu contrato", annotation_position="top")
    fig.update_layout(template=tema_plotly(), height=altura or 70 + 38 * len(nomes),
                      xaxis=dict(title="€ por mês (sem IVA)"))
    return fig
