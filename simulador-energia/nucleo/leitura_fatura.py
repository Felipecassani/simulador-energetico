"""Ler uma fatura de eletricidade (PDF ou foto) e sugerir os valores dos campos.

Tudo acontece neste computador: o ficheiro é lido em memória e não é guardado.
As faturas variam de comercializador para comercializador, por isso isto é uma
ajuda para preencher, não uma verdade: a pessoa confirma sempre os valores.
"""
import io
import re
from datetime import date

# sobe quando a leitura muda: o site volta a ler a fatura já carregada
VERSAO = 6

PERIODOS = [("vazio", r"\bvazio\b"), ("ponta", r"\bponta\b"), ("cheias", r"\bcheias?\b"),
            ("simples", r"\bsimples\b")]
# "Fora de Vazio", "Fora do Vazio", "Fora-Vazio", "F. Vazio"
FORA_VAZIO = re.compile(r"fora[\s.\-]*(?:d[eo]\s+)?vazio|\bf\.?\s*vazio\b", re.I)
# milhares com ponto, ou com espaço só se o número não vier colado a outro ("2026 204" ≠ 26 204)
NUM = (r"(?<![\d/.,])[1-9]\d{0,2}(?:[  ]\d{3})+(?:,\d+)?"
       r"|\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?")
DATA = r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})"
# faturas duplas: as linhas do gás não contam para a eletricidade
GAS = re.compile(r"g[áa]s\b|\bgn\b|m3\b|m³", re.I)
# linhas só informativas ("7,10€ (0,2291 €/Dia * 31 Dia) Acessos…", valores de referência)
INFORMATIVA = re.compile(r"^\s*\d+(?:[.,]\d+)?\s*€\s*\(|valor base|por refer[êe]ncia|"
                         r"inclui os encargos|gasto m[ée]dio", re.I)
# linhas de energia que não são o preço da energia (TAR à parte, descontos, impostos)
NAO_E_PRECO = re.compile(r"acesso|\btar\b|redes|desconto|imposto|\biec\b|tarifa social|"
                         r"contribui|taxa", re.I)
# sinais de um tarifário indexado ao mercado (na parte da eletricidade)
INDEXADO = re.compile(r"index|\bomie\b|mercado\s+(?:grossista|di[áa]rio|ib[ée]rico|spot)|"
                      r"pre[çc]o\s+(?:vari[áa]vel|din[âa]mico)|tarif[áa]rio\s+din[âa]mico|"
                      r"pre[çc]o\s+de\s+mercado", re.I)
# sinais de preço fixo escritos na fatura
FIXO = re.compile(r"pre[çc]o\s+fixo|equiparad[ao]\s+[àa]\s+tarifa\s+regulada|tarifa\s+fixa", re.I)
OPCAO_ESCRITA = re.compile(r"(?:kva\s*/\s*|op[çc][ãa]o\s+hor[áa]ria\W*|tarifa\s+)"
                           r"(simples|bi[- ]?hor[áa]ri\w*|tri[- ]?hor[áa]ri\w*)", re.I)


def numero(texto):
    """'1.234,56' → 1234.56 · '1 120' → 1120 · '0,1654' → 0.1654 · '0.165' → 0.165"""
    t = texto.strip().replace(" ", "").replace(" ", "")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif t.count(".") > 1 or re.fullmatch(r"[1-9]\d{0,2}\.\d{3}", t):
        t = t.replace(".", "")          # separador de milhares (nunca num '0.xxx')
    return float(t)


def texto_de_pdf(conteudo):
    from pypdf import PdfReader

    leitor = PdfReader(io.BytesIO(conteudo))
    return "\n".join(p.extract_text() or "" for p in leitor.pages)


def ocr_disponivel():
    """True se este computador consegue ler fotos (macOS com o pacote ocrmac)."""
    import importlib.util
    import sys
    return sys.platform == "darwin" and importlib.util.find_spec("ocrmac") is not None


def texto_de_imagem(conteudo):
    """OCR local (Apple Vision, através do pacote ocrmac). Só funciona em macOS.

    A imagem passa em memória para o OCR: não é escrita em disco.
    """
    from ocrmac import ocrmac
    from PIL import Image

    imagem = Image.open(io.BytesIO(conteudo)).convert("RGB")
    linhas = ocrmac.OCR(imagem, language_preference=["pt-BR"]).recognize()
    return "\n".join(l[0] for l in linhas)


def _periodos_da_linha(linha):
    """Períodos mencionados numa linha (o 'fora de vazio' não conta também como 'vazio')."""
    encontrados = []
    if FORA_VAZIO.search(linha):
        encontrados.append("fora_vazio")
        linha = FORA_VAZIO.sub(" ", linha)
    baixa = linha.lower()
    encontrados += [nome for nome, padrao in PERIODOS if re.search(padrao, baixa)]
    return encontrados


def _opcao(texto):
    t = texto.lower()
    if t.startswith("tri"):
        return "tri"
    if t.startswith("bi"):
        return "bi"
    return "simples"


def _preco_depois(baixa, unidade):
    """Preço unitário a seguir a uma quantidade: '… 72 kWh 0,1386 9,97' ou '… 31 Dia 0,2502 7,75'.

    Aceita também a forma com unidade explícita: '0,1654 €/kWh', '0,3659 EUR/dia'.
    Um número com '-' à frente (desconto) não conta.
    """
    m = re.search(r"(?<!-)(?<!- )(" + NUM + r")\s*(?:€|eur)?\s*/\s*" + unidade, baixa)
    if m:
        return numero(m.group(1))
    m = re.search(r"\b" + unidade + r"s?\b\s*(?:x\s*)?(\d+,\d{3,})", baixa)
    return numero(m.group(1)) if m else None


# comercializadores de eletricidade em Portugal (nome a mostrar, padrão no texto da fatura)
COMERCIALIZADORES = [
    ("Goldenergy", r"gold\s?energy"), ("EDP Comercial", r"\bedp\b(?![\s\-–]*(?:distribui|servi[çc]o\s+universal))"),
    ("Endesa", r"\bendesa\b"), ("Iberdrola", r"\biberdrola\b"), ("Galp", r"\bgalp\b"),
    ("Repsol", r"\brepsol\b"), ("MEO Energia", r"\bmeo\s+energia\b"),
    ("Coopérnico", r"\bcoop[ée]rnico\b"), ("LUZiGÁS", r"\bluzig[áa]s\b"), ("G9", r"\bg9\b"),
    ("Plenitude", r"\bplenitude\s+(?:energia|portugal)\b|plenitude\.pt|eniplenitude"), ("SU Eletricidade", r"\bsu\s+eletricidade\b"),
    ("Muon", r"\bmuon\b"), ("Ylce", r"\bylce\b"), ("Energia Simples", r"energiasimples\.pt|energia\s+simples,?\s+(?:s\.?\s?a\b|lda)"),  # também é linha da fatura
    ("Luzboa", r"\bluzboa\b"), ("Audax", r"\baudax\b"), ("Enat", r"\benat\b"),
    ("Ezu Energia", r"\bezu\b"), ("Alfa Energia", r"\balfa\s+energia\b"),
]


def comercializador(texto):
    """Empresa que emite a fatura: o nome conhecido que mais vezes aparece (o próprio aparece no
    cabeçalho, no rodapé, no site e nos contactos; outros nomes surgem só de passagem)."""
    melhor = None                                  # (vezes, -posição da 1.ª ocorrência, nome)
    for nome, padrao in COMERCIALIZADORES:
        encontrados = list(re.finditer(padrao, texto, re.I))
        if encontrados:
            candidato = (len(encontrados), -encontrados[0].start(), nome)
            melhor = max(melhor or candidato, candidato)
    return melhor[2] if melhor else None           # empate: a que aparece primeiro (cabeçalho)


def ler_fatura(texto):
    """Procura no texto os valores da eletricidade. Devolve só o que encontrou.

    Chaves possíveis: inicio, fim, dias, potencia_kva, preco_diario, opcao,
    consumos {período: kWh}, precos {período: €/kWh}, consumo_total, preco_energia,
    desconto_pct, campanha, precos_base {"energia": €/kWh, "potencia_dia": €/dia};
    e "evidencias" {campo: [linhas onde foi encontrado]}.

    Regras: ignora linhas do gás e linhas só informativas. Soma só as linhas de
    consumo cobradas (com preço unitário), sem repetir a mesma linha, porque as
    faturas repartem o consumo por taxas de IVA. A potência é a média, pesada pelos
    dias, de todas as linhas cobradas (algumas faturas cobram o acesso às redes à parte).
    """
    r, evid = {"consumos": {}, "precos": {}}, {}
    potencias, vistos = [], set()
    resumo, total_solto, preco_solto, opcao_escrita = {}, None, None, None
    base_dia, secao = [], None
    sinais_indexado, sinais_fixo = [], []

    def anotar(campo, linha):
        evid.setdefault(campo, []).append(linha)

    for linha in texto.splitlines():
        l = linha.strip()
        if not l:
            continue
        if GAS.search(l):
            secao = "gas"                 # as linhas seguintes sem "gás" ainda podem ser do gás
            continue
        baixa = l.lower()
        if re.search(r"el[eé]c?tricidade", baixa):
            secao = "eletricidade"

        # fixo ou indexado, e os parâmetros do indexado (muitas vezes em linhas informativas)
        if secao != "gas":
            if INDEXADO.search(l):
                sinais_indexado.append(l)
            if FIXO.search(l):
                sinais_fixo.append(l)
            m = re.search(r"perdas\D{0,30}?(\d+(?:[.,]\d+)?)\s*%", baixa)
            if m and "perdas_pct" not in r:
                r["perdas_pct"] = numero(m.group(1))
                anotar("perdas_pct", l)
            m = re.search(r"(?:fator|factor|coeficiente)\s+de\s+(?:ajustamento\s+(?:para|de)\s+)?"
                          r"perdas\D{0,20}?(\d+[.,]\d+)(?!\s*%)", baixa)
            if m and "perdas_pct" not in r:
                v = numero(m.group(1))
                r["perdas_pct"] = round((v - 1) * 100 if v >= 1 else v * 100, 2)   # 1,15 → 15 %
                anotar("perdas_pct", l)
            m = re.search(r"(?:margem|spread|\bfee\b|custos?\s+de\s+(?:gest[ãa]o|comercializa[çc][ãa]o))"
                          r"\D{0,30}?(" + NUM + r")\s*(?:€|eur)?\s*/\s*(kwh|mwh)", baixa)
            if m and "margem_kwh" not in r:
                v = numero(m.group(1))
                r["margem_kwh"] = round(v / 1000 if m.group(2) == "mwh" else v, 6)
                anotar("margem_kwh", l)
            m = re.search(r"\bomie\b\D{0,40}?(" + NUM + r")\s*(?:€|eur)?\s*/\s*(mwh|kwh)", baixa)
            if m and "omie_medio_mwh" not in r:
                v = numero(m.group(1))
                r["omie_medio_mwh"] = v if m.group(2) == "mwh" else v * 1000
                anotar("omie_medio_mwh", l)

        # campanha e preços sem desconto (vêm em linhas informativas, lidas antes de as saltar)
        m = re.search(r"desconto\s+(\d+(?:,\d+)?)\s*%", baixa)
        if m and "desconto_pct" not in r:
            r["desconto_pct"] = numero(m.group(1))
            anotar("desconto_pct", l)
        if "campanha" in baixa:
            r["campanha"] = True
        m = re.search(r"valor base de\s*(" + NUM + r")\s*€\s*/\s*(kwh|dia)", baixa)
        if m and secao != "gas":
            if m.group(2) == "kwh":
                r.setdefault("precos_base", {}).setdefault("energia", numero(m.group(1)))
            else:
                base_dia.append(numero(m.group(1)))
            anotar("precos_base", l)
        if INFORMATIVA.search(l):
            continue

        m = re.search(DATA + r"\s*(?:a|até|-|–)\s*" + DATA, l)
        if m and "inicio" not in r:
            d, mo, a, d2, mo2, a2 = (int(x) for x in m.groups())
            try:
                inicio, fim = date(a, mo, d), date(a2, mo2, d2)
            except ValueError:
                inicio = fim = None
            if inicio and fim and fim >= inicio:       # datas trocadas (ex.: OCR) não contam
                r["inicio"], r["fim"] = inicio, fim
                r["dias"] = (fim - inicio).days + 1
                anotar("dias", l)

        m = re.search(r"pot[êe]ncia\s+contratada\D{0,25}?(" + NUM + r")\s*kva", baixa)
        if m and "potencia_kva" not in r:
            r["potencia_kva"] = numero(m.group(1))
            anotar("potencia_kva", l)

        m = OPCAO_ESCRITA.search(l)
        if m and opcao_escrita is None:
            opcao_escrita = _opcao(m.group(1))
            anotar("opcao", l)

        qtd_dias = re.search(r"\b(\d{1,3})\s*dias?\b", baixa)
        if "pot" in baixa and qtd_dias:
            preco = _preco_depois(baixa, "dia")
            if preco is not None:
                potencias.append((int(qtd_dias.group(1)), preco))
                anotar("preco_diario", l)

        periodos_linha = _periodos_da_linha(l)
        kwh = re.search(r"(" + NUM + r")\s*kwh\b(?!\s*/)", baixa)
        preco = _preco_depois(baixa, "kwh")
        e_energia = any(p in baixa for p in ("consumo", "energia", "eletricidade", "electricidade"))
        cobrada = preco is not None and not NAO_E_PRECO.search(l) and "total" not in baixa
        if len(periodos_linha) == 1 and kwh and e_energia:
            periodo = periodos_linha[0]
            quantidade = numero(kwh.group(1))
            if cobrada:
                datas = tuple(re.findall(DATA, l))
                chave = (periodo, quantidade, datas, preco)
                if chave not in vistos:                  # a mesma linha repetida não soma
                    vistos.add(chave)
                    r["consumos"][periodo] = r["consumos"].get(periodo, 0) + quantidade
                    anotar(f"consumo_{periodo}", l)
                    if periodo not in r["precos"]:
                        r["precos"][periodo] = preco
                        anotar(f"preco_{periodo}", l)
            elif not NAO_E_PRECO.search(l):
                resumo.setdefault(periodo, quantidade)   # linha de resumo, sem preço
        elif not periodos_linha and kwh and "consumo" in baixa and total_solto is None:
            total_solto = numero(kwh.group(1))
            anotar("consumo_total", l)
        if not periodos_linha and cobrada and "energia" in baixa and kwh and preco_solto is None:
            preco_solto = preco
            anotar("preco_energia", l)

    if not r["consumos"] and resumo:                     # só havia linhas de resumo
        r["consumos"] = dict(resumo)
    consumos, precos = r["consumos"], r["precos"]
    if potencias:
        dias_ref = r.get("dias") or max(d for d, _ in potencias)
        r["preco_diario"] = sum(d * p for d, p in potencias) / dias_ref
    if base_dia:
        r.setdefault("precos_base", {})["potencia_dia"] = sum(base_dia)
    if consumos:
        r["consumo_total"] = sum(consumos.values())
    elif total_solto is not None:
        r["consumo_total"] = total_solto

    precos_diferentes = len({round(v, 6) for v in precos.values()}) > 1
    if len(consumos) > 1 and precos and not precos_diferentes:
        inferida = "simples"          # contador com períodos, mas o mesmo preço em todos
    elif {"ponta", "cheias"} & set(consumos):
        inferida = "tri"
    elif {"vazio", "fora_vazio"} & set(consumos):
        inferida = "bi"
    else:
        inferida = "simples"
    contradiz = (opcao_escrita in ("bi", "tri") and set(consumos) <= {"simples"} and consumos) \
        or (opcao_escrita == "simples" and precos_diferentes)
    if opcao_escrita and not contradiz:
        r["opcao"] = opcao_escrita
    elif consumos or opcao_escrita:
        r["opcao"] = inferida

    if precos:
        if not precos_diferentes:
            r["preco_energia"] = next(iter(precos.values()))
    elif preco_solto is not None:
        r["preco_energia"] = preco_solto
    # modalidade: indexado se a fatura o diz; fixo se há preço de energia e nenhum sinal de mercado
    if sinais_indexado and not sinais_fixo:
        r["modalidade"] = "indexado"
        evid["modalidade"] = sinais_indexado
    elif sinais_fixo or r["precos"] or "preco_energia" in r:
        r["modalidade"] = "fixo"
        evid["modalidade"] = sinais_fixo or ["preço por kWh sem referência ao mercado"]
    empresa = comercializador(texto)
    if empresa:
        r["comercializador"] = empresa
    r["evidencias"] = evid
    return r


def ler_ficheiro(nome, conteudo):
    """Extrai o texto de um PDF ou imagem e lê os valores."""
    if nome.lower().endswith(".pdf"):
        texto = texto_de_pdf(conteudo)
    else:
        texto = texto_de_imagem(conteudo)
    if not texto.strip():
        raise ValueError("Não consegui ler texto neste ficheiro. É uma digitalização? "
                         "Experimenta uma foto nítida ou preenche à mão.")
    return ler_fatura(texto)
