"""Cálculos do simulador — Python puro, sem Streamlit, para poder testar.

Regras (ver CLAUDE.md e nucleo/roteiro.py):
- os preços vêm do utilizador ou de fontes oficiais (ERSE, OMIE); nada inventado;
- entradas negativas são rejeitadas com ValueError;
- unidades: kWh, €/kWh, €/dia, dias, %.
"""
import pandas as pd


def exigir_nao_negativos(**valores):
    """Rejeita qualquer entrada negativa, dizendo qual foi."""
    for nome, valor in valores.items():
        if valor < 0:
            raise ValueError(f"'{nome}' não pode ser negativo (recebido: {valor}).")


def exigir_percentagem(**valores):
    """Rejeita percentagens fora de [0, 100]."""
    for nome, valor in valores.items():
        if not 0 <= valor <= 100:
            raise ValueError(f"'{nome}' tem de estar entre 0 e 100 % (recebido: {valor}).")


# =====================================================================
# PASSO 1 — Fatura simplificada
# =====================================================================

def fatura_simplificada(consumo_kwh, preco_energia, preco_diario, dias):
    """Fatura simplificada, em euros.

    Cenergia  = consumo [kWh] × preço da energia [€/kWh]
    Cpotência = preço diário da potência [€/dia] × dias
    Ctotal    = Cenergia + Cpotência

    Devolve {"energia": €, "potencia": €, "total": €}.
    Caso de validação: 500 kWh, 0,16 €/kWh, 0,35 €/dia, 30 dias → 90,50 €.
    """
    exigir_nao_negativos(consumo_kwh=consumo_kwh, preco_energia=preco_energia,
                         preco_diario=preco_diario, dias=dias)
    energia = consumo_kwh * preco_energia
    potencia = preco_diario * dias
    return {"energia": energia, "potencia": potencia, "total": energia + potencia}


def fatura_por_periodos(consumos, precos, preco_diario, dias):
    """Fatura com vários períodos horários (simples, bi ou tri-horário).

    consumos: {"vazio": kWh, "fora_vazio": kWh, …}; precos: {"vazio": €/kWh, …}.
    Devolve {"por_periodo": {período: €}, "energia", "potencia", "total"}.
    """
    exigir_nao_negativos(preco_diario=preco_diario, dias=dias, **{
        f"consumo_{p}": v for p, v in consumos.items()}, **{
        f"preco_{p}": v for p, v in precos.items()})
    faltam = set(consumos) - set(precos)
    if faltam:
        raise ValueError(f"Falta o preço de: {', '.join(sorted(faltam))}")
    por_periodo = {p: consumos[p] * precos[p] for p in consumos}
    energia = sum(por_periodo.values())
    potencia = preco_diario * dias
    return {"por_periodo": por_periodo, "energia": energia, "potencia": potencia,
            "total": energia + potencia}


# =====================================================================
# PASSO 2 — Medida de eficiência energética (antes / depois)
# =====================================================================

def consumo_depois(consumo_antes, reducao_pct):
    """Edepois = Eantes × (1 − redução/100).

    Uma redução fora de [0, 100] % (ou um consumo negativo) levanta ValueError.
    """
    exigir_nao_negativos(consumo_antes=consumo_antes)
    exigir_percentagem(reducao_pct=reducao_pct)
    return consumo_antes * (1 - reducao_pct / 100)


def cenario_eficiencia(consumo_kwh, preco_energia, preco_diario, dias, reducao_pct):
    """Compara o período antes e depois de uma medida de eficiência.

    O consumo e os custos são os do período (`dias`, por exemplo os de uma fatura).
    A poupança mensal é a do período levada a um mês de 30 dias, e a anual é a
    mensal × 12 (com dias = 30 fica igual à poupança do período).
    Devolve: consumo_antes, consumo_depois, kwh_evitados, custo_antes, custo_depois,
    poupanca_periodo, poupanca_mensal, poupanca_anual, reducao_pct.
    A potência não muda com a medida, por isso não entra na poupança.
    """
    depois = consumo_depois(consumo_kwh, reducao_pct)
    antes_f = fatura_simplificada(consumo_kwh, preco_energia, preco_diario, dias)
    depois_f = fatura_simplificada(depois, preco_energia, preco_diario, dias)
    poupanca = antes_f["total"] - depois_f["total"]
    mensal = poupanca * 30 / dias if dias else 0.0
    return {"consumo_antes": consumo_kwh, "consumo_depois": depois,
            "kwh_evitados": consumo_kwh - depois,
            "custo_antes": antes_f["total"], "custo_depois": depois_f["total"],
            "poupanca_periodo": poupanca, "poupanca_mensal": mensal,
            "poupanca_anual": mensal * 12, "reducao_pct": reducao_pct}


def payback_anos(custo_medida, poupanca_anual):
    """Payback simples = custo da medida ÷ poupança anual (None se não houver poupança)."""
    exigir_nao_negativos(custo_medida=custo_medida)
    return None if poupanca_anual <= 0 else custo_medida / poupanca_anual


# =====================================================================
# PASSO 3 — Comparar tarifários personalizados
# =====================================================================

def comparar_tarifarios(consumo_kwh, dias, tarifarios):
    """Aplica o mesmo consumo e os mesmos dias a cada tarifário.

    tarifarios: lista de {"nome", "preco_energia", "preco_diario"}.
    Devolve uma lista de {"nome", "energia", "potencia", "total"},
    ordenada do total mais baixo para o mais alto. Não decide qual é
    "o melhor": só mostra os resultados calculados.
    """
    resultados = []
    for t in tarifarios:
        f = fatura_simplificada(consumo_kwh, t["preco_energia"], t["preco_diario"], dias)
        resultados.append({"nome": t["nome"], **f})
    return sorted(resultados, key=lambda r: r["total"])


# =====================================================================
# PASSO 4 — Tabela comparativa (pandas) para o gráfico
# =====================================================================

def tabela_comparativa(resultados):
    """Transforma o resultado de comparar_tarifarios() num DataFrame.

    Colunas: "Tarifário", "Energia (€)", "Potência (€)", "Total (€)",
    "Diferença (€)" (em relação ao mais barato, que fica com 0).
    """
    if not resultados:
        return pd.DataFrame(columns=["Tarifário", "Energia (€)", "Potência (€)",
                                     "Total (€)", "Diferença (€)"])
    minimo = min(r["total"] for r in resultados)
    return pd.DataFrame([{
        "Tarifário": r["nome"], "Energia (€)": r["energia"], "Potência (€)": r["potencia"],
        "Total (€)": r["total"], "Diferença (€)": r["total"] - minimo,
    } for r in resultados])


# =====================================================================
# PASSO 5 — Opção bi-horária (vazio / fora de vazio)
# =====================================================================

def fatura_bi_horaria(consumo_vazio, preco_vazio, consumo_fora_vazio,
                      preco_fora_vazio, preco_diario, dias):
    """Fatura com dois períodos horários, cada um com o seu consumo e preço.

    Os consumos vêm do utilizador (ou de dados medidos): nunca dividir
    o consumo total 50/50 automaticamente.
    Devolve {"energia_vazio", "energia_fora_vazio", "energia", "potencia", "total"}.
    """
    f = fatura_por_periodos({"vazio": consumo_vazio, "fora_vazio": consumo_fora_vazio},
                            {"vazio": preco_vazio, "fora_vazio": preco_fora_vazio},
                            preco_diario, dias)
    return {"energia_vazio": f["por_periodo"]["vazio"],
            "energia_fora_vazio": f["por_periodo"]["fora_vazio"],
            "energia": f["energia"], "potencia": f["potencia"], "total": f["total"]}
