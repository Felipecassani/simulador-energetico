"""Testes dos cálculos, passo a passo.

Executar:  python -m pytest   (ou o botão ▶ "Testes (pytest)" no PyCharm)
Cada resultado esperado foi feito à mão primeiro — se um teste falhar,
corrige-se o código, nunca o valor esperado.
"""
import pytest

from nucleo import calculos as c

BASE = dict(consumo_kwh=500, preco_energia=0.16, preco_diario=0.35, dias=30)
aprox = pytest.approx


# ---------- Passo 1 — fatura simplificada ----------

class TestPasso1Fatura:
    def test_A_caso_de_validacao_90_50(self):
        f = c.fatura_simplificada(**BASE)
        assert f["energia"] == aprox(80.00)
        assert f["potencia"] == aprox(10.50)
        assert f["total"] == aprox(90.50)

    def test_B_consumo_zero_so_potencia(self):
        f = c.fatura_simplificada(**{**BASE, "consumo_kwh": 0})
        assert f["energia"] == 0
        assert f["total"] == aprox(f["potencia"])

    def test_C_dobro_do_consumo_dobra_energia(self):
        f500 = c.fatura_simplificada(**BASE)
        f1000 = c.fatura_simplificada(**{**BASE, "consumo_kwh": 1000})
        assert f1000["energia"] == aprox(2 * f500["energia"])
        assert f1000["potencia"] == aprox(f500["potencia"])

    @pytest.mark.parametrize("campo", ["consumo_kwh", "preco_energia", "preco_diario", "dias"])
    def test_D_negativo_rejeitado(self, campo):
        with pytest.raises(ValueError):
            c.fatura_simplificada(**{**BASE, campo: -1})

    def test_E_31_dias_so_muda_potencia(self):
        f30 = c.fatura_simplificada(**BASE)
        f31 = c.fatura_simplificada(**{**BASE, "dias": 31})
        assert f31["energia"] == aprox(f30["energia"])
        assert f31["potencia"] - f30["potencia"] == aprox(0.35)
        assert f31["total"] == aprox(90.85)


# ---------- Passo 2 — medida de eficiência ----------

class TestPasso2Eficiencia:
    def test_6000_kwh_ano_com_reducao_15(self):
        assert c.consumo_depois(6000, 15) == aprox(5100)

    def test_cenario_mensal(self):
        r = c.cenario_eficiencia(500, 0.20, 0.35, 30, 15)
        assert r["consumo_depois"] == aprox(425)
        assert r["kwh_evitados"] == aprox(75)
        assert r["poupanca_mensal"] == aprox(15.00)
        assert r["poupanca_anual"] == aprox(180.00)

    def test_payback_simples_5_anos(self):
        r = c.cenario_eficiencia(500, 0.20, 0.35, 30, 15)
        assert c.payback_anos(900, r["poupanca_anual"]) == aprox(5)
        assert c.payback_anos(900, 0) is None           # sem poupança não há payback

    def test_fatura_de_60_dias_da_a_mesma_poupanca_mensal(self):
        # 1000 kWh em 60 dias = 500 kWh/mês: mesma poupança mensal que o caso de 30 dias
        r = c.cenario_eficiencia(1000, 0.20, 0.35, 60, 15)
        assert r["poupanca_periodo"] == aprox(30.00)
        assert r["poupanca_mensal"] == aprox(15.00)
        assert r["poupanca_anual"] == aprox(180.00)

    @pytest.mark.parametrize("reducao", [-1, 101])
    def test_reducao_fora_de_0_a_100(self, reducao):
        with pytest.raises(ValueError):
            c.consumo_depois(500, reducao)


# ---------- Passo 3 — comparar tarifários ----------

TARIFARIOS = [
    {"nome": "A", "preco_energia": 0.16, "preco_diario": 0.35},
    {"nome": "B", "preco_energia": 0.14, "preco_diario": 0.45},
    {"nome": "C", "preco_energia": 0.18, "preco_diario": 0.30},
]


class TestPasso3Tarifarios:
    def test_ordenado_do_mais_barato_ao_mais_caro(self):
        r = c.comparar_tarifarios(500, 30, TARIFARIOS)
        assert [t["nome"] for t in r] == ["B", "A", "C"]
        assert [t["total"] for t in r] == [aprox(83.5), aprox(90.5), aprox(99.0)]

    def test_mesmo_consumo_e_dias_para_todos(self):
        r = {t["nome"]: t for t in c.comparar_tarifarios(500, 30, TARIFARIOS)}
        assert r["A"]["energia"] == aprox(500 * 0.16)
        assert r["C"]["potencia"] == aprox(30 * 0.30)


# ---------- Passo 4 — tabela comparativa ----------

class TestPasso4Tabela:
    def test_colunas_e_diferencas(self):
        tabela = c.tabela_comparativa(c.comparar_tarifarios(500, 30, TARIFARIOS))
        assert list(tabela.columns) == ["Tarifário", "Energia (€)", "Potência (€)",
                                        "Total (€)", "Diferença (€)"]
        assert list(tabela["Diferença (€)"]) == [aprox(0), aprox(7.0), aprox(15.5)]


# ---------- Passo 5 — bi-horário ----------

class TestPasso5BiHorario:
    def test_caso_de_validacao(self):
        f = c.fatura_bi_horaria(200, 0.10, 300, 0.20, 0.35, 30)
        assert f["energia_vazio"] == aprox(20.0)
        assert f["energia_fora_vazio"] == aprox(60.0)
        assert f["total"] == aprox(90.5)

    def test_negativo_rejeitado(self):
        with pytest.raises(ValueError):
            c.fatura_bi_horaria(-1, 0.10, 300, 0.20, 0.35, 30)
