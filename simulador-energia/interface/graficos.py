"""Gráficos Plotly com a paleta do projeto (usados em Tarifários, Opções horárias e Gráficos)."""
from datetime import datetime, timedelta

import plotly.graph_objects as go
import plotly.io as pio

from interface.estilo import paleta, tema_atual
from nucleo import periodos

CONFIG = {"displayModeBar": False, "locale": "pt"}


def _euros(v):
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def tema_plotly():
    """Regista (uma vez por tema) e devolve o nome do template Plotly."""
    nome = f"lc-{tema_atual()}"
    if nome not in pio.templates:
        p = paleta()
        pio.templates[nome] = go.layout.Template(layout=dict(
            font=dict(family="Inter, sans-serif", color=p["text"], size=13),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            colorway=[p["primary"], p["gold"], p["bronze"], p["err"], p["muted"]],
            xaxis=dict(gridcolor=p["border"], zerolinecolor=p["border"], linecolor=p["border"]),
            yaxis=dict(gridcolor=p["border"], zerolinecolor=p["border"], linecolor=p["border"],
                       automargin=True),
            hoverlabel=dict(bgcolor=p["surface"], font_color=p["text"]),
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            separators=", ",
        ))
    return nome


def _hora_local(precos):
    """[(hora de relógio sem fuso, €/MWh)], com a hora repetida do fim do verão juntada.

    O Plotly ignora o fuso das datas: no dia de 25 h a hora 01:00–01:45 aparecia duas
    vezes e a linha voltava para trás. Aqui os quartos com a mesma hora de relógio
    passam a ser um só, com a média dos dois preços.
    """
    agrupado = {}
    for instante, valor in precos:
        agrupado.setdefault(instante.replace(tzinfo=None), []).append(valor)
    return [(h, sum(v) / len(v)) for h, v in sorted(agrupado.items())]


def _faixas_vazio(fig, inicio, fim, cor):
    """Sombreia as horas de vazio (periodos.VAZIO_INICIO → VAZIO_FIM) entre dois instantes."""
    dia = inicio.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    ini_v, fim_v = periodos.VAZIO_INICIO, periodos.VAZIO_FIM
    while dia < fim:
        a = max(dia.replace(hour=ini_v.hour, minute=ini_v.minute), inicio)
        b = min(dia.replace(hour=fim_v.hour, minute=fim_v.minute) + timedelta(days=1), fim)
        if a < b:                       # só a parte que cai dentro dos dados
            fig.add_vrect(x0=a, x1=b, fillcolor=cor, opacity=0.12, line_width=0, layer="below")
        dia += timedelta(days=1)


def grafico_omie(hoje, amanha=None, altura=320):
    """Preço OMIE (c€/kWh) em hora de Portugal, com o vazio sombreado."""
    p = paleta()
    fig = go.Figure()
    hoje = _hora_local(hoje)
    amanha = _hora_local(amanha) if amanha else None
    series = [("Hoje", hoje, p["primary"])] + ([("Amanhã", amanha, p["gold"])] if amanha else [])
    for nome, precos, cor in series:
        fig.add_scatter(x=[t for t, _ in precos], y=[v / 10 for _, v in precos], name=nome,
                        mode="lines", line=dict(color=cor, width=2.5, shape="hv"),
                        hovertemplate="%{x|%d/%m %H:%M} · %{y:.2f} c€/kWh<extra></extra>")
    todos = hoje + (amanha or [])
    _faixas_vazio(fig, todos[0][0], todos[-1][0], p["gold"])
    fig.update_layout(template=tema_plotly(), height=altura, yaxis_title="c€/kWh",
                      hovermode="x unified",
                      xaxis=dict(tickformat="%Hh<br>%d/%m", hoverformat="%d/%m %H:%M"))
    return fig


def grafico_opcoes(linhas, altura=360):
    """Custo mensal de cada opção (energia + potência), das mais baratas às mais caras."""
    p = paleta()
    nomes = [f"{periodos.NOMES[l['opcao']]} · {l['modalidade']}" for l in linhas]
    fig = go.Figure()
    fig.add_bar(y=nomes, x=[l["energia"] for l in linhas], name="Energia", orientation="h",
                marker_color=p["primary"], hovertemplate="%{x:.2f} €<extra>Energia</extra>")
    fig.add_bar(y=nomes, x=[l["potencia"] for l in linhas], name="Potência", orientation="h",
                marker_color=p["gold"], hovertemplate="%{x:.2f} €<extra>Potência</extra>")
    esquerda = 12 + 8 * max(len(n) for n in nomes)      # espaço para o nome mais longo
    fig.update_layout(template=tema_plotly(), barmode="stack", height=altura,
                      xaxis_title="€ no período", margin=dict(l=esquerda),
                      yaxis=dict(autorange="reversed", automargin=True, ticksuffix="  "))
    return fig


def grafico_consumo(consumos, altura=300):
    """Donut: onde vai o consumo (kWh por período)."""
    p = paleta()
    cores = {"vazio": p["gold"], "fora_vazio": p["primary"], "ponta": p["err"],
             "cheias": p["bronze"], "simples": p["primary"]}
    rotulos = list(consumos)
    fig = go.Figure(go.Pie(labels=[periodos.NOMES[r] for r in rotulos],
                           values=[consumos[r] for r in rotulos], hole=0.62, sort=False,
                           marker=dict(colors=[cores[r] for r in rotulos]),
                           hovertemplate="%{label}: %{value:.0f} kWh (%{percent})<extra></extra>"))
    fig.update_layout(template=tema_plotly(), height=altura, showlegend=True)
    return fig


def grafico_tarifarios(tabela, altura=320):
    """Barras dos totais de cada tarifário, com a diferença para o mais barato."""
    p = paleta()
    fig = go.Figure(go.Bar(
        x=tabela["Tarifário"], y=tabela["Total (€)"], marker_color=p["primary"],
        text=[f"+{_euros(d)} €" if d > 0.005 else "mais barato" for d in tabela["Diferença (€)"]],
        textposition="outside", hovertemplate="%{x}: %{y:.2f} €<extra></extra>"))
    fig.update_layout(template=tema_plotly(), height=altura, yaxis_title="€ no período")
    return fig
