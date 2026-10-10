"""Gráficos Plotly com a paleta do projeto (usados em «Comparar ofertas», «Bi-horário compensa?»
e «Preço hora a hora»). Rótulos em palavras: «cêntimos por kWh», «euros em N dias», «parte fixa»."""
from datetime import timedelta

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
        pio.templates[nome] = go.layout.Template(
            data=dict(scatter=[go.Scatter(line=dict(shape="spline", smoothing=0.6, width=3))],
                      pie=[go.Pie(hole=0.55, marker=dict(line=dict(color=p["bg"], width=3)))]),
            layout=dict(
            barcornerradius=10,
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


def _faixas_vazio(fig, inicio, fim, cor, cor_texto=None):
    """Sombreia as horas de vazio (periodos.VAZIO_INICIO → VAZIO_FIM) entre dois instantes.

    Cada faixa com pelo menos 3 horas leva escrita a palavra «vazio» (não depender só da cor).
    """
    dia = inicio.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    ini_v, fim_v = periodos.VAZIO_INICIO, periodos.VAZIO_FIM
    while dia < fim:
        a = max(dia.replace(hour=ini_v.hour, minute=ini_v.minute), inicio)
        b = min(dia.replace(hour=fim_v.hour, minute=fim_v.minute) + timedelta(days=1), fim)
        if a < b:                       # só a parte que cai dentro dos dados
            nome = dict(annotation_text="vazio", annotation_position="top left",
                        annotation_font=dict(color=cor_texto or cor, size=12)) \
                if b - a >= timedelta(hours=3) else {}
            fig.add_vrect(x0=a, x1=b, fillcolor=cor, opacity=0.2, line_width=0, layer="below", **nome)
        dia += timedelta(days=1)


def grafico_omie(hoje, amanha=None, altura=320):
    """Preço OMIE (cêntimos por kWh) em hora de Portugal, com o vazio sombreado e escrito."""
    p = paleta()
    fig = go.Figure()
    hoje = _hora_local(hoje)
    amanha = _hora_local(amanha) if amanha else None
    # «Amanhã» a tracejado: as duas linhas distinguem-se também sem ver as cores
    series = ([("Hoje", hoje, p["primary"], "solid")]
              + ([("Amanhã", amanha, p["gold"], "dot")] if amanha else []))
    for nome, precos, cor, traco in series:
        fig.add_scatter(x=[t for t, _ in precos], y=[v / 10 for _, v in precos], name=nome,
                        mode="lines", line=dict(color=cor, width=2.5, shape="hv", dash=traco),
                        hovertemplate=f"{nome}: %{{y:.2f}} cêntimos por kWh<extra></extra>")
    todos = hoje + (amanha or [])
    _faixas_vazio(fig, todos[0][0], todos[-1][0], p["gold"], p.get("gold-texto"))
    fig.update_layout(template=tema_plotly(), height=altura, yaxis_title="cêntimos por kWh",
                      hovermode="x unified",
                      xaxis=dict(tickformat="%Hh<br>%d/%m", hoverformat="%d/%m às %Hh%M"))
    return fig


def _nome_opcao(linha):
    """'Bi-horário<br>preço fixo': duas linhas curtas em vez de uma comprida (cabe no telemóvel)."""
    return (f"{periodos.NOMES[linha['opcao']]}<br>"
            f"{'preço fixo' if linha['modalidade'] == 'fixo' else 'indexado'}")


def grafico_opcoes(linhas, altura=360, dias=None):
    """Custo de cada opção (energia + parte fixa), das mais baratas às mais caras, com o total escrito."""
    p = paleta()
    nomes = [_nome_opcao(l) for l in linhas]
    totais = [l["total"] for l in linhas]
    fig = go.Figure()
    fig.add_bar(y=nomes, x=[l["energia"] for l in linhas], name="Energia gasta", orientation="h",
                marker_color=p["primary"], hovertemplate="%{x:.2f} €<extra>Energia gasta</extra>")
    fig.add_bar(y=nomes, x=[l["potencia"] for l in linhas], name="Parte fixa (potência)",
                orientation="h", marker_color=p["gold"],
                hovertemplate="%{x:.2f} €<extra>Parte fixa</extra>")
    # o total escrito no fim de cada barra: não é preciso passar o dedo para o ver
    fig.add_scatter(x=totais, y=nomes, mode="text", text=[f" {_euros(t)} €" for t in totais],
                    textposition="middle right", textfont=dict(color=p["text"], size=13),
                    showlegend=False, hoverinfo="skip", cliponaxis=False)
    linha_maior = max(len(parte) for n in nomes for parte in n.split("<br>"))
    esquerda = 12 + 8 * linha_maior                      # espaço para o nome mais longo
    fig.update_layout(template=tema_plotly(), barmode="stack", height=altura,
                      xaxis=dict(title=f"euros em {dias} dias" if dias else "euros",
                                 range=[0, max(totais + [0.01]) * 1.3]),
                      margin=dict(l=esquerda),
                      yaxis=dict(autorange="reversed", automargin=True, ticksuffix="  "))
    return fig


def _rotulos_periodo():
    """Nomes do donut com o que cada período quer dizer (sem mexer em periodos.NOMES)."""
    ini, fim = periodos.VAZIO_INICIO.hour, periodos.VAZIO_FIM.hour
    return {"vazio": f"Vazio: {ini}h às {fim}h, mais barato",
            "fora_vazio": f"Fora de vazio: {fim}h às {ini}h",
            "ponta": "Ponta: 4 horas mais caras",
            "cheias": "Cheias: resto do dia",
            "simples": "Simples: todo o dia"}


def grafico_consumo(consumos, altura=300):
    """Donut: a que horas se gasta (kWh por período), com o total no meio."""
    p = paleta()
    cores = {"vazio": p["gold"], "fora_vazio": p["primary"], "ponta": p["err"],
             "cheias": p["bronze"], "simples": p["primary"]}
    nomes = _rotulos_periodo()
    rotulos = list(consumos)
    total = sum(consumos.values())
    fig = go.Figure(go.Pie(labels=[nomes.get(r, periodos.NOMES[r]) for r in rotulos],
                           values=[consumos[r] for r in rotulos], hole=0.62, sort=False,
                           marker=dict(colors=[cores[r] for r in rotulos]),
                           hovertemplate="%{label}<br>%{value:.0f} kWh · %{percent}<extra></extra>"))
    fig.add_annotation(text=f"<b>{total:,.0f}</b><br>kWh no total".replace(",", " "), x=0.5, y=0.5,
                       xref="paper", yref="paper", showarrow=False, font=dict(size=15, color=p["text"]))
    fig.update_layout(template=tema_plotly(), height=altura, showlegend=True,
                      legend=dict(orientation="v", yanchor="top", y=-0.02, x=0))
    return fig


def grafico_tarifarios(tabela, altura=320, dias=None):
    """Barras dos totais de cada tarifário, com a diferença para o mais barato escrita por cima."""
    p = paleta()
    nomes = [str(n).replace(" (", "<br>(") for n in tabela["Tarifário"]]   # nomes longos em 2 linhas
    fig = go.Figure(go.Bar(
        x=nomes, y=tabela["Total (€)"], marker_color=p["primary"],
        text=[f"mais {_euros(d)} €" if d > 0.005 else "mais barato" for d in tabela["Diferença (€)"]],
        textposition="outside", cliponaxis=False, hovertemplate="%{x}<br>%{y:.2f} €<extra></extra>"))
    fig.update_layout(template=tema_plotly(), height=altura,
                      yaxis_title=f"euros em {dias} dias" if dias else "euros")
    return fig
