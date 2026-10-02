"""Opções horárias (simples/bi/tri) em fixo e indexado — contas feitas à mão.

Caso: 300 kWh · 40 % em vazio · 15 % em ponta · 30 dias · 6,9 kVA (ERSE 2026)
  potência: 0,3659 × 30 = 10,977 €
  simples fixo: 300 × 0,1654 = 49,62 → 60,597 €
  bi fixo: 120 × 0,1087 + 180 × 0,1988 = 13,044 + 35,784 → 59,805 €
  tri fixo: 120 × 0,1087 + 45 × 0,2495 + 135 × 0,1690 = 47,0865 → 58,0635 €
  indexado com OMIE a 100 €/MWh, sem perdas nem margem (preço = 0,100 + TAR):
    simples: 300 × 0,1607 → 59,187 € · bi: 120 × 0,1158 + 180 × 0,1835 → 57,903 €
    tri: 120 × 0,1158 + 45 × 0,3452 + 135 × 0,1412 → 59,469 €
"""
import pytest

from nucleo import mercado, tarifas

aprox = pytest.approx
ERSE = mercado.carregar_erse_local(2026)
OMIE_100 = {"simples": {"simples": 100.0}, "bi": {"vazio": 100.0, "fora_vazio": 100.0},
            "tri": {"vazio": 100.0, "ponta": 100.0, "cheias": 100.0}}


def _totais(**kw):
    linhas = tarifas.comparar_opcoes(300, 40, 15, 30, 6.9, ERSE, **kw)
    return {(l["opcao"], l["modalidade"]): l for l in linhas}, linhas


def test_fixo_erse_2026():
    t, _ = _totais()
    assert t[("simples", "fixo")]["total"] == aprox(60.597)
    assert t[("bi", "fixo")]["total"] == aprox(59.805)
    assert t[("tri", "fixo")]["total"] == aprox(58.0635)
    assert t[("tri", "fixo")]["potencia"] == aprox(10.977)


def test_indexado_com_omie_constante():
    t, _ = _totais(medias_omie=OMIE_100)
    assert t[("simples", "indexado")]["total"] == aprox(59.187)
    assert t[("bi", "indexado")]["total"] == aprox(57.903)
    assert t[("tri", "indexado")]["total"] == aprox(59.469)


def test_perdas_e_margem_somam_ao_preco():
    p = tarifas.precos_indexados(OMIE_100, ERSE, perdas_pct=10, margem_eur_kwh=0.01)
    assert p["simples"]["simples"] == aprox(0.100 * 1.10 + 0.01 + 0.0607)


def test_ordenado_e_poupanca_face_ao_simples_fixo():
    t, linhas = _totais(medias_omie=OMIE_100)
    assert [l["total"] for l in linhas] == sorted(l["total"] for l in linhas)
    assert t[("simples", "fixo")]["poupanca_vs_simples_fixo"] == 0
    assert t[("bi", "indexado")]["poupanca_vs_simples_fixo"] == aprox(60.597 - 57.903)


def test_sem_omie_so_ha_fixo():
    _, linhas = _totais()
    assert {l["modalidade"] for l in linhas} == {"fixo"} and len(linhas) == 3


def test_distribuicao_nunca_e_50_50_automatica():
    c = tarifas.distribuir_consumo(300, 40, 15)
    assert c["bi"] == {"vazio": 120, "fora_vazio": 180}
    assert c["tri"] == {"vazio": 120, "ponta": 45, "cheias": 135}


@pytest.mark.parametrize("vazio,ponta", [(-1, 0), (101, 0), (60, 50)])
def test_percentagens_invalidas(vazio, ponta):
    with pytest.raises(ValueError):
        tarifas.distribuir_consumo(300, vazio, ponta)


def test_potencia_ate_2_3_kva_usa_preco_simples_proprio():
    assert tarifas.precos_fixos(ERSE, 2.3)["simples"]["simples"] == aprox(0.1620)
    assert tarifas.precos_fixos(ERSE, 6.9)["simples"]["simples"] == aprox(0.1654)
    with pytest.raises(ValueError):
        tarifas.preco_potencia(ERSE, 7.5)


def test_vazio_mais_ponta_a_100_por_cento_nao_rebenta():
    # 333 kWh, 23 % + 77 %: sem o max(0, …) as cheias davam -0,0000000001 e ValueError
    c = tarifas.distribuir_consumo(333, 23, 77)
    assert c["tri"]["cheias"] == 0.0
    tarifas.comparar_opcoes(333, 23, 77, 30, 6.9, ERSE)


def test_proxima_mudanca_de_periodo():
    from datetime import datetime
    from nucleo import periodos
    # 1 de outubro (verão), 14h00: bi fora de vazio até às 22h00
    agora = datetime(2026, 10, 1, 14, 0, tzinfo=periodos.LISBOA)
    assert periodos.periodo(agora, "bi") == "fora_vazio"
    assert periodos.proxima_mudanca(agora, "bi").hour == 22
