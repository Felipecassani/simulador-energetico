"""IVA e taxas: caso de validação com os valores de uma fatura real (só números, sem dados pessoais).

258 kWh · 31 dias · 4,6 kVA · energia 258 × 0,1386 = 35,76 € · potência 0,4449 × 31 = 13,79 €
  sem IVA  = 35,76 + 13,79 + CAV 2,85 + DGEG 0,07 + IEC 0,26 + tarifa social 0,53 = 53,26 €
  IVA 6 %  sobre 31,97 € (206,67 kWh de energia e tarifa social + CAV)            =  1,92 €
  IVA 23 % sobre 21,29 € (resto da energia + potência + DGEG + IEC)                =  4,90 €
  total    = 60,08 €   (a fatura diz 60,08 €)
"""
import pytest

from nucleo import impostos

aprox = pytest.approx


def test_fatura_real_bate_ao_centimo():
    r = impostos.com_impostos(258 * 0.1386, 0.4449 * 31, 258, 31, 4.6)
    assert r["sem_iva"] == aprox(53.26, abs=0.01)
    assert r["iva"] == aprox(1.92 + 4.90, abs=0.01)
    assert r["total"] == aprox(60.08, abs=0.01)


def test_potencia_ate_3_45_kva_tem_iva_reduzido():
    baixa = impostos.com_impostos(0, 10, 0, 30, 3.45)
    alta = impostos.com_impostos(0, 10, 0, 30, 4.6)
    assert alta["iva"] - baixa["iva"] == aprox(10 * (0.23 - 0.06))


def test_acima_de_6_9_kva_a_energia_paga_iva_normal():
    r = impostos.com_impostos(100, 0, 500, 30, 10.35)
    sem_taxas = r["iva"] - (2.85 * 0.06 + (0.07 + 0.5 + 500 * 0.0020666) * 0.23)
    assert sem_taxas == aprox(100 * 0.23)


def test_familia_numerosa_tem_mais_kwh_com_iva_reduzido():
    normal = impostos.com_impostos(60, 0, 300, 30, 6.9)
    familia = impostos.com_impostos(60, 0, 300, 30, 6.9, familia_numerosa=True)
    assert familia["iva"] < normal["iva"]
