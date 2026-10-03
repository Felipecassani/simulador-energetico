"""Até um ano de faturas: juntar, ordenar e encontrar padrões (sazonalidade, preço, lacunas).

Entra o que o leitor de faturas devolve (leitura_fatura.ler_fatura): inicio, fim, dias,
consumo_total, preco_energia, preco_diario, consumos, comercializador, modalidade.
Valores sem IVA; o custo de cada período é energia + potência (como no resto do site).
"""
from dataclasses import dataclass
from datetime import date, timedelta

MAX_FATURAS = 12
INVERNO = (11, 12, 1, 2, 3)
VERAO = (6, 7, 8, 9)


@dataclass(frozen=True)
class Periodo:
    inicio: object                  # date ou None
    fim: object
    dias: int
    kwh: float
    preco_kwh: object = None        # €/kWh (média do período)
    preco_dia: object = None        # €/dia da potência
    empresa: str = ""
    modalidade: str = ""
    pct_vazio: object = None
    pct_ponta: object = None

    @property
    def kwh_dia(self):
        return self.kwh / self.dias

    @property
    def custo(self):
        """Energia + potência sem IVA, ou None se faltar um dos preços."""
        if self.preco_kwh is None or self.preco_dia is None:
            return None
        return self.kwh * self.preco_kwh + self.preco_dia * self.dias

    @property
    def meio(self):
        """Dia do meio do período (decide o mês a que pertence)."""
        return self.inicio + timedelta(days=self.dias // 2) if self.inicio else None


def periodo_de(lido):
    """Período de uma fatura lida, ou None se faltar o consumo ou os dias."""
    kwh, dias = lido.get("consumo_total"), lido.get("dias")
    if not kwh or not dias:
        return None
    consumos, precos = lido.get("consumos") or {}, lido.get("precos") or {}
    preco = lido.get("preco_energia")
    if preco is None and consumos and set(consumos) <= set(precos):
        preco = sum(consumos[p] * precos[p] for p in consumos) / kwh
    vazio = 100 * consumos["vazio"] / kwh if "vazio" in consumos else None
    ponta = 100 * consumos["ponta"] / kwh if "ponta" in consumos else None
    return Periodo(lido.get("inicio"), lido.get("fim"), int(dias), float(kwh), preco,
                   lido.get("preco_diario"), lido.get("comercializador") or "", lido.get("modalidade") or "",
                   vazio, ponta)


def juntar(lidas):
    """Períodos sem repetidos (mesmas datas, ou mesmo consumo e dias sem datas), por ordem de data.

    Ficam os MAX_FATURAS mais recentes (um ano).
    """
    vistos, saida = set(), []
    for lido in lidas:
        p = periodo_de(lido)
        if p is None:
            continue
        chave = (p.inicio, p.fim) if p.inicio else (round(p.kwh, 1), p.dias)
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(p)
    saida.sort(key=lambda p: (p.inicio is None, p.inicio or date.min))
    return saida[-MAX_FATURAS:]


def _media(valores):
    valores = [v for v in valores if v is not None]
    return sum(valores) / len(valores) if valores else None


def resumo(periodos):
    """Números do ano e observações (texto simples, para o site)."""
    if not periodos:
        return None
    dias = sum(p.dias for p in periodos)
    kwh = sum(p.kwh for p in periodos)
    kwh_dia = kwh / dias
    com_custo = [p for p in periodos if p.custo is not None]
    custo_dia = (sum(p.custo for p in com_custo) / sum(p.dias for p in com_custo)) if com_custo else None

    # repartição vazio/ponta pesada pelo consumo, sempre sobre as MESMAS faturas: com faturas tri usa só
    # essas (vazio e ponta); senão as bi (vazio, ponta desconhecida). Assim vazio + ponta nunca passa de 100 %.
    tri = [p for p in periodos if p.pct_vazio is not None and p.pct_ponta is not None]
    bi = [p for p in periodos if p.pct_vazio is not None]
    base = tri or bi
    peso = sum(p.kwh for p in base)
    pct_vazio = sum(p.pct_vazio * p.kwh for p in base) / peso if base else None
    pct_ponta = sum(p.pct_ponta * p.kwh for p in tri) / peso if tri else None

    inverno = _media([p.kwh_dia for p in periodos if p.meio and p.meio.month in INVERNO])
    verao = _media([p.kwh_dia for p in periodos if p.meio and p.meio.month in VERAO])
    maior = max(periodos, key=lambda p: p.kwh_dia)
    menor = min(periodos, key=lambda p: p.kwh_dia)

    datados = [p for p in periodos if p.inicio and p.fim]
    lacunas = []
    for a, b in zip(datados, datados[1:]):
        falta = (b.inicio - a.fim).days - 1
        if falta > 3:
            lacunas.append((a.fim + timedelta(days=1), b.inicio - timedelta(days=1), falta))

    precos = [p for p in periodos if p.preco_kwh is not None]
    variacao_preco = ((precos[-1].preco_kwh / precos[0].preco_kwh - 1) * 100
                      if len(precos) >= 2 and precos[0].preco_kwh else None)
    fora_do_normal = [p for p in periodos if p.kwh_dia > 1.35 * kwh_dia]
    empresas = sorted({p.empresa for p in periodos if p.empresa})

    return {
        "faturas": len(periodos), "dias": dias, "kwh": kwh, "kwh_dia": kwh_dia,
        "kwh_ano": kwh_dia * 365, "kwh_mes": kwh_dia * 30,
        "custo_ano": custo_dia * 365 if custo_dia is not None else None,
        "custo_mes": custo_dia * 30 if custo_dia is not None else None,
        "inicio": datados[0].inicio if datados else None, "fim": datados[-1].fim if datados else None,
        "pct_vazio": pct_vazio, "pct_ponta": pct_ponta,
        "inverno_kwh_dia": inverno, "verao_kwh_dia": verao,
        "variacao_sazonal": ((inverno / verao - 1) * 100) if inverno and verao else None,
        "maior": maior, "menor": menor, "lacunas": lacunas,
        "variacao_preco": variacao_preco, "fora_do_normal": fora_do_normal, "empresas": empresas,
    }
