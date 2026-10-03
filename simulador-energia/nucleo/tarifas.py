"""Comparar opções horárias (simples, bi, tri) em tarifa fixa e indexada.

- Fixo: preços da tarifa regulada da ERSE (ou os do teu contrato).
- Indexado: preço de cada período = média OMIE nesse período × (1 + perdas)
  + margem do comercializador + TAR desse período. As perdas e a margem
  vêm do contrato de cada pessoa: a ERSE não publica um valor único.
- A potência é a mesma nas duas modalidades (preço da tarifa regulada), para a
  comparação mostrar só o efeito do preço da energia.
"""
from nucleo import calculos, periodos

OPCOES = ("simples", "bi", "tri")
ESCALOES_KVA = [1.15, 2.3, 3.45, 4.6, 5.75, 6.9, 10.35, 13.8, 17.25, 20.7]   # potências contratáveis em BTN
MODALIDADES = ("fixo", "indexado")


def distribuir_consumo(total_kwh, pct_vazio, pct_ponta):
    """Reparte o consumo pelos períodos de cada opção, com percentagens do utilizador.

    Nunca assume 50/50: a pessoa indica quanto gasta em vazio (e em ponta, para o
    tri-horário); o resto vai para fora de vazio / cheias.
    """
    calculos.exigir_nao_negativos(total_kwh=total_kwh)
    calculos.exigir_percentagem(pct_vazio=pct_vazio, pct_ponta=pct_ponta)
    if pct_vazio + pct_ponta > 100:
        raise ValueError("Vazio + ponta não podem passar de 100 %.")
    vazio = total_kwh * pct_vazio / 100
    ponta = total_kwh * pct_ponta / 100
    # max(0, …): com vazio + ponta = 100 % o arredondamento podia dar -0,0000000001
    return {
        "simples": {"simples": total_kwh},
        "bi": {"vazio": vazio, "fora_vazio": max(0.0, total_kwh - vazio)},
        "tri": {"vazio": vazio, "ponta": ponta, "cheias": max(0.0, total_kwh - vazio - ponta)},
    }


def preco_potencia(erse, kva):
    """Preço diário da potência regulada (€/dia) para um escalão de kVA."""
    tabela = erse["regulada"]["potencia_eur_dia"]
    chave = str(float(kva))
    if chave not in tabela:
        raise ValueError(f"Potência {kva} kVA não está na tabela da ERSE.")
    return tabela[chave]


def precos_fixos(erse, kva):
    """Preços de energia da tarifa regulada para cada opção (€/kWh)."""
    precos = {o: dict(p) for o, p in erse["regulada"]["energia_eur_kwh"].items()}
    if float(kva) <= 2.3:
        precos["simples"]["simples"] = erse["regulada"]["energia_simples_ate_2_3_kva"]
    return precos


def medias_omie_por_periodo(precos_omie):
    """Média do preço OMIE (€/MWh) em cada período de cada opção horária."""
    medias = {}
    for opcao in OPCOES:
        somas, contagens = {}, {}
        for instante, valor in precos_omie:
            p = periodos.periodo(instante, opcao)
            somas[p] = somas.get(p, 0) + valor
            contagens[p] = contagens.get(p, 0) + 1
        medias[opcao] = {p: somas[p] / contagens[p] for p in somas}
    return medias


def precos_indexados(medias_omie, erse, perdas_pct, margem_eur_kwh):
    """€/kWh por período: OMIE/1000 × (1 + perdas) + margem + TAR."""
    calculos.exigir_nao_negativos(perdas_pct=perdas_pct, margem_eur_kwh=margem_eur_kwh)
    tar = erse["tar"]["energia_eur_kwh"]
    return {
        opcao: {p: medias_omie[opcao][p] / 1000 * (1 + perdas_pct / 100) + margem_eur_kwh
                + tar[opcao][p] for p in tar[opcao]}
        for opcao in OPCOES
    }


def comparar_opcoes(total_kwh, pct_vazio, pct_ponta, dias, kva, erse,
                    medias_omie=None, perdas_pct=0.0, margem_eur_kwh=0.0):
    """Custo de cada opção horária, em fixo e (se houver dados OMIE) em indexado.

    Devolve uma lista ordenada do total mais baixo para o mais alto, com
    "opcao", "modalidade", "energia", "potencia", "total", "por_periodo" e
    "poupanca_vs_simples_fixo" (positivo = mais barato que simples fixo).
    """
    consumos = distribuir_consumo(total_kwh, pct_vazio, pct_ponta)
    potencia_dia = preco_potencia(erse, kva)
    tabelas = {"fixo": precos_fixos(erse, kva)}
    if medias_omie is not None:
        tabelas["indexado"] = precos_indexados(medias_omie, erse, perdas_pct, margem_eur_kwh)
    linhas = []
    for modalidade, precos in tabelas.items():
        for opcao in OPCOES:
            f = calculos.fatura_por_periodos(consumos[opcao], precos[opcao], potencia_dia, dias)
            linhas.append({"opcao": opcao, "modalidade": modalidade, **f,
                           "precos": precos[opcao]})
    referencia = next(l["total"] for l in linhas
                      if l["opcao"] == "simples" and l["modalidade"] == "fixo")
    for l in linhas:
        l["poupanca_vs_simples_fixo"] = referencia - l["total"]
    return sorted(linhas, key=lambda l: l["total"])
