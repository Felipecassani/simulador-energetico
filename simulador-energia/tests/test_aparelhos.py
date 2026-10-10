"""Estimativa pelos aparelhos — contas à mão."""
import pytest

from nucleo import aparelhos

aprox = pytest.approx


def test_kwh_de_um_aparelho():
    # frigorífico de 150 W a trabalhar 8 h por dia: 0,15 kW × 8 h × 30 dias = 36 kWh
    assert aparelhos.kwh_mes(150, 8) == aprox(36.0)
    assert aparelhos.kwh_mes(-100, 5) == 0 and aparelhos.kwh_mes(100, -1) == 0


def test_so_contam_os_marcados_e_ficam_ordenados():
    total, detalhe = aparelhos.estimar([
        ("Frigorífico", True, 150, 8),        # 36 kWh
        ("Forno", True, 2000, 0.3),           # 18 kWh
        ("Arca", False, 120, 8),              # não marcado
    ])
    assert total == aprox(54.0)
    assert [n for n, _ in detalhe] == ["Frigorífico", "Forno"]


def test_lista_tem_valores_validos():
    assert all(a.potencia_w > 0 and 0 < a.horas_dia <= 24 for a in aparelhos.APARELHOS)
    nomes = [a.nome for a in aparelhos.APARELHOS]
    assert len(nomes) == len(set(nomes))
