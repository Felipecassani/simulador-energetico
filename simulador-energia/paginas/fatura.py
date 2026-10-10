"""Ferramenta 1 — A minha fatura: escrever os números da fatura (ou carregá-la) e ver quanto se paga.

Dois passos numerados: 1. os números da fatura, 2. quanto pagas e as ofertas mais baratas.
Carregar a fatura ou os consumos da E-REDES é opcional e fica no fim da página; as partes
«Como pagar menos» e «O teu ano» estão em interface/fatura_extra.py.

O que a página mostra depende do tipo de preço:
- fixo: o preço por kWh do contrato, comparado com a tarifa regulada (também fixa);
- indexado: o preço médio desta fatura, as perdas e a margem do contrato, quanto custaria
  o mesmo consumo com o mercado de agora, e a comparação com um preço fixo.
Ao carregar uma fatura, os valores passam para todas as outras ferramentas.
"""
from datetime import date

import streamlit as st

from interface import componentes as ui
from interface import carregar_eredes, fatura_extra, marketing
from interface import perfil as pf
from interface.dados import erse, medias_omie, ofertas_erse
from nucleo import (calculos, historico, impostos, leitura_fatura, ofertas, periodos, recomendacoes,
                    relatorio, roteiro, tarifas)

passo = roteiro.passo(1)
disponivel = roteiro.disponivel(1)
ui.cabecalho_ferramenta(passo, disponivel)

MODALIDADES = {"fixo": "Preço fixo", "indexado": "Indexado ao mercado"}       # legendas e PDF
TIPO_DE_PRECO = {"fixo": "Fixo (igual todos os meses)", "indexado": "Indexado (muda com o mercado)"}
NO_PERIODO = {"vazio": "no vazio", "fora_vazio": "fora do vazio", "ponta": "na ponta", "cheias": "nas cheias"}

ONDE_ENCONTRAR = """
- **Fixo ou indexado**: nas condições do contrato. Se aparecer «indexado», «OMIE» ou «preço dinâmico», é indexado.
- **Dias da fatura**: no topo, no período de faturação. De 1 a 31 de agosto são 31 dias.
- **Eletricidade gasta**: junto às leituras do contador, por exemplo «Consumo 258 kWh».
- **Preço de cada kWh**: na linha «Energia», o número ao lado de «€/kWh», por exemplo 0,1652.
- **Potência contratada**: nos dados do contrato, por exemplo «6,9 kVA».
- **Preço da potência por dia**: na linha «Potência», o número ao lado de «€/dia», por exemplo 0,3659.
"""

AJUDA_IVA = ("Ligado: vês o total como vem na fatura, com IVA e as pequenas taxas de todas as faturas "
             "(como a da RTP). Desligado: vês só o preço da eletricidade, sem impostos — é assim que se "
             "comparam empresas, porque os impostos são iguais em todas.")


def _kva(k):
    """Potência como vem no papel: 6.9 → '6,9'; 3.45 → '3,45'."""
    return f"{float(k):g}".replace(".", ",")


def _valores_da_fatura(lido):
    """Converte o que foi lido da fatura nos campos do perfil."""
    valores = {}
    total = lido.get("consumo_total")
    if total:
        valores["consumo_kwh"] = float(total)
    if lido.get("dias"):
        valores["dias"] = int(lido["dias"])
    if lido.get("preco_diario"):
        valores["preco_diario"] = float(lido["preco_diario"])
    if lido.get("potencia_kva"):
        valores["kva"] = min(pf.ESCALOES_KVA, key=lambda k: abs(k - lido["potencia_kva"]))
    consumos, precos = lido.get("consumos", {}), lido.get("precos", {})
    if lido.get("preco_energia"):
        valores["preco_energia"] = float(lido["preco_energia"])
    elif consumos and total and set(consumos) <= set(precos):
        # bi/tri-horário (ou indexado por período): preço médio pago por kWh neste período
        valores["preco_energia"] = sum(consumos[p] * precos[p] for p in consumos) / total
    if total and "vazio" in consumos:
        valores["pct_vazio"] = round(100 * consumos["vazio"] / total, 1)
        valores["pct_ponta"] = round(100 * consumos.get("ponta", 0) / total, 1)
        valores["perfil_da_fatura"] = True
        valores["ponta_na_fatura"] = "ponta" in consumos     # bi-horário: ponta desconhecida
    for chave in ("comercializador", "opcao", "modalidade", "perdas_pct", "margem_kwh", "omie_medio_mwh",
                  "precos_base", "desconto_pct"):
        if lido.get(chave) is not None:
            valores[chave] = lido[chave]
    return valores


def _resumo(lido):
    """Lista curta (markdown) com o que foi lido, pela ordem em que se confere no papel."""
    linhas = []
    if lido.get("comercializador"):
        linhas.append(f"Empresa: {lido['comercializador']}")
    total, dias = lido.get("consumo_total"), lido.get("dias")
    if total:
        texto = f"Eletricidade gasta: {ui.numero(total)} kWh" + (f" em {dias} dias" if dias else "")
        consumos = lido.get("consumos", {})
        if len(consumos) > 1:
            texto += " (" + ", ".join(f"{ui.numero(v)} {NO_PERIODO.get(p, periodos.NOMES[p].lower())}"
                                       for p, v in consumos.items()) + ")"
        linhas.append(texto)
    elif dias:
        linhas.append(f"Dias da fatura: {dias}")
    if lido.get("preco_energia"):
        linhas.append(f"Preço de cada kWh: {ui.preco(lido['preco_energia'])} €")
    kva, por_dia = lido.get("potencia_kva"), lido.get("preco_diario")
    if kva or por_dia:
        partes = ([f"{_kva(kva)} kVA"] if kva else []) + ([f"a {ui.preco(por_dia)} € por dia"] if por_dia else [])
        linhas.append("Potência: " + ", ".join(partes))
    tipo = []
    if lido.get("modalidade") == "indexado":
        tipo.append("indexado ao mercado")
    elif lido.get("modalidade") == "fixo":
        desconto = lido.get("desconto_pct")
        tipo.append("preço fixo" + (f" com desconto de campanha de {round(desconto)} %" if desconto else ""))
    if lido.get("opcao"):
        tipo.append(periodos.NOMES[lido["opcao"]].lower())
    if tipo:
        linhas.append("Tipo: " + ", ".join(tipo))
    if lido.get("modalidade") == "indexado":
        extra = []
        if lido.get("perdas_pct") is not None:
            extra.append(f"perdas de {ui.numero(lido['perdas_pct'], 1)} %")
        if lido.get("margem_kwh") is not None:
            extra.append(f"margem de {ui.preco(lido['margem_kwh'])} € por kWh")
        if extra:
            linhas.append("No indexado: " + " e ".join(extra))
    return "\n".join(f"- {linha}" for linha in linhas)


# ---------- a fatura carregada: o botão para a carregar fica no fim da página (é opcional e não deve
# assustar quem só quer escrever os números), mas os ficheiros escolhidos leem-se já aqui — o Streamlit
# guarda-os em session_state — para os números aparecerem preenchidos lá em cima
com_fotos = leitura_fatura.ocr_disponivel()
ficheiros = st.session_state.get("f_faturas") or []
cache = st.session_state.setdefault("faturas_cache", {})
limite = 2 * historico.MAX_FATURAS                  # protege o servidor: lê no máximo 24 ficheiros
para_ler = ficheiros[:limite]
novos = [f for f in para_ler if (f.file_id, leitura_fatura.VERSAO) not in cache]
if novos:
    fotos = any(not f.name.lower().endswith(".pdf") for f in novos)
    with st.spinner(f"A ler {len(novos)} fatura{'s' if len(novos) > 1 else ''}…"
                    + (" As fotos podem demorar até meio minuto." if fotos else "")):
        for f in novos:
            try:
                lido = leitura_fatura.ler_ficheiro(f.name, f.getvalue())
                cache[(f.file_id, leitura_fatura.VERSAO)] = {k: v for k, v in lido.items() if k != "evidencias"}
            except Exception:  # ficheiro ilegível, digitalização sem texto, OCR indisponível, …
                cache[(f.file_id, leitura_fatura.VERSAO)] = None
pares = [(f, cache.get((f.file_id, leitura_fatura.VERSAO))) for f in para_ler]
falhadas = [f.name for f, l in pares if l is None]
vazias = [f.name for f, l in pares if l is not None and not l]       # lida, mas sem valores
com_valores = [(f, l) for f, l in pares if l]
st.session_state["faturas_lidas"] = [l for _, l in com_valores]
# a fatura principal (a mais recente) só é reaplicada quando ela muda: juntar outro ficheiro
# não apaga as correções feitas à mão; uma versão nova do leitor (VERSAO) volta a aplicá-la
if com_valores:
    f_principal, principal = max(com_valores, key=lambda par: (par[1].get("fim") is not None,
                                                                par[1].get("fim") or date.min))
    chave_principal = (f_principal.file_id, leitura_fatura.VERSAO)
else:
    principal, chave_principal = None, None
if chave_principal != st.session_state.get("fatura_principal"):
    st.session_state["fatura_principal"] = chave_principal
    st.session_state.pop("fatura_resumo", None)
    if principal is not None:
        valores = _valores_da_fatura(principal)
        if valores:
            pf.carregar_fatura(valores)       # passa para todas as ferramentas
        st.session_state["fatura_resumo"] = _resumo(principal) if valores else ""
unicas = len(historico.juntar(st.session_state["faturas_lidas"]))
if st.session_state.get("fatura_resumo"):
    prefixo = (f"Li {unicas} faturas. Estes números são da mais recente: confirma-os" if unicas > 1
               else "Li estes números da tua fatura: confirma-os")
    st.success(prefixo + " no papel e, se algum estiver errado, corrige-o em baixo.\n\n"
               + st.session_state["fatura_resumo"], icon=":material/task_alt:")

st.write("")
marketing.visita_guiada()
aba_fatura, aba_explorar, aba_ano = st.tabs([":material/receipt_long: A tua fatura",
                                             ":material/savings: Como pagar menos",
                                             ":material/calendar_month: O teu ano (várias faturas)"])

with aba_fatura:
    st.write("")
    entradas, resultado = st.columns([1, 1.3], gap="large")

    # ---------- 2) os números (à mão ou vindos da fatura), pela ordem em que aparecem no papel
    with entradas:
        st.subheader(":material/edit_note: 1. Os números da tua fatura")
        with st.expander("Onde encontro estes números na fatura?", icon=":material/help:"):
            ui.texto(ONDE_ENCONTRAR)
        p_inicial = pf.perfil()
        if not p_inicial.get("da_fatura"):
            ui.nota(f"Os números já preenchidos são um exemplo: uma casa que gasta "
                    f"{ui.numero(pf.PADRAO['consumo_kwh'])} kWh em {pf.PADRAO['dias']} dias, na tarifa regulada. "
                    "Troca-os pelos da tua fatura para veres a tua conta.", "Números de exemplo")
        elif p_inicial.get("precos_em_falta"):
            nomes = {"preco_energia": "o preço da energia", "preco_diario": "o preço da potência"}
            dois = len(p_inicial["precos_em_falta"]) > 1
            st.warning("Não consegui ler " + " nem ".join(nomes[k] for k in p_inicial["precos_em_falta"])
                       + " nesta fatura: pus um preço de referência, o da tarifa regulada. Procura "
                       + ("esses preços" if dois else "esse preço") + " na tua fatura em papel e corrige "
                       + ("os campos" if dois else "o campo") + " em baixo.", icon=":material/edit:")
        modalidade = pf.campo(st.radio, "O preço de cada kWh é fixo ou muda todos os meses?", "modalidade",
                              "f_modalidade", options=list(MODALIDADES), format_func=TIPO_DE_PRECO.get,
                              horizontal=True,
                              help="Vê no contrato ou na fatura. Se aparecer «indexado», «OMIE» ou «preço "
                                   "dinâmico», escolhe Indexado. Na dúvida, deixa Fixo: é o mais comum.")
        indexado = modalidade == "indexado"
        pf.campo(st.number_input, "Dias da fatura", "dias", "f_dias", min_value=1, step=1,
                 help="Conta os dias do período de faturação, no topo da fatura. Por exemplo, de 1 a 31 "
                      "de agosto são 31 dias.")
        pf.campo(st.number_input, "Eletricidade gasta (kWh)", "consumo_kwh", "f_consumo",
                 min_value=0.0, step=10.0,
                 help="Está junto às leituras do contador, por exemplo «Consumo: 258 kWh». O kWh é a "
                      "medida da eletricidade gasta: um aquecedor de 1000 W ligado 1 hora gasta 1 kWh. "
                      "Se a fatura tem dois ou três consumos (por exemplo «vazio», as horas baratas da "
                      "noite, e «fora de vazio»), soma-os todos.")
        pf.campo(st.number_input,
                 "Preço médio de cada kWh nesta fatura (€)" if indexado else "Preço de cada kWh (€)",
                 "preco_energia", "f_preco_energia", min_value=0.0, step=0.001, format="%.4f",
                 help=("Num indexado o preço muda todos os meses. Divide o total da energia desta fatura "
                       "pelos kWh gastos: 42,60 € ÷ 258 kWh = 0,1651." if indexado else
                       "Na linha «Energia» da fatura, é o número ao lado de «€/kWh», por exemplo 0,1652. "
                       "Se tens dois ou três preços (bi ou tri-horário), divide o total da energia pelos "
                       "kWh gastos: 42,60 € ÷ 258 kWh = 0,1651."))
        pf.campo(st.selectbox, "Potência contratada (kVA)", "kva", "f_kva",
                 options=pf.ESCALOES_KVA, format_func=lambda k: f"{_kva(k)} kVA",
                 help="Diz quantos aparelhos podes ter ligados ao mesmo tempo sem o quadro disparar. Vem "
                      "nos dados do contrato, no topo da fatura, por exemplo «6,9 kVA». Nas casas, o mais "
                      "comum é 3,45, 4,6 ou 6,9.")
        pf.campo(st.number_input, "Preço da potência, por dia (€)", "preco_diario", "f_preco_diario",
                 min_value=0.0, step=0.001, format="%.4f",
                 help="É o valor fixo que pagas por cada dia só por teres a luz ligada, mesmo sem gastar. "
                      "Na linha «Potência» da fatura, é o número ao lado de «€/dia», por exemplo 0,3659. "
                      "Se houver duas linhas de potência (uma delas «acesso às redes»), soma as duas.")
        if indexado:
            ui.nota("Só para tarifários indexados. Se não encontrares estes valores, deixa 0: a conta "
                       "fica um pouco abaixo do real.")
            i1, i2 = st.columns(2)
            with i1:
                pf.campo(st.number_input, "Perdas na rede (%)", "perdas_pct", "f_perdas", min_value=0.0,
                         max_value=50.0, step=0.5,
                         help="A energia que se perde no caminho até tua casa, que a empresa cobra à parte. "
                              "Aparece como «perdas» ou «fator de perdas». Se vires 1,15, escreve 15.")
            with i2:
                pf.campo(st.number_input, "Margem da empresa (€ por kWh)", "margem_kwh", "f_margem",
                         min_value=0.0, step=0.001, format="%.4f",
                         help="O que a empresa soma ao preço do mercado em cada kWh. Pode chamar-se "
                              "«margem», «fee» ou «spread», por exemplo 0,0100.")

        fatura_extra.estimar_aparelhos()

    # ---------- 3) quanto pagas
    p = pf.perfil()
    tarifa = erse()
    medias, _ = medias_omie(7)
    com_perfil = p.get("perfil_da_fatura", False)
    pct_vazio = p["pct_vazio"] if com_perfil else 0.0
    pct_ponta = p["pct_ponta"] if com_perfil else 0.0
    # com uma fatura bi-horária não se sabe quanto cai em ponta: o tri-horário não se pode comparar
    sem_tri = com_perfil and not p.get("ponta_na_fatura", True)

    with resultado:
        st.subheader(":material/payments: 2. Quanto pagas")
        pf.campo(st.toggle, "Incluir IVA e taxas", "com_impostos",
                 "f_impostos", padrao=False, help=AJUDA_IVA)
        if p.get("com_impostos"):
            pf.campo(st.checkbox, "Sou família numerosa", "familia_numerosa", "f_familia", padrao=False,
                     help="Nas famílias numerosas, os primeiros 300 kWh de cada mês pagam IVA a 6 % (nas "
                          "outras casas são 200 kWh). Marca só se tens este benefício.")
        vazio = [ui.metrica("Pela eletricidade gasta", "—", "€", vazio=True),
                 ui.metrica("Pela potência (parte fixa)", "—", "€", vazio=True),
                 ui.metrica("Total sem IVA", "—", "€", vazio=True)]
        f = None
        if not disponivel:
            ui.grelha(vazio, largura_min=140)
            st.info("Esta ferramenta ainda não está disponível.", icon=":material/construction:")
        else:
            try:
                f = calculos.fatura_simplificada(p["consumo_kwh"], p["preco_energia"],
                                                 p["preco_diario"], p["dias"])
            except ValueError:
                ui.grelha(vazio, largura_min=140)
                st.error("Os números não podem ser negativos. Corrige-os no passo 1.", icon=":material/error:")
        if f is not None:
            ci = impostos.com_impostos(f["energia"], f["potencia"], p["consumo_kwh"], p["dias"],
                                       p["kva"], p.get("familia_numerosa", False))
            ui.grelha([ui.metrica("Pela eletricidade gasta", ui.euros(f["energia"]), "€"),
                       ui.metrica("Pela potência (parte fixa)", ui.euros(f["potencia"]), "€"),
                       ui.metrica("Total sem IVA", ui.euros(f["total"]), "€", destaque=not p.get("com_impostos"))],
                      largura_min=140)
            if not p.get("com_impostos"):
                ui.texto(f"Com IVA e taxas: cerca de **{ui.euros(ci['total'])} €**, o valor a comparar com a fatura.")
            ui.nota(f"Em {p['dias']} dias: {ui.euros(f['energia'])} € pela eletricidade que gastaste e "
                       f"{ui.euros(f['potencia'])} € pela potência (a parte fixa, que pagas mesmo sem gastar). "
                       f"De onde vêm os preços: {p['fonte']}.")
            ui.para_onde_vai(f["energia"], f["potencia"], ci["taxas"] + ci["iva"])
            if p.get("com_impostos"):
                ui.grelha([ui.metrica("Taxas", ui.euros(ci["taxas"]), "€"),
                           ui.metrica("IVA", ui.euros(ci["iva"]), "€"),
                           ui.metrica("Total com IVA", ui.euros(ci["total"]), "€", destaque=True)],
                          largura_min=140)
                ui.nota("O total com IVA junta a eletricidade, o IVA e as pequenas taxas que vêm em todas as "
                           "faturas, como a da rádio e televisão públicas (2,85 € por mês). Deve ficar perto "
                           "do total da tua fatura.")

            # indexado: o mesmo consumo com o mercado de agora (perdas e margem do contrato)
            if indexado:
                st.write("")
                ui.texto("**Com o mercado de agora**: quanto pagarias pelo mesmo consumo com os preços "
                            "desta semana e as condições do teu contrato.")
                if medias is None:
                    st.info("Não consegui ver os preços do mercado agora. Tenta outra vez daqui a uns minutos.",
                            icon=":material/wifi_off:")
                else:
                    opcao = p.get("opcao", "simples") if com_perfil else "simples"
                    agora = next(l for l in tarifas.comparar_opcoes(
                        p["consumo_kwh"], pct_vazio, pct_ponta, p["dias"], p["kva"], tarifa,
                        medias_omie=medias, perdas_pct=p.get("perdas_pct") or 0.0,
                        margem_eur_kwh=p.get("margem_kwh") or 0.0)
                        if l["modalidade"] == "indexado" and l["opcao"] == opcao)
                    # com a potência do teu contrato, para comparar com esta fatura
                    agora_total = agora["energia"] + p["preco_diario"] * p["dias"]
                    variacao = agora_total - f["total"]
                    if variacao > 0.005:
                        rotulo, frase = "Mais do que nesta fatura", (
                            f"Com os preços desta semana, pagarias mais {ui.euros(variacao)} € do que nesta fatura.")
                    elif variacao < -0.005:
                        rotulo, frase = "Menos do que nesta fatura", (
                            f"Com os preços desta semana, pagarias menos {ui.euros(-variacao)} € do que nesta fatura.")
                    else:
                        rotulo, frase = "Diferença", "Com os preços desta semana, pagarias o mesmo que nesta fatura."
                    if p.get("com_impostos"):
                        ui.nota("Atenção: estas comparações são sem IVA. Compara-as com o «Total sem IVA» "
                                   "lá em cima, não com o total com IVA.")
                    ui.grelha([
                        ui.metrica("Com o mercado de agora" + (", sem IVA" if p.get("com_impostos") else ""),
                                   ui.euros(agora_total), "€"),
                        ui.metrica(rotulo, ui.euros(abs(variacao)), "€", destaque=variacao < -0.005),
                    ], largura_min=140)
                    ui.texto(frase)
                    ui.nota("É uma estimativa com os preços do mercado dos últimos 7 dias e as condições do "
                               "teu contrato, sem IVA. O mercado muda todos os dias, por isso a próxima fatura "
                               "pode ser diferente.")

            # comparação automática com a tarifa regulada (preço fixo)
            reguladas = [l for l in tarifas.comparar_opcoes(
                p["consumo_kwh"], pct_vazio, pct_ponta, p["dias"], p["kva"], tarifa)
                if (com_perfil or l["opcao"] == "simples") and not (sem_tri and l["opcao"] == "tri")]
            regulada = reguladas[0]
            diferenca = f["total"] - regulada["total"]
            st.write("")
            opcao_reg = ("o mesmo preço a qualquer hora" if regulada["opcao"] == "simples"
                         else periodos.NOMES[regulada["opcao"]].lower())
            ui.texto(f"**Na tarifa regulada da ERSE**, o preço oficial de referência, para "
                        f"{_kva(p['kva'])} kVA e {opcao_reg}:")
            if diferenca > 0.005:
                rotulo = "Poupança se mudares"
                frase = (f"Se mudasses para a tarifa regulada, pagarias menos {ui.euros(diferenca)} € "
                         f"nestes {p['dias']} dias.")
            elif diferenca < -0.005:
                rotulo = "A mais se mudares"
                frase = (f"O teu preço é melhor: na tarifa regulada pagarias mais {ui.euros(-diferenca)} € "
                         f"nestes {p['dias']} dias.")
            else:
                rotulo, frase = "Diferença", "Pagas praticamente o mesmo que na tarifa regulada."
            if p.get("com_impostos"):
                ui.nota("Atenção: estas comparações são sem IVA. Compara-as com o «Total sem IVA» "
                           "lá em cima, não com o total com IVA.")
            ui.grelha([
                ui.metrica("Na tarifa regulada pagarias" + (", sem IVA" if p.get("com_impostos") else ""),
                           ui.euros(regulada["total"]), "€"),
                ui.metrica(rotulo, ui.euros(abs(diferenca)), "€", destaque=diferenca > 0.005),
            ], largura_min=140)
            ui.texto(frase)
            ui.nota(f"A tarifa regulada é um preço fixo que a ERSE, a entidade que regula a eletricidade, "
                       f"define para cada ano (aqui, {tarifa['ano']}). Serve de termo de comparação e podes "
                       "aderir a ela. Valores sem IVA.")

    # ---------- 4) recomendações (fatura + ERSE + OMIE)
    if f is not None:
        st.write("")
        if p.get("da_fatura"):
            ui.cartao_meu_tarifario(p, f["total"] * 30 / p["dias"], na_fatura=True)
        st.subheader(":material/recommend: Recomendações para ti")
        ui.nota("Ideias para pagares menos, da que poupa mais para a que poupa menos. Valores por mês, sem IVA.")
        dados_fatura = {
            "consumo_kwh": p["consumo_kwh"], "preco_energia": p["preco_energia"],
            "preco_diario": p["preco_diario"], "dias": p["dias"], "kva": p["kva"],
            "opcao": p.get("opcao", "simples"), "modalidade": modalidade,
            "perdas_pct": p.get("perdas_pct"), "margem_kwh": p.get("margem_kwh"),
            "pct_vazio": p["pct_vazio"] if com_perfil else None,
            "pct_ponta": p["pct_ponta"] if com_perfil and not sem_tri else None,
            "precos_base": p.get("precos_base"), "desconto_pct": p.get("desconto_pct"),
        }
        lista_recs = recomendacoes.recomendar(dados_fatura, tarifa, medias)
        ui.grelha([ui.cartao_recomendacao(r) for r in lista_recs], largura_min=420)

        # ---------- 5) as ofertas mais baratas (dados oficiais da ERSE)
        lista, data_ofertas = ofertas_erse()
        top = []
        if lista:
            top = ofertas.mais_baratas(lista, p["consumo_kwh"], p["dias"], p["kva"],
                                       dados_fatura["pct_vazio"], dados_fatura["pct_ponta"])
            st.write("")
            st.subheader(":material/emoji_events: As ofertas mais baratas para ti")
            if top:
                vista = st.segmented_control(
                    "Mostrar o custo", ["Por mês", "No 1.º ano"], default="Por mês", key="f_vista_ofertas",
                    help="«No 1.º ano» soma 12 meses e conta com o fim dos descontos de campanha da tua "
                         "fatura.") or "Por mês"
                com_iva = p.get("com_impostos", False)

                def mensal(energia, potencia):
                    """€ por mês (30 dias), com ou sem IVA e taxas."""
                    valor = energia + potencia
                    if com_iva:
                        valor = impostos.com_impostos(energia, potencia, p["consumo_kwh"], p["dias"],
                                                      p["kva"], p.get("familia_numerosa", False))["total"]
                    return valor * 30 / p["dias"]

                atual_mes = mensal(f["energia"], f["potencia"])
                linhas = []
                for o, custo in top:
                    pot = o.potencia_dia * p["dias"]
                    linhas.append((o, mensal(custo - pot, pot)))
                if vista == "No 1.º ano":
                    base = p.get("precos_base") or {}
                    atual = atual_mes * 12
                    if base.get("energia") and base.get("potencia_dia"):
                        meses = pf.campo(st.number_input, "Quantos meses faltam para acabar o desconto?",
                                         "meses_campanha", "f_meses_campanha", padrao=12, min_value=0,
                                         max_value=12, step=1,
                                         help="Vê na fatura ou no contrato até quando dura a campanha. Depois "
                                              "desses meses, a conta usa o preço sem desconto. Se não "
                                              "souberes, deixa 12.")
                        sem = mensal(p["consumo_kwh"] * base["energia"], base["potencia_dia"] * p["dias"])
                        atual = atual_mes * meses + sem * (12 - meses)
                    ui.podio_ofertas([(o, v * 12) for o, v in linhas], atual, "no 1.º ano",
                                     p.get("comercializador"), com_fatura=bool(p.get("da_fatura")))
                else:
                    ui.podio_ofertas(linhas, atual_mes, "por mês", p.get("comercializador"),
                                     com_fatura=bool(p.get("da_fatura")))
                if linhas:
                    marketing.partilhar((atual_mes - linhas[0][1]) * 365 / 30, "fatura", atual_mes, linhas[0][1])
                ui.nota(
                    f"Para cada empresa, a oferta mais barata para o teu consumo e potência. São ofertas de "
                    f"preço fixo, só de eletricidade, publicadas pela ERSE a {data_ofertas:%d/%m/%Y}. "
                    + ("Com IVA e taxas. " if p.get("com_impostos") else "Sem IVA nem taxas. ")
                    + "Antes de mudar, confirma as condições no site da empresa.")
            else:
                st.info("Não há ofertas de preço fixo publicadas para esta potência.")

        # ---------- 6) guardar o resultado em PDF
        st.write("")
        resumo_pdf = relatorio.gerar(
            {"empresa": p.get("comercializador") or "O meu contrato", "tipo": MODALIDADES[modalidade],
             "opcao": periodos.NOMES[p.get("opcao", "simples")], "kva": p["kva"],
             "consumo_kwh": p["consumo_kwh"], "dias": p["dias"], "preco_energia": p["preco_energia"],
             "preco_diario": p["preco_diario"]},
            {**f, **({"total_com_iva": impostos.com_impostos(
                f["energia"], f["potencia"], p["consumo_kwh"], p["dias"], p["kva"],
                p.get("familia_numerosa", False))["total"]} if p.get("com_impostos") else {})},
            {"opcao": periodos.NOMES[regulada["opcao"]].lower(), "total": regulada["total"]},
            lista_recs,
            [(o.comercializador, o.nome, periodos.NOMES[o.opcao], c * 30 / p["dias"]) for o, c in top],
            data_ofertas)
        st.download_button("Guardar este resumo em PDF", resumo_pdf, file_name="simulacao-eletricidade.pdf",
                           mime="application/pdf", icon=":material/download:", key="f_pdf")
        ui.nota("Para imprimir ou mostrar a alguém. O PDF tem só os números e as recomendações: nada de "
                   "nomes, moradas ou o ficheiro da fatura.")


# ---------- as outras duas partes (código em interface/fatura_extra.py)
contexto = fatura_extra.Contexto(p=p, f=f, tarifa=tarifa, medias=medias, com_perfil=com_perfil, sem_tri=sem_tri,
                                 lidas=st.session_state.get("faturas_lidas", []))
with aba_explorar:
    fatura_extra.explorar(contexto)
with aba_ano:
    fatura_extra.o_teu_ano(contexto)

# ---------- carregar a fatura e os consumos da E-REDES: opcional, por isso no fim
st.write("")
st.subheader(":material/upload_file: Carregar a fatura (opcional)")
with st.container(border=True):
    ui.texto("**Tens a fatura em PDF" + (" ou foto" if com_fotos else "") + "?** Carrega-a aqui e os números "
             "lá de cima preenchem-se sozinhos.")
    st.file_uploader(
        "Escolhe o ficheiro da tua fatura",
        type=["pdf", "png", "jpg", "jpeg"] if com_fotos else ["pdf"],
        accept_multiple_files=True, key="f_faturas",
        help=("Carrega no botão «Escolher ficheiro» e escolhe o PDF da fatura. No telemóvel também podes "
              "tirar uma foto à fatura em papel: em cima de uma mesa, com boa luz e com a página inteira."
              if com_fotos else
              "Carrega no botão «Escolher ficheiro» e escolhe o PDF da fatura, que recebes por email ou "
              "na área de cliente da tua empresa de eletricidade."))
    ui.nota(f"Podes escolher várias de uma vez, até {historico.MAX_FATURAS}, para veres o teu ano na parte "
            "«O teu ano». Depois confirma os números com a tua fatura em papel: cada empresa escreve as "
            "faturas à sua maneira.")
    for nome in falhadas:
        st.warning(f"Não consegui ler {ui.nome_ficheiro(nome)}. Experimenta o PDF original ou uma foto nítida, "
                   "ou escreve os números à mão no passo 1, lá em cima.", icon=":material/error:")
    for nome in vazias:
        st.warning(f"Não encontrei números em {ui.nome_ficheiro(nome)}. Escreve-os à mão no passo 1, "
                   "lá em cima.", icon=":material/help:")
    if len(ficheiros) > limite or len(com_valores) > unicas:
        repetidas = len(com_valores) - unicas
        st.info(f"Carregaste {len(ficheiros)} ficheiros: "
                + (f"{repetidas} eram repetidos ou de há mais de um ano; " if repetidas > 0 else "")
                + f"conto {unicas} faturas diferentes.", icon=":material/info:")
carregar_eredes.secao("f")
