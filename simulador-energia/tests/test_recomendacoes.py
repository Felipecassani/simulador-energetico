"""Recomendações: conta à mão com uma fatura fictícia e preços ERSE 2026.

Fatura (30 dias, 6,9 kVA, simples): 300 kWh a 0,2000 €/kWh e 0,3659 €/dia
  atual = 60,00 + 10,977 = 70,977 €
  regulada simples = 300 × 0,1654 + 10,977 = 60,597 € → poupa 10,38 €/mês
"""
import pytest

from nucleo import mercado, recomendacoes as rc

aprox = pytest.approx
ERSE = mercado.carregar_erse_local(2026)
BASE = {"consumo_kwh": 300, "preco_energia": 0.20, "preco_diario": 0.3659, "dias": 30,
        "kva": 6.9, "opcao": "simples"}


def _ids(recs):
    return [r.id for r in recs]


def test_regulada_mais_barata_vem_primeiro():
    recs = rc.recomendar(BASE, ERSE)
    assert recs[0].id == "regulada"
    assert recs[0].poupanca_mensal == aprox(70.977 - 60.597)


def test_contrato_barato_nao_recomenda_mudar():
    recs = rc.recomendar({**BASE, "preco_energia": 0.12}, ERSE)
    regulada = next(r for r in recs if r.id == "regulada")
    assert regulada.poupanca_mensal is None and "abaixo" in regulada.titulo


def test_sem_perfil_pede_a_reparticao():
    assert "perfil" in _ids(rc.recomendar(BASE, ERSE))


def test_com_perfil_sugere_a_melhor_opcao():
    # 40 % vazio, 15 % ponta: tri regulado 58,06 € < simples 60,60 € → diferença 2,53 €
    recs = rc.recomendar({**BASE, "pct_vazio": 40, "pct_ponta": 15}, ERSE)
    opcao = next(r for r in recs if r.id == "opcao")
    assert "tri-horário" in opcao.titulo
    assert opcao.poupanca_mensal is None          # regulada vs regulada: é informação
    assert "2,53" in opcao.texto


def test_empate_com_a_regulada():
    # contrato a 0,1654 €/kWh e 0,3659 €/dia = exatamente a regulada simples
    recs = rc.recomendar({**BASE, "preco_energia": 0.1654}, ERSE)
    regulada = next(r for r in recs if r.id == "regulada")
    assert "igual" in regulada.titulo and regulada.poupanca_mensal is None


def test_fatura_real_com_campanha():
    """Os valores da fatura verdadeira (dupla, com campanha de 15 %), conferidos à mão.

    Contrato: 258 kWh × 0,1386 + 0,4449 €/dia × 31 = 49,55 € → 47,95 €/mês
    Regulada tri 4,6 kVA: 90×0,1087 + 46×0,2495 + 122×0,1690 + 0,2499×31 = 49,62 € → 48,02 €/mês
    Sem campanha: 258 × 0,1631 + 0,5234 × 31 = 58,31 € → 56,42 €/mês
    """
    fatura = {"consumo_kwh": 258, "preco_energia": 0.1386, "preco_diario": 0.4449, "dias": 31,
              "kva": 4.6, "opcao": "simples", "pct_vazio": 100 * 90 / 258,
              "pct_ponta": 100 * 46 / 258, "desconto_pct": 15,
              "precos_base": {"energia": 0.1631, "potencia_dia": 0.5234}}
    recs = {r.id: r for r in rc.recomendar(fatura, ERSE)}
    assert "igual" in recs["regulada"].titulo                     # 47,95 vs 48,02
    assert "47,95" in recs["regulada"].texto and "48,02" in recs["regulada"].texto
    assert "56,42" in recs["campanha"].texto and "8,47" in recs["campanha"].texto
    assert "8,40" in recs["campanha"].texto                        # 56,42 − 48,02
    assert "5,85" in recs["potencia_cara"].texto                  # (0,4449 − 0,2499) × 30
    assert "1,75" in recs["descer_potencia"].texto                # (0,2499 − 0,1917) × 30
    assert all(r.poupanca_mensal is None for r in recs.values())  # nada a poupar hoje


def test_campanha_mostra_o_preco_sem_desconto():
    recs = rc.recomendar({**BASE, "precos_base": {"energia": 0.25, "potencia_dia": 0.40},
                          "desconto_pct": 20}, ERSE)
    campanha = next(r for r in recs if r.id == "campanha")
    assert "20 %" in campanha.texto and "87,00" in campanha.texto   # 300×0,25 + 0,40×30


def test_indexado_usa_o_omie():
    barato = {o: {p: 10.0 for p in ps} for o, ps in
              {"simples": ["simples"], "bi": ["vazio", "fora_vazio"],
               "tri": ["vazio", "ponta", "cheias"]}.items()}
    recs = rc.recomendar(BASE, ERSE, medias_omie=barato)
    indexado = next(r for r in recs if r.id == "indexado")
    # 300 × (0,010 + 0,0607) + 10,977 = 32,187 € (limite mínimo: informativa, sem valor)
    assert "32,19" in indexado.texto and indexado.poupanca_mensal is None


def test_comercializador_aponta_para_o_simulador_da_erse():
    ultima = rc.recomendar(BASE, ERSE)[-1]
    assert ultima.ligacao == rc.SIMULADOR_ERSE


def test_sem_consumo_nao_ha_recomendacoes():
    assert rc.recomendar({**BASE, "consumo_kwh": 0}, ERSE) == []


def test_valores_mensais_com_periodos_diferentes_de_30_dias():
    # 60 dias com o dobro do consumo = o mesmo mês
    a = rc.recomendar(BASE, ERSE)[0].poupanca_mensal
    b = rc.recomendar({**BASE, "consumo_kwh": 600, "dias": 60}, ERSE)[0].poupanca_mensal
    assert a == aprox(b)


def _omie(valor):
    """Médias OMIE iguais em todos os períodos (€/MWh): só as TAR mudam entre opções."""
    return {o: {p: float(valor) for p in ps} for o, ps in
            {"simples": ["simples"], "bi": ["vazio", "fora_vazio"],
             "tri": ["vazio", "ponta", "cheias"]}.items()}


INDEXADO = {**BASE, "modalidade": "indexado", "perdas_pct": 10, "margem_kwh": 0.01}


def test_indexado_compara_o_preco_fixo_com_o_mercado_de_agora():
    # energia = 300 × (0,100 × 1,10 + 0,01 + 0,0607) = 54,21 €; + 0,3659 × 30 = 65,187 €
    # regulada simples = 60,597 € → o preço fixo poupa 4,59 €/mês
    recs = rc.recomendar(INDEXADO, ERSE, medias_omie=_omie(100))
    regulada = next(r for r in recs if r.id == "regulada")
    assert "preço fixo" in regulada.titulo
    assert regulada.poupanca_mensal == aprox(65.187 - 60.597)
    assert "70,98" in regulada.texto and "65,19" in regulada.texto
    assert "indexado" not in _ids(recs)            # já é indexado: não sugere mudar para indexado
    assert "horas_baratas" in _ids(recs)


def test_indexado_abaixo_do_preco_fixo():
    # 300 × (0,011 + 0,01 + 0,0607) + 10,977 = 35,487 € < 60,597 €
    recs = rc.recomendar(INDEXADO, ERSE, medias_omie=_omie(10))
    regulada = next(r for r in recs if r.id == "regulada")
    assert "abaixo do preço fixo" in regulada.titulo and regulada.poupanca_mensal is None


def test_indexado_sem_perdas_nem_margem_avisa_que_e_o_minimo():
    recs = rc.recomendar({**BASE, "modalidade": "indexado"}, ERSE, medias_omie=_omie(100))
    assert "valor mais baixo possível" in next(r for r in recs if r.id == "regulada").texto


def test_indexado_so_sem_perdas_tambem_avisa():
    recs = rc.recomendar({**BASE, "modalidade": "indexado", "margem_kwh": 0.01}, ERSE,
                         medias_omie=_omie(100))
    assert "não mostra as perdas do contrato" in next(r for r in recs if r.id == "regulada").texto


def test_indexado_sem_mercado_usa_a_fatura():
    recs = rc.recomendar({**BASE, "modalidade": "indexado"}, ERSE)
    assert recs[0].id == "regulada" and recs[0].poupanca_mensal == aprox(70.977 - 60.597)


def test_indexado_com_perfil_compara_as_opcoes_com_o_mercado():
    # OMIE igual em tudo: só as TAR contam. 40 % vazio, 15 % ponta, 45 % cheias
    # simples 0,0607; bi 0,4×0,0158 + 0,6×0,0835 = 0,05642; tri 0,06164
    # simples − bi = 0,00428 × 300 = 1,28 €/mês
    recs = rc.recomendar({**INDEXADO, "pct_vazio": 40, "pct_ponta": 15}, ERSE,
                         medias_omie=_omie(100))
    opcao = next(r for r in recs if r.id == "opcao")
    assert "indexado" in opcao.titulo and "bi-horário" in opcao.titulo
    assert "1,28" in opcao.texto and opcao.poupanca_mensal is None


def test_fatura_bi_horaria_nao_compara_com_o_tri():
    """Sem ponta na fatura, o tri não pode ganhar com 0 % em ponta (achado da verificação).

    Contrato aos preços da regulada bi: 120 × 0,1087 + 180 × 0,1988 + 10,977 = 59,805 €.
    """
    f = {**BASE, "opcao": "bi", "pct_vazio": 40, "pct_ponta": None,
         "preco_energia": (120 * 0.1087 + 180 * 0.1988) / 300}
    recs = rc.recomendar(f, ERSE)
    regulada = next(r for r in recs if r.id == "regulada")
    assert regulada.poupanca_mensal is None and "igual" in regulada.titulo
    assert "opcao" not in _ids(recs) and "% em ponta" not in regulada.texto


def test_indexado_para_contrato_fixo_e_informativo():
    recs = rc.recomendar(BASE, ERSE, medias_omie=_omie(10))
    indexado = next(r for r in recs if r.id == "indexado")
    assert indexado.poupanca_mensal is None and "poupança real será menor" in indexado.texto
