"""Consumos de 15 em 15 minutos do Balcão Digital da E-REDES (Excel ou CSV).

Formato confirmado com um ficheiro real (01/10/2026), folha "Dados de Energia":
  linhas de cabeçalho (CPE, "Mês/Ano", "Intervalo: 15 min"), depois
  Data | Hora | Consumo registado (kW) | Estado     ex.: 2026/09/01 | 00:15 | 0,464 | Real
  A hora marca o FIM do quarto de hora; o último intervalo de cada dia vem como 00:00 do dia
  seguinte. O consumo é a potência média (kW) do quarto de hora → kWh = kW × 0,25.
A leitura continua tolerante a variações:
  - procura a linha de cabeçalho com "Data" e "Hora" (ou uma coluna de data e hora juntas);
  - a coluna de consumo é a que tem "consumo", "kw" ou "energia" no nome;
  - em kW (potência média do quarto de hora) multiplica por 0,25 h; em kWh usa direto;
  - se o primeiro registo é 00:15 (ou aparece 24:00), a hora marca o fim do intervalo.
"""
import csv
import io
import re
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from nucleo import periodos

QUARTO = timedelta(minutes=15)


def _celulas_xlsx(conteudo):
    import warnings

    from openpyxl import load_workbook
    with warnings.catch_warnings():             # o ficheiro da E-REDES não tem estilo por omissão
        warnings.simplefilter("ignore")
        livro = load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    for folha in livro.worksheets:
        yield from folha.iter_rows(values_only=True)


def _celulas_csv(conteudo):
    texto = conteudo.decode("utf-8-sig", errors="replace")
    separador = ";" if texto.count(";") >= texto.count(",") else ","
    yield from csv.reader(io.StringIO(texto), delimiter=separador)


def _numero(v):
    if isinstance(v, (int, float)):
        return float(v)
    texto = str(v or "").strip().replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _data(v):
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    texto = str(v or "").strip()
    for formato in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M",
                    "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def _hora(v):
    """(horas, minutos) — aceita time, datetime, '00:15', '24:00'."""
    if isinstance(v, (time, datetime)):
        return v.hour, v.minute
    m = re.match(r"^\s*(\d{1,2})[:h](\d{2})", str(v or ""))
    return (int(m.group(1)), int(m.group(2))) if m else None


def ler(nome, conteudo):
    """→ [(início do quarto de hora em Lisboa, kWh)] por ordem."""
    linhas = list(_celulas_xlsx(conteudo) if nome.lower().endswith((".xlsx", ".xlsm"))
                  else _celulas_csv(conteudo))
    cabecalho, i_cab = None, None
    for i, linha in enumerate(linhas):
        nomes = [str(c or "").strip().lower() for c in linha]
        if any("data" in n for n in nomes) and any(("consumo" in n or "kw" in n or "energia" in n)
                                                     for n in nomes):
            cabecalho, i_cab = nomes, i
            break
    if cabecalho is None:
        raise ValueError("Não encontrei as colunas de data e consumo neste ficheiro.")
    c_data = next(i for i, n in enumerate(cabecalho) if "data" in n)
    c_hora = next((i for i, n in enumerate(cabecalho) if n.startswith("hora")), None)
    c_valor = next(i for i, n in enumerate(cabecalho)
                   if ("consumo" in n or "kw" in n or "energia" in n) and i not in (c_data, c_hora))
    em_kw = "kw" in cabecalho[c_valor] and "kwh" not in cabecalho[c_valor]
    c_estado = next((i for i, n in enumerate(cabecalho) if n.startswith("estado")), None)

    brutos = []
    for linha in linhas[i_cab + 1:]:
        if len(linha) <= max(c_data, c_valor, c_hora or 0):
            continue
        dia, valor = _data(linha[c_data]), _numero(linha[c_valor])
        if dia is None or valor is None:
            continue
        hm = _hora(linha[c_hora]) if c_hora is not None else (dia.hour, dia.minute)
        if hm is None:
            continue
        estimado = c_estado is not None and len(linha) > c_estado and "estim" in str(linha[c_estado] or "").lower()
        brutos.append((dia.replace(hour=0, minute=0, second=0), hm, valor * 0.25 if em_kw else valor, estimado))
    if not brutos:
        raise ValueError("O ficheiro não tem consumos de 15 em 15 minutos.")
    # a E-REDES marca o fim do intervalo: o 1.º registo é 00:15 e o último de cada dia é 00:00 do seguinte
    marca_fim = brutos[0][1] == (0, 15) or any(hm == (24, 0) for _, hm, _, _ in brutos)
    registos = []
    for dia, (h, m), kwh, _ in brutos:
        inicio = dia + timedelta(hours=h, minutes=m) - (QUARTO if marca_fim else timedelta(0))
        registos.append((inicio.replace(tzinfo=periodos.LISBOA), kwh))
    ler.estimados = sum(1 for *_, e in brutos if e)      # quantos valores eram estimados
    return sorted(registos)


def analisar(registos):
    """Totais, repartição pelos períodos, pico e consumo médio por hora do dia."""
    total = sum(k for _, k in registos)
    dias = max(1, round(len(registos) / 96))            # dias completos de quartos de hora
    por_periodo = {o: defaultdict(float) for o in ("bi", "tri")}
    por_hora = defaultdict(float)
    for t, kwh in registos:
        for o in por_periodo:
            por_periodo[o][periodos.periodo(t, o)] += kwh
        por_hora[t.hour] += kwh
    pct = lambda o, p: 100 * por_periodo[o][p] / total if total else 0.0
    return {
        "total_kwh": total, "dias": dias, "inicio": registos[0][0].date(), "fim": registos[-1][0].date(),
        "pct_vazio": pct("tri", "vazio"), "pct_ponta": pct("tri", "ponta"),
        "pico_kw": max(k for _, k in registos) * 4,
        "media_por_hora": [por_hora[h] / dias if dias else 0.0 for h in range(24)],
    }


def preco_ponderado(registos, precos_omie):
    """€/MWh médio que o teu perfil paga no mercado (ponderado pelo consumo) e a média simples.

    precos_omie: [(instante, €/MWh)]. Quartos de hora sem preço ficam de fora.
    """
    mapa = {t.astimezone(periodos.LISBOA).replace(second=0, microsecond=0): v for t, v in precos_omie}
    horario = len(precos_omie) > 1 and (precos_omie[1][0] - precos_omie[0][0]) >= timedelta(hours=1)
    soma, kwh_total, valores = 0.0, 0.0, []
    for t, kwh in registos:
        chave = t.replace(minute=0) if horario else t
        if chave in mapa:
            soma += kwh * mapa[chave]
            kwh_total += kwh
            valores.append(mapa[chave])
    if not kwh_total:
        return None
    return {"ponderado": soma / kwh_total, "simples": sum(valores) / len(valores)}
