"""Histórico de faturas, padrões da E-REDES e cenários (dados fictícios, contas à mão)."""
from datetime import date, datetime, timedelta

import pytest

from nucleo import cenarios, eredes, historico, mercado, ofertas as of, periodos

aprox = pytest.approx
ERSE = mercado.carregar_erse_local(2026)


def _fatura(inicio, dias, kwh, preco=0.15, dia=0.30, empresa="Alfa", vazio=None):
    lido = {"inicio": inicio, "fim": inicio + timedelta(days=dias - 1), "dias": dias, "consumo_total": kwh,
            "preco_energia": preco, "preco_diario": dia, "comercializador": empresa}
    if vazio is not None:
        lido["consumos"] = {"vazio": vazio, "fora_vazio": kwh - vazio}
    return lido


# ---------- histórico
def test_juntar_ordena_tira_repetidas_e_fica_com_12():
    lidas = [_fatura(date(2025, m, 1), 30, 200) for m in range(1, 13)]
    lidas += [_fatura(date(2024, 12, 1), 31, 300), lidas[3], {"consumo_total": None}]
    p = historico.juntar(lidas)
    assert len(p) == 12 and p[0].inicio == date(2025, 1, 1)           # a de 2024 é a mais antiga: sai
    assert [x.inicio for x in p] == sorted(x.inicio for x in p)


def test_resumo_do_ano():
    # inverno (jan) 20 kWh/dia, verão (jul) 10 kWh/dia; preço sobe de 0,15 para 0,18
    lidas = [_fatura(date(2026, 1, 1), 31, 620, preco=0.15), _fatura(date(2026, 7, 1), 31, 310, preco=0.18),
             _fatura(date(2026, 9, 1), 30, 300, preco=0.18, vazio=120)]
    r = historico.resumo(historico.juntar(lidas))
    assert r["kwh"] == 1230 and r["dias"] == 92
    assert r["kwh_ano"] == aprox(1230 / 92 * 365)
    assert r["variacao_sazonal"] == aprox(100.0)                         # 20 / 10 − 1
    assert r["variacao_preco"] == aprox(20.0)                            # 0,18 / 0,15 − 1
    assert r["pct_vazio"] == aprox(40.0)                                 # só a fatura com vazio
    assert len(r["lacunas"]) == 2                                        # fev–jun e agosto em falta
    assert r["maior"].inicio == date(2026, 1, 1)
    custo = 620 * 0.15 + 0.3 * 31 + 310 * 0.18 + 0.3 * 31 + 300 * 0.18 + 0.3 * 30
    assert r["custo_ano"] == aprox(custo / 92 * 365)


# ---------- E-REDES: padrões de um período longo
def _registos(dias=35):
    """0,1 kWh por quarto de hora; aos sábados e domingos o dobro; base noturna = 0,4 kW."""
    inicio = datetime(2026, 1, 1, tzinfo=periodos.LISBOA)
    regs = []
    for q in range(dias * 96):
        t = inicio + timedelta(minutes=15 * q)
        regs.append((t, 0.2 if t.weekday() >= 5 else 0.1))
    return regs


def test_padroes():
    p = eredes.padroes(_registos())
    assert [m["mes"] for m in p["meses"]] == [date(2026, 1, 1), date(2026, 2, 1)]
    assert p["meses"][0]["dias"] == aprox(31)
    assert p["kwh_dia_util"] == aprox(9.6) and p["kwh_dia_fds"] == aprox(19.2)
    assert p["base_kw"] == aprox(0.4)
    assert p["base_kwh_ano"] == aprox(0.4 * 24 * 365)
    assert len(p["mapa"][date(2026, 1, 1)]) == 24
    assert p["dia_maior"][1] == aprox(19.2)


# ---------- cenários
def _ofertas():
    return [of.Oferta("Beta", "B1", "Beta Casa", 6.9, "simples", 0.30, {"simples": 0.12}),
            of.Oferta("Beta", "B1", "Beta Casa", 6.9, "bi", 0.30, {"vazio": 0.08, "fora_vazio": 0.16}),
            of.Oferta("Gama", "G1", "Gama Luz", 5.75, "simples", 0.25, {"simples": 0.13})]


def test_cenarios_sem_perfil_so_simples_e_ordenados():
    lista = cenarios.explorar(300, 6.9, None, None, ERSE, _ofertas(), hoje=date(2026, 10, 1))
    nomes = [c.nome for c in lista]
    assert "Melhor oferta em simples" in nomes and "Melhor oferta em bi-horário" not in nomes
    assert [c.mensal for c in lista] == sorted(c.mensal for c in lista)
    simples = next(c for c in lista if c.nome == "Melhor oferta em simples")
    assert simples.mensal == aprox(0.30 * 30 + 300 * 0.12)              # 45,00 €
    descer = next(c for c in lista if c.nome.startswith("Descer"))
    assert descer.mensal == aprox(0.25 * 30 + 300 * 0.13)               # Gama a 5,75 kVA: 46,50 €


def test_cenarios_com_perfil_e_mais_vazio():
    lista = cenarios.explorar(300, 6.9, 40, None, ERSE, _ofertas(), hoje=date(2026, 10, 1))
    bi = next(c for c in lista if c.nome == "Melhor oferta em bi-horário")
    assert bi.mensal == aprox(9 + 120 * 0.08 + 180 * 0.16)              # 47,40 €
    mais_vazio = next(c for c in lista if c.nome.startswith("Pôr mais"))
    assert mais_vazio.mensal < bi.mensal
    assert all("tri" not in c.detalhe for c in lista)                    # ponta desconhecida



def test_nao_sugere_descer_potencia_se_o_pico_nao_cabe():
    """Caso real: pico de 4,56 kW com 4,6 kVA contratados → descer para 3,45 kVA faria disparar o quadro."""
    lista = cenarios.explorar(250, 4.6, 35, 19, ERSE, _ofertas(), hoje=date(2026, 10, 1), pico_kw=4.56)
    assert not any(c.nome.startswith("Descer") for c in lista)
    juntar = next(c for c in lista if c.nome == "Juntar tudo")
    assert "kVA" not in juntar.detalhe
    com_folga = cenarios.explorar(250, 4.6, 35, 19, ERSE, _ofertas(), hoje=date(2026, 10, 1), pico_kw=2.0)
    assert any(c.nome.startswith("Descer") for c in com_folga)


def test_faturas_bi_e_tri_misturadas_nao_passam_de_100():
    """Auditoria: vazio de todas + ponta só das tri dava 114 % e rebentava os cenários."""
    bi = _fatura(date(2026, 1, 1), 30, 1000, vazio=800)
    tri = {"inicio": date(2026, 2, 1), "fim": date(2026, 3, 2), "dias": 30, "consumo_total": 100,
           "preco_energia": 0.15, "preco_diario": 0.3, "consumos": {"vazio": 20, "ponta": 40, "cheias": 40}}
    r = historico.resumo(historico.juntar([bi, tri]))
    assert r["pct_vazio"] == aprox(20.0) and r["pct_ponta"] == aprox(40.0)       # só a tri
    assert cenarios.melhor(_ofertas(), 300, 6.9, r["pct_vazio"], r["pct_ponta"], ERSE) is not None
