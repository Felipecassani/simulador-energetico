"""Leitura de faturas: texto e um PDF de exemplo gerado no próprio teste."""
import io
from datetime import date

import pytest

from nucleo import leitura_fatura as lf

aprox = pytest.approx

SIMPLES = """FATURA DE ELETRICIDADE
Período de faturação: 01/08/2026 a 31/08/2026
Potência contratada: 6,90 kVA - Tarifa Simples
Termo de potência 31 dias x 0,3659 €/dia 11,34 €
Energia Simples 312 kWh x 0,1654 €/kWh 51,60 €"""

BI = """Periodo 15.07.2026 - 14.08.2026
Opção horária: Bi-horário
Potência Contratada 3,45 kVA
Potência 31 dias 0,1917 EUR/dia
Energia Vazio 1.120 kWh 0,1087 EUR/kWh
Energia Fora de Vazio 880 kWh 0,1988 EUR/kWh"""


# Estrutura de uma fatura real dupla (eletricidade + gás), com números fictícios e sem
# dados pessoais: consumo repartido por taxas de IVA, potência em duas linhas, linhas
# informativas "(… €/Dia * … Dia)" e leituras do contador sem "kWh".
DUPLA = """Período de Faturação 01/09/2026 a 30/09/2026
Termo Fixo 01/09/2026 30/09/2026 30 Dia 0,1220 3,66 23
Acesso às redes 01/09/2026 30/09/2026 30 Dia 0,0133 0,40 6
Consumo Gás Natural Escalão 1 BP < (0 - 220 m3/ano) medido 01/09/2026 30/09/2026 150 kWh 0,0928 13,92 23
9,00€ (0,0441 €/kWh * 150 kWh)Acessos de Energia Escalão 1 BP < (0 - 220 m3/ano) (Desde 01/09/2026 a 30/09/2026)
Imposto Especial de Consumo GN medido 01/09/2026 30/09/2026 150 kWh 0,0152532 2,29 23
Potência:
3,45 kVA/Simples
000009 Vazio 01/09/2026 4393 Inicial 30/09/2026 4468 Real 75
000009 Ponta 01/09/2026 4563 Inicial 30/09/2026 4601 Real 38
000009 Cheia 01/09/2026 8285 Inicial 30/09/2026 8385 Real 100
Acesso às Redes Potência Contratada 3,45 kVA 01/09/2026 30/09/2026 30 Dia 0,2000 6,00 23
Potência Contratada 3,45 kVA 01/09/2026 30/09/2026 30 Dia 0,2600 7,80 23
Consumo Eletricidade Vazio medido 01/09/2026 30/09/2026 60 kWh 0,1400 8,40 6
Consumo Eletricidade Ponta medido 01/09/2026 30/09/2026 30 kWh 0,1400 4,20 6
Consumo Eletricidade Cheia medido 01/09/2026 30/09/2026 80 kWh 0,1400 11,20 6
Consumo Eletricidade Vazio medido 01/09/2026 30/09/2026 15 kWh 0,1400 2,10 23
Consumo Eletricidade Ponta medido 01/09/2026 30/09/2026 8 kWh 0,1400 1,12 23
Consumo Eletricidade Cheia medido 01/09/2026 30/09/2026 20 kWh 0,1400 2,80 23
7,00€ (0,2291 €/Dia * 30 Dia)Acessos às Redes Potência Contratada 3,45 kVA (Desde 01/09/2026 a 30/09/2026)
4,55€ (0,0607 €/kWh * 75 kWh)Acessos de Energia Vazio (Desde 01/09/2026 a 30/09/2026)
Imposto Especial de Consumo Electricidade medido 01/09/2026 30/09/2026 213 kWh 0,001 0,21 23
01/09/2026 a 30/09/2026 tem por referência o valor base de 0.2943 €/dia (Potência Contratada)
Gasto médio diário de eletricidade referente ao período de faturação: 7.10 kWh"""


def test_fatura_dupla_eletricidade_e_gas():
    r = lf.ler_fatura(DUPLA)
    # 60+15 · 30+8 · 80+20 (linhas repartidas por IVA somadas; gás e contador ignorados)
    assert r["consumos"] == {"vazio": 75, "ponta": 38, "cheias": 100}
    assert r["consumo_total"] == aprox(213)
    assert r["preco_energia"] == aprox(0.14)
    assert r["preco_diario"] == aprox(0.20 + 0.26)      # as duas linhas de potência
    assert r["dias"] == 30 and r["potencia_kva"] == aprox(3.45)
    assert r["opcao"] == "simples"                     # escrito "kVA/Simples" na fatura


def test_contador_com_periodos_e_preco_unico_e_simples():
    texto = ("Consumo Eletricidade Vazio 40 kWh 0,1500 6,00\n"
             "Consumo Eletricidade Ponta 20 kWh 0,1500 3,00\n"
             "Consumo Eletricidade Cheia 40 kWh 0,1500 6,00")
    r = lf.ler_fatura(texto)
    assert r["opcao"] == "simples" and r["preco_energia"] == aprox(0.15)


def test_numeros_nao_se_juntam_a_datas():
    r = lf.ler_fatura("Consumo Eletricidade Vazio medido 28/08/2026 27/09/2026 72 kWh 0,1386")
    assert r["consumos"]["vazio"] == aprox(72)          # e não 26 072


def test_fatura_simples():
    r = lf.ler_fatura(SIMPLES)
    assert r["dias"] == 31
    assert r["potencia_kva"] == aprox(6.9)
    assert r["preco_diario"] == aprox(0.3659)
    assert r["consumo_total"] == aprox(312)
    assert r["preco_energia"] == aprox(0.1654)
    assert r["opcao"] == "simples"


def test_fatura_bi_horaria():
    r = lf.ler_fatura(BI)
    assert r["opcao"] == "bi"
    assert r["consumos"] == {"vazio": 1120, "fora_vazio": 880}
    assert r["precos"] == {"vazio": aprox(0.1087), "fora_vazio": aprox(0.1988)}
    assert r["consumo_total"] == aprox(2000)
    assert r["dias"] == 31


def test_so_devolve_o_que_encontra():
    r = lf.ler_fatura("Olá, isto não é uma fatura.")
    assert r["consumos"] == {} and "dias" not in r and "preco_energia" not in r


@pytest.mark.parametrize("texto,valor", [("1.234,56", 1234.56), ("0,1654", 0.1654),
                                         ("1.120", 1120), ("312", 312), ("6.9", 6.9)])
def test_numeros_portugueses(texto, valor):
    assert lf.numero(texto) == aprox(valor)


def test_pdf_de_exemplo():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    memoria = io.BytesIO()
    c = canvas.Canvas(memoria, pagesize=A4)
    for i, linha in enumerate(SIMPLES.splitlines()):
        c.drawString(60, 780 - 20 * i, linha.replace("€", "EUR"))
    c.save()
    r = lf.ler_ficheiro("fatura.pdf", memoria.getvalue())
    assert r["consumo_total"] == aprox(312) and r["dias"] == 31
    assert r["preco_energia"] == aprox(0.1654) and r["preco_diario"] == aprox(0.3659)


def test_pdf_sem_texto():
    from reportlab.pdfgen import canvas

    memoria = io.BytesIO()
    canvas.Canvas(memoria).save()
    with pytest.raises(ValueError):
        lf.ler_ficheiro("vazio.pdf", memoria.getvalue())


# ---------- casos-limite encontrados na revisão independente ----------

@pytest.mark.parametrize("texto,campo,esperado", [
    # a mesma parcela partida por datas: média pesada pelos dias, não a soma
    ("Período de faturação 15/12/2025 a 14/01/2026\n"
     "Potência Contratada 6,9 kVA 15/12/2025 31/12/2025 17 Dia 0,3600 6,12 23\n"
     "Potência Contratada 6,9 kVA 01/01/2026 14/01/2026 14 Dia 0,3659 5,12 23",
     "preco_diario", (17 * 0.36 + 14 * 0.3659) / 31),
    # linha informativa sem quantidade de dias não entra na potência
    ("Período 01/08/2026 a 31/08/2026\nPotência contratada: 6,90 kVA (0,3659 €/dia)\n"
     "Termo de potência 31 dias x 0,3659 €/dia 11,34 €", "preco_diario", 0.3659),
    # resumo + detalhe: o consumo não duplica
    ("Consumo Vazio 120 kWh\nConsumo Fora de Vazio 180 kWh\n"
     "Energia Vazio 120 kWh x 0,1087 €/kWh 13,04\nEnergia Fora de Vazio 180 kWh x 0,1988 €/kWh 35,78",
     "consumo_total", 300),
    # a TAR à parte não substitui o preço da energia
    ("Energia Simples 300 kWh 0,1654 €/kWh 49,62\nAcesso às redes energia 300 kWh 0,0607 €/kWh 18,21",
     "preco_energia", 0.1654),
    ("Consumo Eletricidade Simples 1 120 kWh 0,1654 €/kWh", "consumo_total", 1120),   # espaço de milhares
    ("Energia Simples 300 kWh 0.165 €/kWh", "preco_energia", 0.165),                   # OCR com ponto
])
def test_casos_limite(texto, campo, esperado):
    assert lf.ler_fatura(texto)[campo] == aprox(esperado)


def test_fora_do_vazio_nao_conta_como_vazio():
    r = lf.ler_fatura("Energia Fora do Vazio 180 kWh 0,1988 €/kWh\nEnergia Vazio 120 kWh 0,1087 €/kWh")
    assert r["consumos"] == {"fora_vazio": 180, "vazio": 120} and r["opcao"] == "bi"


def test_datas_trocadas_sao_ignoradas():
    assert "dias" not in lf.ler_fatura("Período 31/08/2026 a 01/08/2026")


def test_campanha_e_precos_base_so_da_eletricidade():
    texto = ("O desconto aplicado ao preço final de gás no período de:\n"
             "01/09/2026 a 30/09/2026 tem por referência o valor base de 0.1092 €/kWh\n"
             "Consumo Eletricidade Simples medido 100 kWh 0,1386 13,86 6\n"
             "Campanha Regresso (Desconto 15% já incluído)\n"
             "O desconto aplicado ao preço final de eletricidade no período de:\n"
             "01/09/2026 a 30/09/2026 tem por referência o valor base de 0.2943 €/dia (Potência Contratada)\n"
             "01/09/2026 a 30/09/2026 tem por referência o valor base de 0.1631 €/kWh em Vazio")
    r = lf.ler_fatura(texto)
    assert r["desconto_pct"] == aprox(15) and r["campanha"] is True
    assert r["precos_base"] == {"energia": aprox(0.1631), "potencia_dia": aprox(0.2943)}


def test_comercializador_e_o_nome_que_mais_aparece():
    texto = ("GOLDENERGY - Comercializadora de Energia\n" + SIMPLES +
             "\nAvarias: E-REDES 800 506 506\nwww.goldenergy.pt · Gold Energy\n"
             "Antigo contrato EDP terminado")
    assert lf.ler_fatura(texto)["comercializador"] == "Goldenergy"


def test_edp_distribuicao_nao_e_o_comercializador():
    assert lf.comercializador("EDP Distribuição - avarias") is None
    assert "comercializador" not in lf.ler_fatura(SIMPLES)


def test_comercializador_empate_e_variantes():
    assert lf.comercializador("Galp\nLuzboa") == "Galp"                 # empate: a primeira
    assert lf.comercializador("EDP - Distribuição avarias") is None
    assert lf.comercializador("EDP Serviço Universal") is None
    assert lf.comercializador("Viva em plenitude\nGalp") == "Galp"



DUAL_DATAS_DIFERENTES = """FATURA
Gás Natural
Termo Fixo 07/05/2026 14/06/2026 39 Dia 0,1237 4,82 23
Contador gás 07/05/2026 3348 Inicial 14/06/2026 3368 Real 20 11,2430028 225
Eletricidade
Vazio 11/05/2026 4083 Inicial 14/06/2026 4159 Real 76
Acesso às Redes Potência Contratada 4,6 kVA 11/05/2026 14/06/2026 35 Dia 0,2291 8,02 23
Potência Contratada 4,6 kVA 11/05/2026 14/06/2026 35 Dia 0,3148 11,02 23
Consumo Eletricidade Vazio medido 11/05/2026 14/06/2026 76 kWh 0,1397 10,62 6
Consumo Eletricidade Ponta medido 11/05/2026 14/06/2026 53 kWh 0,1397 7,40 6
Consumo Eletricidade Cheia medido 11/05/2026 14/06/2026 123 kWh 0,1397 17,18 6
"""


def test_fatura_dual_usa_o_periodo_da_eletricidade():
    """Erro encontrado com uma fatura real: o leitor ficava com as datas do gás (39 dias em vez de 35)."""
    r = lf.ler_fatura(DUAL_DATAS_DIFERENTES)
    assert (r["inicio"], r["fim"], r["dias"]) == (date(2026, 5, 11), date(2026, 6, 14), 35)
    assert r["preco_diario"] == aprox(0.2291 + 0.3148)
    assert r["consumo_total"] == aprox(252)


@pytest.mark.parametrize("texto,inicio,dias,diario", [
    # dual com o título "Energia elétrica" (não "eletricidade")
    ("Período de faturação 07/05/2026 a 14/06/2026\nGás natural\nTermo fixo 39 dias 0,1237\nEnergia elétrica\n"
     "Potência 6,9 kVA 11/05/2026 a 14/06/2026 35 dias 0,3000\nEnergia Simples 200 kWh 0,15 €/kWh",
     date(2026, 5, 11), 35, 0.30),
    # acerto de um mês anterior não alarga o período
    ("Potência 6,9 kVA 01/05/2026 a 31/05/2026 31 dias 0,3000\n"
     "Acerto potência 6,9 kVA 01/04/2026 a 30/04/2026 30 dias 0,3000\nEnergia Simples 200 kWh 0,15 €/kWh",
     date(2026, 5, 1), 31, None),
    # dual sem datas na potência: os dias da potência são os da eletricidade
    ("Período de faturação 07/05/2026 a 14/06/2026\nGás Natural\nTermo Fixo 39 Dia 0,1237\nEletricidade\n"
     "Potência 6,9 kVA 35 dias 0,3000\nEnergia Simples 200 kWh 0,15 €/kWh",
     date(2026, 5, 11), 35, 0.30),
])
def test_periodo_da_eletricidade_casos_da_auditoria(texto, inicio, dias, diario):
    r = lf.ler_fatura(texto)
    assert (r["inicio"], r["dias"]) == (inicio, dias)
    if diario is not None:
        assert r["preco_diario"] == aprox(diario)
