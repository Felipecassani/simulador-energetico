"""Explorar possibilidades: o que custaria mudar de contrato, de potência ou de hábitos.

Tudo em € por mês (30 dias), sem IVA nem taxas, para o mesmo consumo da pessoa.
Cada cenário diz quanto custa e que esforço pede: só mudar de contrato, mudar a potência ou
mudar hábitos. Usa as ofertas da ERSE (preço fixo), a tarifa regulada e, se houver mercado,
as fórmulas dos indexados.
"""
from dataclasses import dataclass
from datetime import date

from nucleo import indexados, ofertas as of, periodos, tarifas

ESCALOES = tarifas.ESCALOES_KVA
CONTRATO, POTENCIA, HABITOS, TUDO = ("Só mudar de contrato", "Mudar a potência", "Mudar hábitos",
                                     "Juntar tudo")


@dataclass(frozen=True)
class Cenario:
    nome: str
    detalhe: str
    mensal: float
    esforco: str


def opcoes_validas(pct_vazio, pct_ponta):
    """Que opções horárias se podem comparar com o que se sabe do perfil."""
    if pct_vazio is None:
        return ("simples",)
    if pct_ponta is None:
        return ("simples", "bi")                  # fatura bi-horária: ponta desconhecida
    return ("simples", "bi", "tri")


def melhor(lista_ofertas, kwh_mes, kva, pct_vazio, pct_ponta, erse, opcoes=None, hoje=None):
    """(custo mensal, descrição) do contrato mais barato: ofertas da ERSE ou tarifa regulada."""
    validas = [o for o in opcoes_validas(pct_vazio, pct_ponta) if opcoes is None or o in opcoes]
    candidatos = []
    lista = [o for o in lista_ofertas if o.opcao in validas]
    for o, custo in of.mais_baratas(lista, kwh_mes, 30, kva, pct_vazio, pct_ponta, n=1, hoje=hoje):
        candidatos.append((custo, f"{o.comercializador} · {o.nome} ({periodos.NOMES[o.opcao].lower()})"))
    for linha in tarifas.comparar_opcoes(kwh_mes, pct_vazio or 0.0, pct_ponta or 0.0, 30, kva, erse):
        if linha["modalidade"] == "fixo" and linha["opcao"] in validas:
            candidatos.append((linha["total"], f"Tarifa regulada ({periodos.NOMES[linha['opcao']].lower()})"))
    return min(candidatos) if candidatos else None


def _abaixo(kva):
    menores = [e for e in ESCALOES if e < kva - 1e-9]
    return menores[-1] if menores else None


def explorar(kwh_mes, kva, pct_vazio, pct_ponta, erse, lista_ofertas, medias_omie=None, hoje=None,
             pico_kw=None):
    """Lista de cenários, do mais barato para o mais caro.

    pico_kw: o maior pico medido (E-REDES, média de 15 min). Se já passa de 90 % da potência abaixo,
    descer de escalão faria disparar o quadro: esse cenário não aparece.
    """
    hoje = hoje or date.today()
    validas = opcoes_validas(pct_vazio, pct_ponta)
    cenarios = []

    regulada = [l for l in tarifas.comparar_opcoes(kwh_mes, pct_vazio or 0.0, pct_ponta or 0.0, 30, kva, erse)
                if l["modalidade"] == "fixo" and l["opcao"] in validas]
    if regulada:
        r = min(regulada, key=lambda l: l["total"])
        cenarios.append(Cenario("Tarifa regulada", f"ERSE, preço fixo, {periodos.NOMES[r['opcao']].lower()}",
                                r["total"], CONTRATO))

    for opcao in validas:
        m = melhor([o for o in lista_ofertas if o.com != "TUR"], kwh_mes, kva, pct_vazio, pct_ponta, erse,
                   opcoes=(opcao,), hoje=hoje)
        if m and not m[1].startswith("Tarifa regulada"):
            cenarios.append(Cenario(f"Melhor oferta em {periodos.NOMES[opcao].lower()}", m[1], m[0], CONTRATO))

    if medias_omie is not None:
        tar = erse["tar"]["energia_eur_kwh"]["simples"]["simples"]
        pot = of.potencia_indexadas(lista_ofertas, kva, [(f.comercializador, f.procurar) for f in indexados.FORMULAS])
        pot[None] = tarifas.preco_potencia(erse, kva)
        f, preco, custo = indexados.estimar(medias_omie["simples"]["simples"], hoje.month, tar, kwh_mes, 30, pot)[0]
        cenarios.append(Cenario("Indexado ao mercado", f"{f.comercializador} · {f.oferta} (estimativa com o "
                                "mercado recente; muda todos os dias)", custo, CONTRATO))

    menor = _abaixo(kva)
    if menor and pico_kw is not None and pico_kw > 0.9 * menor:
        menor = None                              # o pico medido não cabe na potência abaixo
    if menor:
        m = melhor(lista_ofertas, kwh_mes, menor, pct_vazio, pct_ponta, erse, hoje=hoje)
        if m:
            cenarios.append(Cenario(f"Descer para {menor:g} kVA".replace(".", ","),
                                    f"{m[1]} · só se o quadro não disparar", m[0], POTENCIA))

    if pct_vazio is not None:
        vazio = min(100.0 - (pct_ponta or 0.0), pct_vazio + 10)
        m = melhor(lista_ofertas, kwh_mes, kva, vazio, pct_ponta, erse, hoje=hoje)
        if m:
            cenarios.append(Cenario("Pôr mais 10 % do consumo no vazio",
                                    f"{m[1]} · máquinas e água quente à noite", m[0], HABITOS))

    m = melhor(lista_ofertas, kwh_mes * 0.9, kva, pct_vazio, pct_ponta, erse, hoje=hoje)
    if m:
        cenarios.append(Cenario("Gastar 10 % menos", f"{m[1]} · dicas da ferramenta Eficiência", m[0], HABITOS))

    vazio = min(100.0 - (pct_ponta or 0.0), pct_vazio + 10) if pct_vazio is not None else None
    m = melhor(lista_ofertas, kwh_mes * 0.9, menor or kva, vazio, pct_ponta, erse, hoje=hoje)
    if m:
        partes = ["10 % menos"] + (["mais vazio"] if vazio is not None else []) + \
                 ([f"{menor:g} kVA".replace(".", ",")] if menor else [])
        cenarios.append(Cenario("Juntar tudo", f"{m[1]} · {', '.join(partes)}", m[0], TUDO))

    return sorted(cenarios, key=lambda c: c.mensal)
