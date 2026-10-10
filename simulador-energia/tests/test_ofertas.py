"""Ofertas da ERSE.

1) Um ZIP FICTÍCIO no formato real do ficheiro da ERSE (empresas inventadas).
   Conta à mão (300 kWh, 30 dias, 6,9 kVA, simples):
     Alfa  0,3000 €/dia × 30 + 300 × 0,1500 = 9,00 + 45,00 = 54,00 €
     Beta  0,4000 × 30 + 300 × 0,1300       = 12,00 + 39,00 = 51,00 €
     Gama  0,3500 × 30 + 300 × 0,1600       = 10,50 + 48,00 = 58,50 €
     Delta indexada · Zeta dual · Eta com restrições · Teta expirada · Epsilon 3,45 kVA → fora
2) O ficheiro verdadeiro (nucleo/dados), conferido com a tarifa regulada da ERSE 2026.
"""
import io
import zipfile
from datetime import date

import pytest

from nucleo import mercado, ofertas as of

aprox = pytest.approx
HOJE = date(2026, 10, 1)

PRECOS = """﻿COM;Pot_Cont;Escalao;ORD;COD_Proposta;Contagem;TF;TV|TVFV|TVP;TVV|TVC;TVVz;TFGN;TVGN
ALFA;6,9;;;A1;1;0,3000;0,1500;;;;
BETA;6,9;;;B1;1;0,4000;0,1300;;;;
BETA;6,9;;;B1;2;0,4000;0,1700;0,0900;;;
BETA;6,9;;;B1;3;0,4000;0,2500;0,1500;0,0900;;
GAMA;6,9;;;G1;1;0,3500;0,1600;;;;
DELTA;6,9;;;D1;1;0,2000;0,0500;;;;
ZETA;6,9;;;Z1;1;0,1000;0,0800;;;;
ETA;6,9;;;H1;1;0,1000;0,0800;;;;
TETA;6,9;;;T1;1;0,1000;0,0800;;;;
EPSILON;3,45;;;E1;1;0,1000;0,1000;;;;
GASSA;;E1;;GN1;;;;;;0,2;0,08
"""
COND = """﻿COM;COD_Proposta;NomeProposta;Segmento;Fornecimento;Data ini;Data fim;FiltroFidelização;FiltroRestrições;FiltroPrecosIndex_ELE;ReembTW_ELE (%);ConsIni_ELE;LinkFichaPadrao
ALFA;A1;Alfa Casa;Dom;ELE;01/01/2026;31/12/2026;N;N;N;0;;https://exemplo.invalid/alfa
BETA;B1;Beta Poupança;Tod;ELE;01/01/2026;31/12/2026;S;N;N;0,02;;https://exemplo.invalid/beta
GAMA;G1;Gama Luz;Dom;ELE;;;N;N;N;0;;
DELTA;D1;Delta Mercado;Dom;ELE;01/01/2026;31/12/2026;N;N;S;0;;
ZETA;Z1;Zeta Dual;Dom;DUAL;01/01/2026;31/12/2026;N;N;N;0;;
ETA;H1;Eta Sócios;Dom;ELE;01/01/2026;31/12/2026;N;S;N;0;;
TETA;T1;Teta Verão;Dom;ELE;01/06/2026;30/09/2026;N;N;N;0;;
EPSILON;E1;Epsilon Mini;Dom;ELE;01/01/2026;31/12/2026;N;N;N;0;;
"""


def _zip(codificacao="utf-8"):
    tampao = io.BytesIO()
    with zipfile.ZipFile(tampao, "w") as z:
        z.writestr("csv\\Precos_ELEGN.csv", PRECOS.encode(codificacao, errors="ignore"))
        z.writestr("csv\\CondComerciais.csv", COND.encode(codificacao, errors="ignore"))
    return tampao.getvalue()


def test_le_as_colunas_partilhadas_por_ciclo():
    ofertas = of.ler_zip(_zip())
    assert len(ofertas) == 12 - 2                       # sem a linha do gás
    beta = {o.opcao: o.energia for o in ofertas if o.comercializador == "Beta"}
    assert beta["bi"] == {"fora_vazio": 0.17, "vazio": 0.09}
    assert beta["tri"] == {"ponta": 0.25, "cheias": 0.15, "vazio": 0.09}
    b = next(o for o in ofertas if o.codigo == "B1")
    assert b.fidelizacao and b.reembolsos and b.nome == "Beta Poupança"


def test_top_3_so_com_ofertas_que_qualquer_casa_pode_contratar():
    top = of.mais_baratas(of.ler_zip(_zip()), 300, 30, 6.9, hoje=HOJE)
    assert [o.comercializador for o, _ in top] == ["Beta", "Alfa", "Gama"]
    assert [v for _, v in top] == aprox([51.00, 54.00, 58.50])


def test_com_perfil_usa_a_opcao_horaria_mais_barata_de_cada_oferta():
    # Beta bi com 50 % vazio: 12,00 + 150 × 0,09 + 150 × 0,17 = 12,00 + 39,00 = 51,00 €
    # Beta tri (50 % vazio, 0 % ponta): 12,00 + 150 × 0,09 + 150 × 0,15 = 48,00 €
    top = of.mais_baratas(of.ler_zip(_zip()), 300, 30, 6.9, pct_vazio=50, pct_ponta=0, hoje=HOJE)
    oferta, valor = top[0]
    assert oferta.comercializador == "Beta" and oferta.opcao == "tri" and valor == aprox(48.00)


def test_fatura_bi_horaria_deixa_as_ofertas_tri_de_fora():
    top = of.mais_baratas(of.ler_zip(_zip()), 300, 30, 6.9, pct_vazio=50, pct_ponta=None, hoje=HOJE)
    oferta, valor = top[0]
    assert oferta.opcao != "tri" and valor == aprox(51.00)


def test_aceita_windows_1252():
    assert len(of.ler_zip(_zip("cp1252"))) == 10


def test_zip_incompleto_da_erro_claro():
    tampao = io.BytesIO()
    with zipfile.ZipFile(tampao, "w") as z:
        z.writestr("csv\\Precos_ELEGN.csv", PRECOS)
    with pytest.raises(ValueError, match="condições"):
        of.ler_zip(tampao.getvalue())


# ---------- ficheiro verdadeiro ----------
REAL = of.ficheiro_local()
real = pytest.mark.skipif(REAL is None, reason="sem cópia local das ofertas da ERSE")


@real
def test_ficheiro_real_bate_com_a_tarifa_regulada_da_erse():
    erse = mercado.carregar_erse_local(2026)
    tur = {o.opcao: o for o in of.ler_zip(REAL.read_bytes()) if o.com == "TUR" and o.kva == 6.9}
    reg = erse["regulada"]["energia_eur_kwh"]
    assert tur["simples"].energia["simples"] == aprox(reg["simples"]["simples"])
    assert tur["bi"].energia == aprox(reg["bi"])
    assert tur["tri"].energia == aprox(reg["tri"])
    assert tur["simples"].potencia_dia == aprox(erse["regulada"]["potencia_eur_dia"]["6.9"])


@real
def test_ficheiro_real_da_um_top_3_valido():
    top = of.mais_baratas(of.ler_zip(REAL.read_bytes()), 300, 30, 6.9, hoje=HOJE)
    assert len(top) == 3
    assert [v for _, v in top] == sorted(v for _, v in top)
    assert all(of.elegivel(o, HOJE) and o.kva == 6.9 for o, _ in top)


def test_resumo_mercado_conta_e_mede_a_diferenca():
    lista = [of.Oferta("Alfa", "A1", "Alfa Casa", 6.9, "simples", 0.30, {"simples": 0.12}),
             of.Oferta("Alfa", "A2", "Alfa Mais", 6.9, "simples", 0.30, {"simples": 0.16}),
             of.Oferta("Beta", "B1", "Beta Luz", 6.9, "simples", 0.40, {"simples": 0.20})]
    r = of.resumo_mercado(lista, kwh_mes=300, kva=6.9)
    assert r["ofertas"] == 3 and r["empresas"] == 2
    # mais barata 0,30×30 + 300×0,12 = 45 €; mais cara 0,40×30 + 300×0,20 = 72 € → 27 €/mês
    assert r["diferenca_ano"] == pytest.approx(27 * 365 / 30)
    assert of.resumo_mercado(lista[:1]) is None
