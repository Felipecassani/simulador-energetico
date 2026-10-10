"""Ofertas comerciais de eletricidade (dados oficiais da ERSE) e o top das mais baratas.

Fonte: simulador de preços da ERSE, ligação "Ofertas comerciais (CSV)" na página inicial
(https://simuladorprecos.erse.pt/). Cópia local em nucleo/dados/ofertas_erse_<AAAAMMDD>.zip
(é usada a mais recente). É um ZIP com dois CSV (UTF-8 com BOM, separador ";", vírgula
decimal, datas dd/mm/aaaa, caminhos com "\\") ligados por COM + COD_Proposta:
  csv\\Precos_ELEGN.csv    — preços SEM IVA por oferta, potência e ciclo. As colunas de
                            energia são partilhadas conforme o ciclo (Contagem):
                            "TV|TVFV|TVP" · "TVV|TVC" · "TVVz"
  csv\\CondComerciais.csv  — nome, segmento, fornecimento (ELE/GN/DUAL), validade,
                            indexada, fidelização, restrições, reembolsos, ligações
Confirmado com o ficheiro de 29/09/2026: a regulada (COM "TUR") dá 0,162 €/kWh até 2,3 kVA,
igual ao documento da ERSE sem IVA.

Ficam de fora do top: indexadas (o preço do ficheiro é só de referência), duais (obrigam a
contratar também o gás), com restrições (sócios, clientes de outra empresa, carro elétrico),
fora de validade, só para empresas, e a própria tarifa regulada (mostrada à parte).
Reembolsos (saldo em cartões, percentagens "de volta") NÃO entram no preço: são assinalados.
"""
import csv
import io
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from nucleo import tarifas

DADOS = Path(__file__).resolve().parent / "dados"
CONTAGEM = {"1": "simples", "2": "bi", "3": "tri"}
# período de cada coluna de energia, conforme o ciclo
COLUNAS = ("TV|TVFV|TVP", "TVV|TVC", "TVVz")
PERIODOS_POR_COLUNA = {
    "simples": ("simples",),
    "bi": ("fora_vazio", "vazio"),
    "tri": ("ponta", "cheias", "vazio"),
}
NOMES = {
    "ACCIONA": "Acciona", "ALFAENERGIA": "Alfa Energia", "AUDAX": "Audax", "COOP": "Coopérnico",
    "CURLIS": "CUR Lisboagás", "DOUROGAS": "Dourogás", "EDPC": "EDP Comercial",
    "ELERGONE": "Elergone", "END": "Endesa", "ENIPLENITUDE": "Plenitude", "EZUENERGIA": "Ezu Energia",
    "GALP": "Galp", "GOLD": "Goldenergy", "IBD": "Iberdrola", "IBELECTRA": "Ibelectra",
    "JAFPLUS": "Jafplus", "LOGICA": "Lógica Energy", "LUZBOA": "Luzboa", "LUZIGAS": "LUZiGÁS",
    "MEOENERGIA": "MEO Energia", "NABALIAENERGIA": "Nabalia Energia", "NOSSAENERGIA": "Nossa Energia",
    "OENEO": "Oeneo", "PORTULOGOS": "Portulogos", "REPSOL": "Repsol", "TUR": "Tarifa regulada",
    "U1": "U1", "USENERGY": "US Energy", "YESENERGY": "Yes Energy", "ZUG POWER": "Zug Power",
}


@dataclass(frozen=True)
class Oferta:
    comercializador: str            # nome a mostrar
    codigo: str
    nome: str
    kva: float
    opcao: str                      # simples · bi · tri
    potencia_dia: float             # €/dia sem IVA
    energia: dict                   # {período: €/kWh sem IVA}
    indexada: bool = False
    dual: bool = False
    restricoes: bool = False
    domestica: bool = True
    fidelizacao: bool = False
    reembolsos: bool = False        # benefícios à parte (saldo, devoluções): não entram no preço
    inicio: object = None           # date
    fim: object = None              # date
    consumo_minimo_ano: float = 0.0
    ligacao: str = ""
    com: str = ""                   # código da ERSE (GOLD, EDPC, TUR…)


def _numero(texto):
    """'0,1654' · '0.1654' · '2E-05' · '' → float ou None."""
    texto = (texto or "").strip().replace("€", "").replace(" ", "")
    if not texto:
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _sim(texto):
    return (texto or "").strip().upper() in ("S", "SIM", "1", "TRUE", "Y")


def _data(texto):
    try:
        return datetime.strptime((texto or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _ler_csv(conteudo):
    for codificacao in ("utf-8-sig", "cp1252", "latin-1"):    # latin-1 nunca falha
        try:
            texto = conteudo.decode(codificacao)
            break
        except UnicodeDecodeError:
            continue
    dialeto = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=";,\t")
    return [{(k or "").strip(): (v or "").strip() for k, v in linha.items()}
            for linha in csv.DictReader(io.StringIO(texto), dialect=dialeto)]


def _coluna(linha, inicio):
    """Valor da coluna cujo nome começa por `inicio` (as colunas trazem a unidade no nome)."""
    return next((v for k, v in linha.items() if k.startswith(inicio)), "")


def ler_zip(conteudo):
    """ZIP da ERSE (bytes) → lista de Oferta de eletricidade (todas, sem filtrar)."""
    with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
        nomes = {}
        for n in z.namelist():
            base = re.split(r"[\\/]", n)[-1]
            if not base.startswith("._"):
                nomes[base.lower()] = n
        precos_nome = next((n for k, n in nomes.items() if k.startswith("precos")), None)
        cond_nome = next((n for k, n in nomes.items() if k.startswith("cond")), None)
        if not precos_nome or not cond_nome:
            raise ValueError("O ZIP da ERSE não tem os ficheiros de preços e de condições.")
        precos, condicoes = _ler_csv(z.read(precos_nome)), _ler_csv(z.read(cond_nome))

    cond = {(c.get("COM"), c.get("COD_Proposta") or c.get("CODProposta")): c for c in condicoes}
    ofertas = []
    for linha in precos:
        opcao = CONTAGEM.get(linha.get("Contagem", ""))
        kva, tf = _numero(linha.get("Pot_Cont")), _numero(linha.get("TF"))
        c = cond.get((linha.get("COM"), linha.get("COD_Proposta")))
        if not opcao or kva is None or tf is None or c is None:
            continue                         # gás, linhas incompletas ou sem condições
        valores = [_numero(linha.get(col)) for col in COLUNAS]
        periodos = PERIODOS_POR_COLUNA[opcao]
        if any(v is None for v in valores[:len(periodos)]):
            continue
        com = linha.get("COM", "")
        ofertas.append(Oferta(
            comercializador=NOMES.get(com, com.title()), codigo=linha.get("COD_Proposta", ""),
            nome=(c.get("NomeProposta") or "").strip(), kva=kva, opcao=opcao, potencia_dia=tf,
            energia=dict(zip(periodos, valores)),
            indexada=_sim(_coluna(c, "FiltroPrecosIndex")), dual=c.get("Fornecimento") == "DUAL",
            restricoes=_sim(_coluna(c, "FiltroRestri")), domestica=c.get("Segmento") in ("Dom", "Tod"),
            fidelizacao=_sim(_coluna(c, "FiltroFideliza")),
            reembolsos=any((_numero(_coluna(c, k)) or 0) > 0
                           for k in ("ReembFixo", "ReembTF_ELE", "ReembTW_ELE", "ReembW_ELE")),
            inicio=_data(c.get("Data ini")), fim=_data(c.get("Data fim")),
            consumo_minimo_ano=_numero(c.get("ConsIni_ELE")) or 0.0,
            ligacao=(c.get("LinkFichaPadrao") or c.get("LinkOfertaCom") or "").strip(), com=com))
    return ofertas


def ficheiro_local():
    """O ZIP de ofertas mais recente em nucleo/dados (ou None)."""
    zips = sorted(p for p in DADOS.glob("ofertas_erse_*.zip") if not p.name.startswith("._"))
    return zips[-1] if zips else None


def data_do_ficheiro(caminho):
    m = re.search(r"(\d{8})", Path(caminho).name)
    return datetime.strptime(m.group(1), "%Y%m%d").date() if m else None


def custo(oferta, consumos, dias):
    """Custo sem IVA no período: potência × dias + Σ kWh × preço do período."""
    return oferta.potencia_dia * dias + sum(kwh * oferta.energia[p] for p, kwh in consumos.items())


def elegivel(oferta, hoje=None, consumo_ano=None, incluir_duais=False, incluir_restricoes=False):
    """Oferta que qualquer casa pode contratar hoje só de eletricidade, a preço fixo
    (as duais e as com restrições só entram se pedidas)."""
    hoje = hoje or date.today()
    return (oferta.domestica and not oferta.indexada
            and (incluir_duais or not oferta.dual) and (incluir_restricoes or not oferta.restricoes)
            and oferta.com != "TUR"
            and (oferta.inicio is None or oferta.inicio <= hoje)
            and (oferta.fim is None or hoje <= oferta.fim)
            and (consumo_ano is None or consumo_ano >= oferta.consumo_minimo_ano))


def mais_baratas(ofertas, total_kwh, dias, kva, pct_vazio=None, pct_ponta=None, n=3, hoje=None,
                 por_empresa=True, incluir_duais=False, incluir_restricoes=False,
                 so_sem_fidelizacao=False, excluir=()):
    """As n ofertas de preço fixo mais baratas para este consumo e potência.

    Sem repartição do contador (pct_vazio None), só entram ofertas de tarifa simples; sem
    consumo em ponta conhecido (pct_ponta None, fatura bi-horária), as tri ficam de fora.
    Devolve [(oferta, custo no período)], da mais barata para a mais cara: a melhor oferta de
    cada comercializador (por_empresa) ou de cada oferta (a opção horária mais barata).
    """
    tem_perfil = pct_vazio is not None
    repartido = tarifas.distribuir_consumo(total_kwh, pct_vazio or 0.0, pct_ponta or 0.0)
    consumo_ano = total_kwh * 365 / dias if dias else None
    melhores = {}
    for o in ofertas:
        if (not elegivel(o, hoje, consumo_ano, incluir_duais, incluir_restricoes)
                or (so_sem_fidelizacao and o.fidelizacao) or o.comercializador in excluir
                or abs(o.kva - kva) > 1e-6
                or (not tem_perfil and o.opcao != "simples")
                or (tem_perfil and pct_ponta is None and o.opcao == "tri")):
            continue
        valor = custo(o, repartido[o.opcao], dias)
        chave = o.comercializador if por_empresa else (o.comercializador, o.nome or o.codigo)
        if chave not in melhores or valor < melhores[chave][1]:
            melhores[chave] = (o, valor)
    return sorted(melhores.values(), key=lambda par: par[1])[:n]   # n=None: todas


def potencia_indexadas(ofertas, kva, procurar):
    """{(comercializador, texto): €/dia} das ofertas indexadas simples cujo nome contém o texto."""
    saida = {}
    for comercializador, texto in procurar:
        for o in ofertas:
            if (o.indexada and o.opcao == "simples" and abs(o.kva - kva) < 1e-6
                    and o.comercializador == comercializador and texto.lower() in o.nome.lower()):
                saida[(comercializador, texto)] = o.potencia_dia
                break
    return saida


def resumo_mercado(ofertas, kwh_mes=300, kva=6.9):
    """Números para a Início (sempre calculados, nunca escritos à mão): quantas ofertas de preço
    fixo e de quantas empresas uma casa típica pode contratar hoje, e quanto a mais custa por ano
    a mais cara face à mais barata (sem IVA, tarifa simples). None se não houver ofertas."""
    todas = mais_baratas(ofertas, kwh_mes, 30, kva, n=None, por_empresa=False)
    if len(todas) < 2:
        return None
    return {"ofertas": len(todas), "empresas": len({o.comercializador for o, _ in todas}),
            "diferenca_ano": (todas[-1][1] - todas[0][1]) * 365 / 30, "kwh_mes": kwh_mes, "kva": kva}
