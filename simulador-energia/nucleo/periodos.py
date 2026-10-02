"""Períodos horários da ERSE (ciclo diário, BTN) e hora legal portuguesa.

Fonte: ERSE — períodos horários em BTN, ciclo diário (em vigor em 2026).
Todas as horas mostradas no site vêm daqui (texto_intervalos, VAZIO_INICIO/FIM).

Nota para 2027: a ERSE aprovou novos períodos (comunicado de 31/07/2026). Entram por
instalação entre 1/7 e 31/12/2027, o vazio do bi-horário passa a começar às 22h30 e o
tri-horário deixa de distinguir verão e inverno. Nessa altura será preciso mudar as
tabelas e também a regra de datas (não é uma troca simples de horas).
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

LISBOA = ZoneInfo("Europe/Lisbon")

# (início, fim) em hora legal portuguesa; fim exclusivo; 00:00 como fim = meia-noite
VAZIO_INICIO, VAZIO_FIM = time(22, 0), time(8, 0)
_VAZIO = [(VAZIO_INICIO, time(0, 0)), (time(0, 0), VAZIO_FIM)]

BI = {
    "vazio": _VAZIO,
    "fora_vazio": [(VAZIO_FIM, VAZIO_INICIO)],
}

TRI = {
    "inverno": {
        "vazio": _VAZIO,
        "ponta": [(time(9, 0), time(10, 30)), (time(18, 0), time(20, 30))],
        "cheias": [(time(8, 0), time(9, 0)), (time(10, 30), time(18, 0)),
                   (time(20, 30), time(22, 0))],
    },
    "verao": {
        "vazio": _VAZIO,
        "ponta": [(time(10, 30), time(13, 0)), (time(19, 30), time(21, 0))],
        "cheias": [(time(8, 0), time(10, 30)), (time(13, 0), time(19, 30)),
                   (time(21, 0), time(22, 0))],
    },
}

PERIODOS = {"simples": ["simples"], "bi": ["fora_vazio", "vazio"],
            "tri": ["ponta", "cheias", "vazio"]}

NOMES = {"simples": "Simples", "bi": "Bi-horário", "tri": "Tri-horário",
         "fora_vazio": "Fora de vazio", "vazio": "Vazio", "ponta": "Ponta", "cheias": "Cheias"}


def _dentro(hora, intervalo):
    inicio, fim = intervalo
    if fim == time(0, 0):          # até à meia-noite
        return hora >= inicio
    return inicio <= hora < fim


def epoca(momento):
    """'verao' se a hora legal de verão estiver em vigor em Portugal, senão 'inverno'."""
    local = momento.astimezone(LISBOA) if momento.tzinfo else momento.replace(tzinfo=LISBOA)
    return "verao" if local.dst() and local.dst().total_seconds() > 0 else "inverno"


def proxima_mudanca(momento, opcao):
    """Instante (Lisboa) em que o período da opção muda a seguir (procura em passos de 15 min)."""
    atual = periodo(momento, opcao)
    local = momento.astimezone(LISBOA) if momento.tzinfo else momento.replace(tzinfo=LISBOA)
    passo = timedelta(minutes=15)
    t = local.replace(minute=local.minute - local.minute % 15, second=0, microsecond=0) + passo
    for _ in range(4 * 48):
        if periodo(t, opcao) != atual:
            return t
        t += passo
    return None


def periodo(momento, opcao):
    """Período horário ('vazio', 'ponta', …) de um instante, para a opção dada."""
    if opcao == "simples":
        return "simples"
    local = momento.astimezone(LISBOA) if momento.tzinfo else momento.replace(tzinfo=LISBOA)
    hora = local.time()
    tabela = BI if opcao == "bi" else TRI[epoca(local)]
    for nome, intervalos in tabela.items():
        if any(_dentro(hora, i) for i in intervalos):
            return nome
    raise ValueError(f"Hora sem período definido: {hora}")


def horas_por_periodo(opcao, dia=None):
    """Quantas horas de cada período tem um dia (útil para verificar as tabelas)."""
    dia = dia or datetime(2026, 1, 15, tzinfo=LISBOA)
    contagem = {}
    for quarto in range(96):
        instante = dia.replace(hour=quarto // 4, minute=15 * (quarto % 4), second=0, microsecond=0)
        nome = periodo(instante, opcao)
        contagem[nome] = contagem.get(nome, 0) + 0.25
    return contagem


def _hora(t):
    return f"{t:%H:%M}" if t != time(0, 0) else "24:00"


def texto_intervalos(opcao, nome, estacao="inverno"):
    """'09:00–10:30 · 18:00–20:30' — o vazio aparece como '22:00–08:00'."""
    if nome == "vazio":
        return f"{VAZIO_INICIO:%H:%M}–{VAZIO_FIM:%H:%M}"
    tabela = BI if opcao == "bi" else TRI[estacao]
    return " · ".join(f"{a:%H:%M}–{_hora(b)}" for a, b in tabela[nome])


def texto_vazio_curto():
    """'22h–8h' para rótulos curtos."""
    return f"{VAZIO_INICIO.hour}h–{VAZIO_FIM.hour}h"
