"""Fórmulas dos indexados.

Exemplo publicado pela Goldenergy (blogue, "como calcular o kWh indexado"): OMIE 0,0742 €/kWh,
perdas de junho 10 %, QTarifa 0,02425, CG 0,03, TAR 0,06, 300 kWh → energia ≈ 58,80 €.
  (0,0742 × 1,10 + 0,02425 + 0,03 + 0,06) × 300 = 0,19587 × 300 = 58,76 €
"""
import pytest

from nucleo import indexados

aprox = pytest.approx


def test_exemplo_publicado_pela_goldenergy():
    gold = indexados.FORMULAS[0]
    assert (gold.calcular(0.0742, 6) + 0.06) * 300 == aprox(58.76, abs=0.01)


def test_estimar_ordena_e_usa_a_potencia_de_cada_empresa():
    linhas = indexados.estimar(80, 10, 0.0607, 300, 30,
                               {None: 0.40, ("Goldenergy", "Index 04/25"): 0.30})
    custos = [c for _, _, c in linhas]
    assert custos == sorted(custos)
    gold = next(l for l in linhas if l[0].oferta == "Tarifa Index 04/25")
    # (0,080 × 1,10 + 0,05425 + 0,0607) × 300 + 0,30 × 30
    assert gold[2] == aprox((0.080 * 1.10 + 0.05425 + 0.0607) * 300 + 9.0)
