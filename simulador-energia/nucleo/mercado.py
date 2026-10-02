"""Dados oficiais em tempo real: preços do mercado OMIE e tarifas da ERSE.

- OMIE: ficheiro diário "marginalpdbcpt" com o preço marginal de Portugal (€/MWh),
  em períodos de 15 min (ou 1 h nos ficheiros antigos), em hora de Espanha (CET).
- ERSE: tarifas BTN do documento oficial do ano. Há uma cópia local em
  nucleo/dados/erse_2026.json; obter_erse_online() tenta ler o documento original.

Sem Streamlit (a cache fica na interface). Com SIMULADOR_OFFLINE=1 nada vai à rede.
"""
import http.client
import io
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")
LISBOA = ZoneInfo("Europe/Lisbon")
DADOS = Path(__file__).resolve().parent / "dados"

URL_OMIE = ("https://www.omie.es/es/file-download?parents%5B0%5D=marginalpdbcpt"
            "&filename=marginalpdbcpt_{data:%Y%m%d}.1")
TEMPO_LIMITE = 15


class SemRede(ConnectionError):
    """Modo offline ativo ou fonte indisponível."""


def _descarregar(url, tempo=TEMPO_LIMITE):
    if os.environ.get("SIMULADOR_OFFLINE") == "1":
        raise SemRede("modo offline")
    pedido = Request(url, headers={"User-Agent": "simulador-energia/1.0 (projeto pessoal)"})
    try:
        with urlopen(pedido, timeout=tempo) as resposta:
            return resposta.read()
    except (OSError, http.client.HTTPException) as erro:   # sem rede, 404, descarga cortada
        raise SemRede(str(erro)) from erro


# =====================================================================
# OMIE
# =====================================================================

def ler_omie(texto):
    """Converte um ficheiro marginalpdbcpt em [(instante em Lisboa, €/MWh)].

    Os períodos contam a partir da meia-noite de Espanha; a conversão passa por
    UTC, por isso os dias com mudança de hora (23 ou 25 h) ficam certos.
    """
    linhas = [l.split(";") for l in texto.strip().splitlines() if re.match(r"^\d{4};", l)]
    if not linhas:
        raise ValueError("Ficheiro OMIE sem dados")
    ano, mes, dia = (int(x) for x in linhas[0][:3])
    n = len(linhas)
    passo = timedelta(minutes=15) if n > 30 else timedelta(hours=1)
    meia_noite_utc = datetime(ano, mes, dia, tzinfo=MADRID).astimezone(timezone.utc)
    precos = []
    for campos in linhas:
        periodo = int(campos[3])
        valor = float(campos[4].replace(",", "."))
        instante = (meia_noite_utc + (periodo - 1) * passo).astimezone(LISBOA)
        precos.append((instante, valor))
    return precos


def obter_omie(dia):
    """Preços OMIE de Portugal para um dia (lança SemRede se não houver acesso)."""
    bruto = _descarregar(URL_OMIE.format(data=dia))
    texto = bruto.decode("latin-1")
    if "MARGINALPDBC" not in texto.upper():
        raise SemRede(f"OMIE ainda não publicou {dia:%d/%m/%Y}")
    return ler_omie(texto)


def obter_omie_varios(fim, dias):
    """Preços dos últimos `dias` dias até `fim` (inclusive). Dias em falta são ignorados."""
    todos, falhados = [], []
    for k in range(dias - 1, -1, -1):
        dia = fim - timedelta(days=k)
        try:
            todos.extend(obter_omie(dia))
        except SemRede:
            falhados.append(dia)
    if not todos:
        raise SemRede("Sem dados OMIE para o intervalo pedido")
    return todos, falhados


def melhor_janela(precos, horas, depois_de=None):
    """As `horas` seguidas mais baratas: (início, fim, média €/MWh), ou None se não couber.

    precos: [(instante, €/MWh)] em passos iguais (15 min ou 1 h); depois_de corta o passado.
    """
    pontos = [(t, v) for t, v in precos if depois_de is None or t >= depois_de]
    if not pontos:
        return None
    passo = pontos[1][0] - pontos[0][0] if len(pontos) > 1 else timedelta(hours=1)
    n = max(1, round(timedelta(hours=horas) / passo))
    if len(pontos) < n:
        return None
    soma = sum(v for _, v in pontos[:n])
    melhor, melhor_soma = 0, soma
    for i in range(1, len(pontos) - n + 1):          # janela deslizante
        soma += pontos[i + n - 1][1] - pontos[i - 1][1]
        if soma < melhor_soma - 1e-9:
            melhor, melhor_soma = i, soma
    return pontos[melhor][0], pontos[melhor + n - 1][0] + passo, melhor_soma / n


def resumo_omie(precos):
    """Média, mínimo e máximo em €/MWh."""
    valores = [v for _, v in precos]
    return {"media": sum(valores) / len(valores), "min": min(valores), "max": max(valores),
            "n": len(valores)}


# =====================================================================
# ERSE
# =====================================================================

def ficheiro_erse(ano=None):
    """Caminho da cópia local da ERSE: a do ano pedido ou a mais recente (erse_<ano>.json)."""
    if ano is not None:
        return DADOS / f"erse_{ano}.json"
    return max(DADOS.glob("erse_*.json"), key=lambda f: int(f.stem.split("_")[1]))


def carregar_erse_local(ano=None):
    """Cópia local das tarifas ERSE (extraída do documento oficial).

    Na mudança de ano basta acrescentar nucleo/dados/erse_<ano>.json (com o URL do
    documento novo): passa a ser a usada. Os testes pedem sempre ano=2026.
    """
    dados = json.loads(ficheiro_erse(ano).read_text(encoding="utf-8"))
    dados["origem"] = "cópia local"
    return dados


def _numero(texto):
    return float(texto.replace(",", "."))


def ler_quadro_erse(texto_pagina, ordem=0, exigir_6_9=True):
    """Lê um quadro BTN de uma página do documento da ERSE (ordem = 0, 1, …).

    Estrutura do texto: 'EUR/dia', linhas 'kVA preço', 'EUR/kWh' e 6 linhas de
    energia pela ordem simples · fora de vazio · vazio · ponta · cheias · vazio.
    """
    bloco = texto_pagina.split("EUR/dia")[1 + ordem]
    potencia_txt, energia_txt = bloco.split("EUR/kWh", 1)
    potencia = {}
    for kva, preco in re.findall(r"^\s*(\d+(?:,\d+)?)\s+(\d+,\d{4})\s*$", potencia_txt, re.M):
        potencia[str(_numero(kva))] = _numero(preco)
    rotulos = ["Tarifa simples", "Horas de fora de vazio", "Horas de vazio",
               "Horas de ponta", "Horas cheias", "Horas de vazio"]
    valores, resto = [], energia_txt
    for rotulo in rotulos:
        m = re.search(re.escape(rotulo) + r"\s+(\d+,\d{4})", resto)
        if not m:
            raise ValueError(f"Não encontrei '{rotulo}' no quadro da ERSE")
        valores.append(_numero(m.group(1)))
        resto = resto[m.end():]
    if exigir_6_9 and "6.9" not in potencia:
        raise ValueError("Quadro da ERSE sem o escalão de 6,9 kVA")
    s, bf, bv, tp, tc, tv = valores
    return {"potencia_eur_dia": potencia,
            "energia_eur_kwh": {"simples": {"simples": s},
                                "bi": {"fora_vazio": bf, "vazio": bv},
                                "tri": {"ponta": tp, "cheias": tc, "vazio": tv}}}


def ler_documento_erse(pdf_bytes):
    """Procura no documento oficial os quadros da tarifa regulada e das TAR (BTN)."""
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    try:
        leitor = PdfReader(io.BytesIO(pdf_bytes))
    except (PyPdfError, ValueError, OSError) as erro:
        raise ValueError("O documento descarregado da ERSE não é um PDF legível") from erro
    tar = regulada = None
    for pagina in leitor.pages:
        texto = pagina.extract_text() or ""
        if tar is None and "ACESSO ÀS REDES EM BTN (≤20,7 kVA)" in texto \
                and "ARMAZENAMENTO" not in texto:
            tar = ler_quadro_erse(texto)
        if regulada is None and "EM BTN (≤20,7 kVA e >2,3 kVA)" in texto:
            regulada = ler_quadro_erse(texto)
            # 2.º quadro da mesma página: potências até 2,3 kVA (preço simples próprio)
            pequena = ler_quadro_erse(texto, ordem=1, exigir_6_9=False)
            regulada["potencia_eur_dia"].update(pequena["potencia_eur_dia"])
            regulada["energia_simples_ate_2_3_kva"] = pequena["energia_eur_kwh"]["simples"]["simples"]
        if tar and regulada:
            break
    if not (tar and regulada):
        raise ValueError("Não encontrei os quadros BTN no documento da ERSE")
    return tar, regulada


def obter_erse_online():
    """Descarrega o documento oficial e devolve as tarifas no formato da cópia local."""
    base = carregar_erse_local()
    tar, regulada = ler_documento_erse(_descarregar(base["url"], tempo=60))
    for destino, lido in ((base["tar"], tar), (base["regulada"], regulada)):
        destino["potencia_eur_dia"].update(lido["potencia_eur_dia"])
        destino["energia_eur_kwh"] = lido["energia_eur_kwh"]
        if "energia_simples_ate_2_3_kva" in lido:
            destino["energia_simples_ate_2_3_kva"] = lido["energia_simples_ate_2_3_kva"]
    base["origem"] = "ERSE (documento oficial, lido agora)"
    base["extraido_em"] = date.today().isoformat()
    return base


def diferencas_erse(a, b):
    """Lista os preços que mudaram entre duas versões das tarifas (vazia se iguais)."""
    mudancas = []
    for bloco in ("regulada", "tar"):
        for chave, valor in a[bloco]["potencia_eur_dia"].items():
            if abs(valor - b[bloco]["potencia_eur_dia"].get(chave, valor)) > 1e-9:
                mudancas.append(f"{bloco} potência {chave} kVA")
        for opcao, periodos in a[bloco]["energia_eur_kwh"].items():
            for periodo, valor in periodos.items():
                if abs(valor - b[bloco]["energia_eur_kwh"][opcao][periodo]) > 1e-9:
                    mudancas.append(f"{bloco} {opcao}/{periodo}")
    return mudancas
