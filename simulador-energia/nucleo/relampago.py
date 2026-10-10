"""Calculadora relâmpago (Início): do total de uma fatura mensal, a poupança possível por ano.

1. Consumo estimado: o kWh que, com os preços da tarifa regulada (simples), a potência e todas
   as taxas e IVA, dá o total que a pessoa pagou (procura por bisseção: o total cresce com o kWh).
2. Para esse consumo, a oferta de preço fixo mais barata, também com taxas e IVA.
3. Poupança por ano = (o que pagou − o que pagaria) × 365/30.

É conservadora: quem paga mais caro do que a regulada fica com um consumo estimado maior do que
o real, e a oferta mais barata para esse consumo sai mais cara, por isso a poupança nunca é exagerada.
"""
from nucleo import impostos, ofertas, tarifas

DIAS = 30
ANO = 365 / DIAS


def _total_regulada(kwh, tarifa, kva):
    preco = tarifa["regulada"]["energia_eur_kwh"]["simples"]["simples"]
    potencia = tarifas.preco_potencia(tarifa, kva) * DIAS
    return impostos.com_impostos(kwh * preco, potencia, kwh, DIAS, kva)["total"]


def kwh_da_fatura(total_com_iva, tarifa, kva=6.9):
    """kWh por mês que, na tarifa regulada, dariam este total (com IVA). 0 se o total só paga a potência."""
    if total_com_iva <= _total_regulada(0, tarifa, kva):
        return 0.0
    baixo, alto = 0.0, 1.0
    while _total_regulada(alto, tarifa, kva) < total_com_iva and alto < 1e5:
        alto *= 2
    for _ in range(60):
        meio = (baixo + alto) / 2
        if _total_regulada(meio, tarifa, kva) < total_com_iva:
            baixo = meio
        else:
            alto = meio
    return (baixo + alto) / 2


def poupanca(total_com_iva, lista_ofertas, tarifa, kva=6.9, kwh_real=None):
    """{"kwh_mes", "oferta", "melhor_mes", "poupanca_ano", "exata"} ou None (sem ofertas ou total inválido).

    kwh_real: o consumo da fatura, se a pessoa o souber. Com ele a conta deixa de depender da
    estimativa pela tarifa regulada ("exata" = True); sem ele, a estimativa é conservadora.
    """
    if not total_com_iva or total_com_iva <= 0:
        return None
    exata = bool(kwh_real and kwh_real > 0)
    kwh = float(kwh_real) if exata else kwh_da_fatura(total_com_iva, tarifa, kva)
    melhor = ofertas.mais_baratas(lista_ofertas, kwh, DIAS, kva, n=1)
    if not melhor:
        return None
    oferta, custo = melhor[0]
    potencia = oferta.potencia_dia * DIAS
    melhor_mes = impostos.com_impostos(custo - potencia, potencia, kwh, DIAS, kva)["total"]
    return {"kwh_mes": kwh, "oferta": oferta, "melhor_mes": melhor_mes, "exata": exata,
            "poupanca_ano": max(0.0, (total_com_iva - melhor_mes) * ANO)}
