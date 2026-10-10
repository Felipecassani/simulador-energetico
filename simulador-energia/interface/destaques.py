"""Números de destaque no cabeçalho de cada ferramenta (o «porque vale a pena» logo à entrada).

Regra: só números verdadeiros, calculados aqui com os dados oficiais (ERSE, OMIE) ou com os
números da própria pessoa — nada escrito à mão. Se um cálculo falhar (sem rede, sem ofertas),
esse destaque simplesmente não aparece.
"""
from interface import perfil as pf
from interface.dados import erse, ofertas_erse, omie_hoje_e_amanha


def _numero(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", " ").replace(".", ",")


def _mercado():
    from nucleo import ofertas
    lista, _ = ofertas_erse()
    return ofertas.resumo_mercado(lista) if lista else None


def _fatura():
    m = _mercado()
    return [(str(m["ofertas"]), "ofertas comparadas"),
            (f"até {_numero(m['diferenca_ano'])} €", "de diferença por ano")] if m else []


def _comparar():
    m = _mercado()
    return [(str(m["ofertas"]), "ofertas oficiais"), (str(m["empresas"]), "empresas"),
            (f"até {_numero(m['diferenca_ano'])} €", "por ano entre a mais cara e a mais barata")] if m else []


def _poupar():
    from nucleo import eficiencia
    p = pf.perfil()
    poupanca_ano = p["consumo_kwh"] * 30 / p["dias"] * 0.10 * p["preco_energia"] * 365 / 30
    return [(str(len(eficiencia.DICAS)), "dicas para a tua casa"),
            (f"≈ {_numero(poupanca_ano)} €", "por ano, se gastares 10 % menos")]


def _bi_horario():
    from nucleo import periodos
    bi = erse()["regulada"]["energia_eur_kwh"]["bi"]
    mais_barato = (1 - bi["vazio"] / bi["fora_vazio"]) * 100
    return [(f"{_numero(mais_barato)} %", "mais barato no vazio (tarifa regulada)"),
            (periodos.texto_vazio_curto(), "as horas de vazio")]


def _preco_hora():
    from nucleo import mercado
    hoje, _ = omie_hoje_e_amanha()
    r = mercado.resumo_omie(hoje)
    return [(f"{_numero((r['max'] - r['min']) / 10, 1)} cêntimos", "entre a hora mais cara e a mais barata, hoje"),
            ("96", "preços por dia, de 15 em 15 minutos")]


CALCULOS = {1: _fatura, 2: _poupar, 3: _comparar, 4: _preco_hora, 5: _bi_horario}


def da_ferramenta(numero):
    """[(valor, rótulo)] para o cabeçalho da ferramenta, ou [] se não houver dados."""
    try:
        return CALCULOS[numero]() if numero in CALCULOS else []
    except Exception:          # sem rede, sem ofertas, dados incompletos: o destaque não aparece
        return []
