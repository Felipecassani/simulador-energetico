"""Calculadora relâmpago: consumo estimado a partir do total e poupança por ano."""
import pytest

from nucleo import impostos, mercado, ofertas as of, relampago, tarifas

ERSE = mercado.carregar_erse_local(2026)
aprox = pytest.approx


def test_kwh_da_fatura_inverte_o_total_da_regulada():
    preco = ERSE["regulada"]["energia_eur_kwh"]["simples"]["simples"]
    pot = tarifas.preco_potencia(ERSE, 6.9) * 30
    total = impostos.com_impostos(250 * preco, pot, 250, 30, 6.9)["total"]
    assert relampago.kwh_da_fatura(total, ERSE) == aprox(250, abs=0.01)
    assert relampago.kwh_da_fatura(1.0, ERSE) == 0.0          # nem paga a potência


def test_poupanca_com_uma_oferta_mais_barata():
    barata = of.Oferta("Alfa", "A1", "Alfa Casa", 6.9, "simples", 0.20, {"simples": 0.10})
    preco = ERSE["regulada"]["energia_eur_kwh"]["simples"]["simples"]
    pot = tarifas.preco_potencia(ERSE, 6.9) * 30
    total = impostos.com_impostos(300 * preco, pot, 300, 30, 6.9)["total"]
    r = relampago.poupanca(total, [barata], ERSE)
    esperado = impostos.com_impostos(300 * 0.10, 0.20 * 30, 300, 30, 6.9)["total"]
    assert r["kwh_mes"] == aprox(300, abs=0.01) and r["melhor_mes"] == aprox(esperado, abs=0.01)
    assert r["poupanca_ano"] == aprox((total - esperado) * 365 / 30, abs=0.1)
    assert relampago.poupanca(0, [barata], ERSE) is None and relampago.poupanca(total, [], ERSE) is None


def test_com_o_consumo_real_a_conta_usa_esse_consumo():
    barata = of.Oferta("Alfa", "A1", "Alfa Casa", 6.9, "simples", 0.20, {"simples": 0.10})
    r = relampago.poupanca(80.0, [barata], ERSE, kwh_real=250)
    esperado = impostos.com_impostos(250 * 0.10, 0.20 * 30, 250, 30, 6.9)["total"]
    assert r["exata"] and r["kwh_mes"] == 250 and r["melhor_mes"] == aprox(esperado)
    assert r["poupanca_ano"] == aprox((80.0 - esperado) * 365 / 30)
    assert not relampago.poupanca(80.0, [barata], ERSE)["exata"]
