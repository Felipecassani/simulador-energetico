"""Ferramenta 1 — Fatura: carregar a fatura (fixa ou indexada) ou preencher à mão.

O que a página mostra depende do tipo de preço:
- fixo: o preço por kWh do contrato, comparado com a tarifa regulada (também fixa);
- indexado: o preço médio desta fatura, as perdas e a margem do contrato, quanto custaria
  o mesmo consumo com o mercado de agora, e a comparação com um preço fixo.
Ao carregar uma fatura, os valores passam para todas as outras ferramentas.
"""
import streamlit as st

from interface import componentes as ui
from interface import carregar_eredes
from interface import perfil as pf
from interface.dados import erse, medias_omie, ofertas_erse
from nucleo import (calculos, impostos, leitura_fatura, ofertas, periodos, recomendacoes, relatorio,
                    roteiro, tarifas)

passo = roteiro.passo(1)
disponivel = roteiro.disponivel(1)
ui.cabecalho_ferramenta(passo, disponivel)

MODALIDADES = {"fixo": "Preço fixo", "indexado": "Indexado ao mercado"}


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
    """Frase curta com o que foi lido, para comparar com a fatura."""
    partes = [lido["comercializador"]] if lido.get("comercializador") else []
    if lido.get("consumo_total"):
        texto = f"{ui.numero(lido['consumo_total'])} kWh"
        if len(lido.get("consumos", {})) > 1:
            texto += " (" + " · ".join(f"{periodos.NOMES[p].lower()} {ui.numero(v)}"
                                        for p, v in lido["consumos"].items()) + ")"
        partes.append(texto)
    if lido.get("preco_energia"):
        partes.append(f"{ui.preco(lido['preco_energia'])} €/kWh")
    if lido.get("preco_diario"):
        partes.append(f"potência {ui.preco(lido['preco_diario'])} €/dia")
    if lido.get("dias"):
        partes.append(f"{lido['dias']} dias")
    if lido.get("potencia_kva"):
        partes.append(f"{ui.numero(lido['potencia_kva'], 2)} kVA")
    if lido.get("opcao"):
        partes.append(periodos.NOMES[lido["opcao"]].lower())
    if lido.get("modalidade") == "indexado":
        extra = []
        if lido.get("perdas_pct") is not None:
            extra.append(f"perdas {ui.numero(lido['perdas_pct'], 1)} %")
        if lido.get("margem_kwh") is not None:
            extra.append(f"margem {ui.preco(lido['margem_kwh'])} €/kWh")
        partes.append("indexado ao mercado" + (f" ({', '.join(extra)})" if extra else ""))
    elif lido.get("modalidade") == "fixo":
        desconto = lido.get("desconto_pct")
        partes.append("preço fixo" + (f" com campanha de {round(desconto)} %" if desconto else ""))
    return " · ".join(partes)


# ---------- 1) carregar a fatura
with st.container(border=True):
    com_fotos = leitura_fatura.ocr_disponivel()
    st.markdown("**Carregar a fatura** · " + ("PDF ou foto" if com_fotos else "PDF"))
    st.caption("A fatura é lida neste computador e não fica guardada. Os valores passam para todas "
               "as ferramentas. Confirma-os em baixo: cada comercializador escreve as faturas à sua maneira.")
    ficheiro = st.file_uploader("Fatura (PDF, PNG ou JPG)" if com_fotos else "Fatura (PDF)",
                                type=["pdf", "png", "jpg", "jpeg"] if com_fotos else ["pdf"],
                                label_visibility="collapsed")
    chave_leitura = None if ficheiro is None else (ficheiro.file_id, leitura_fatura.VERSAO)
    if ficheiro is not None and st.session_state.get("fatura_lida") != chave_leitura:
        aviso = ("A ler a fatura…" if ficheiro.name.lower().endswith(".pdf")
                 else "A ler a foto… a primeira vez pode demorar até meio minuto.")
        with st.spinner(aviso):
            try:
                lido = leitura_fatura.ler_ficheiro(ficheiro.name, ficheiro.getvalue())
            except Exception:  # ficheiro ilegível, digitalização sem texto, OCR indisponível, …
                lido = None
                st.session_state["fatura_erro"] = ("Não consegui ler este ficheiro. Experimenta o PDF "
                                                   "original ou uma foto nítida, ou preenche à mão.")
            else:
                st.session_state.pop("fatura_erro", None)
        st.session_state["fatura_lida"] = chave_leitura
        if lido is not None:
            valores = _valores_da_fatura(lido)
            if valores:
                pf.carregar_fatura(valores)       # passa para todas as ferramentas
            st.session_state["fatura_resumo"] = _resumo(lido) if valores else ""
    if ficheiro is None:
        st.session_state.pop("fatura_lida", None)
    elif st.session_state.get("fatura_erro"):
        st.warning(st.session_state["fatura_erro"], icon=":material/error:")
    elif st.session_state.get("fatura_resumo"):
        st.success("Li da fatura: " + st.session_state["fatura_resumo"]
                   + ". Compara com a tua fatura e corrige em baixo se for preciso.",
                   icon=":material/task_alt:")
    elif "fatura_resumo" in st.session_state:
        st.warning("Não encontrei valores nesta fatura. Preenche à mão em baixo.", icon=":material/help:")

carregar_eredes.secao("f")

st.write("")
entradas, resultado = st.columns([1, 1.3], gap="large")

# ---------- 2) os dados (à mão ou vindos da fatura)
with entradas:
    st.subheader("Os teus dados")
    modalidade = pf.campo(st.radio, "Tipo de preço", "modalidade", "f_modalidade",
                          options=list(MODALIDADES), format_func=MODALIDADES.get, horizontal=True,
                          help="Fixo: o preço por kWh não muda com o mercado. Indexado: o preço "
                               "segue o mercado (OMIE) e muda todos os meses.")
    indexado = modalidade == "indexado"
    pf.campo(st.number_input, "Consumo (kWh)", "consumo_kwh", "f_consumo",
             min_value=0.0, step=10.0,
             help="A energia gasta no período, em kWh. Costuma aparecer no resumo da fatura, "
                  "junto às leituras do contador.")
    pf.campo(st.number_input,
             "Preço médio da energia nesta fatura (€/kWh)" if indexado else "Preço da energia (€/kWh)",
             "preco_energia", "f_preco_energia", min_value=0.0, step=0.001, format="%.4f",
             help=("Num indexado o preço muda com o mercado: este é o preço médio que pagaste neste "
                   "período (custo da energia ÷ kWh)." if indexado else
                   "Quanto pagas por cada kWh, no detalhe da fatura ou nas condições do contrato. "
                   "Em bi ou tri-horário, usa o preço médio (custo da energia ÷ kWh)."))
    pf.campo(st.number_input, "Preço da potência (€/dia)", "preco_diario", "f_preco_diario",
             min_value=0.0, step=0.001, format="%.4f",
             help="Valor fixo por dia da potência contratada, na linha da potência da fatura "
                  "(soma as linhas se o acesso às redes vier à parte).")
    if indexado:
        i1, i2 = st.columns(2)
        with i1:
            pf.campo(st.number_input, "Perdas (%)", "perdas_pct", "f_perdas", min_value=0.0,
                     max_value=50.0, step=0.5,
                     help="O fator de perdas do teu contrato indexado (1,15 = 15 %). Está na fatura "
                          "ou nas condições do contrato.")
        with i2:
            pf.campo(st.number_input, "Margem (€/kWh)", "margem_kwh", "f_margem", min_value=0.0,
                     step=0.001, format="%.4f",
                     help="O valor que o comercializador soma ao preço do mercado (fee, spread).")
    pf.campo(st.number_input, "Dias do período", "dias", "f_dias", min_value=1, step=1,
             help="Número de dias entre o início e o fim do período faturado.")
    pf.campo(st.selectbox, "Potência contratada", "kva", "f_kva",
             options=pf.ESCALOES_KVA, format_func=lambda k: f"{ui.numero(k, 2)} kVA",
             help="Está nos dados do contrato. Define o preço da potência na tarifa regulada.")
    pf.campo(st.toggle, "Mostrar com IVA e taxas", "com_impostos", "f_impostos", padrao=False,
             help="Junta o IVA, a contribuição audiovisual, a taxa da DGEG, o imposto especial de "
                  "consumo e o encargo da tarifa social: o total passa a bater com o da fatura.")
    if pf.perfil().get("com_impostos"):
        pf.campo(st.checkbox, "Família numerosa (300 kWh com IVA reduzido)", "familia_numerosa",
                 "f_familia", padrao=False)
    if not pf.perfil().get("da_fatura"):
        st.caption("Sem fatura, os preços começam nos da tarifa regulada da ERSE: troca-os pelos "
                   "do teu contrato. A comparação com a ERSE aparece sempre no resultado.")

# ---------- 3) resultado
p = pf.perfil()
if p.get("precos_em_falta") and p.get("da_fatura"):
    nomes = {"preco_energia": "o preço da energia", "preco_diario": "o preço da potência"}
    with entradas:
        st.warning("Não consegui ler " + " nem ".join(nomes[k] for k in p["precos_em_falta"])
                   + " nesta fatura: pus o da tarifa regulada. Confirma-o na tua fatura e corrige em cima.",
                   icon=":material/edit:")
tarifa = erse()
medias, _ = medias_omie(7)
com_perfil = p.get("perfil_da_fatura", False)
pct_vazio = p["pct_vazio"] if com_perfil else 0.0
pct_ponta = p["pct_ponta"] if com_perfil else 0.0
# com uma fatura bi-horária não se sabe quanto cai em ponta: o tri-horário não se pode comparar
sem_tri = com_perfil and not p.get("ponta_na_fatura", True)

with resultado:
    st.subheader("Resultado")
    vazio = [ui.metrica("Energia", "—", "€", vazio=True),
             ui.metrica("Potência", "—", "€", vazio=True),
             ui.metrica("Total", "—", "€", vazio=True)]
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
            st.error("Os valores não podem ser negativos.", icon=":material/error:")
    if f is not None:
        ui.grelha([ui.metrica("Energia", ui.euros(f["energia"]), "€"),
                   ui.metrica("Potência", ui.euros(f["potencia"]), "€"),
                   ui.metrica("Total", ui.euros(f["total"]), "€", destaque=True)],
                  largura_min=140)
        st.caption(f"{p['dias']} dias · {MODALIDADES[modalidade].lower()} · valores sem IVA nem "
                   f"taxas · preços: {p['fonte']}.")
        if p.get("com_impostos"):
            ci = impostos.com_impostos(f["energia"], f["potencia"], p["consumo_kwh"], p["dias"],
                                       p["kva"], p.get("familia_numerosa", False))
            ui.grelha([ui.metrica("Taxas e encargos", ui.euros(ci["taxas"]), "€"),
                       ui.metrica("IVA", ui.euros(ci["iva"]), "€"),
                       ui.metrica("Total com IVA", ui.euros(ci["total"]), "€", destaque=True)],
                      largura_min=140)
            st.caption("Com IVA, contribuição audiovisual, taxa da DGEG, imposto especial de consumo "
                       "e encargo da tarifa social (valores de 2026).")

        # indexado: o mesmo consumo com o mercado de agora (perdas e margem do contrato)
        if indexado:
            st.write("")
            opcao = p.get("opcao", "simples") if com_perfil else "simples"
            st.markdown(f"**Com o mercado de agora** · {periodos.NOMES[opcao].lower()}, "
                        "com as tuas perdas e margem")
            if medias is None:
                st.info("Sem ligação ao mercado (OMIE) agora: volta a tentar daqui a pouco.",
                        icon=":material/wifi_off:")
            else:
                agora = next(l for l in tarifas.comparar_opcoes(
                    p["consumo_kwh"], pct_vazio, pct_ponta, p["dias"], p["kva"], tarifa,
                    medias_omie=medias, perdas_pct=p.get("perdas_pct") or 0.0,
                    margem_eur_kwh=p.get("margem_kwh") or 0.0)
                    if l["modalidade"] == "indexado" and l["opcao"] == opcao)
                # com a potência do teu contrato, para comparar com esta fatura
                agora_total = agora["energia"] + p["preco_diario"] * p["dias"]
                variacao = agora_total - f["total"]
                ui.grelha([
                    ui.metrica("Com o mercado de agora", ui.euros(agora_total), "€"),
                    ui.metrica("Face a esta fatura", ("+" if variacao > 0 else "−")
                               + ui.euros(abs(variacao)), "€", destaque=variacao < 0),
                ], largura_min=140)
                st.caption("Mesmo consumo, com a média do mercado dos últimos 7 dias em cada período, "
                           "as tarifas de acesso da ERSE e as tuas perdas e margem. É uma estimativa: "
                           "o mercado muda todos os dias.")

        # comparação automática com a tarifa regulada (preço fixo)
        reguladas = [l for l in tarifas.comparar_opcoes(
            p["consumo_kwh"], pct_vazio, pct_ponta, p["dias"], p["kva"], tarifa)
            if (com_perfil or l["opcao"] == "simples") and not (sem_tri and l["opcao"] == "tri")]
        regulada = reguladas[0]
        diferenca = f["total"] - regulada["total"]
        st.write("")
        st.markdown(f"**Na tarifa regulada da ERSE (preço fixo)** · "
                    f"{periodos.NOMES[regulada['opcao']].lower()}, {ui.numero(p['kva'], 2)} kVA")
        ui.grelha([
            ui.metrica("Tarifa regulada", ui.euros(regulada["total"]), "€"),
            ui.metrica("Mudar para a regulada" if abs(diferenca) >= 0.005 else "Igual",
                       ("+" if diferenca < 0 else "−" if diferenca > 0 else "")
                       + ui.euros(abs(diferenca)), "€", destaque=diferenca > 0.005),
        ], largura_min=140)
        if diferenca > 0.005:
            st.caption(f"Na tarifa regulada pagarias menos {ui.euros(diferenca)} € neste período.")
        elif diferenca < -0.005:
            st.caption(f"O teu preço está {ui.euros(-diferenca)} € abaixo da tarifa regulada neste período.")
        st.caption(f"Tarifa regulada ERSE {tarifa['ano']}: preços fixos definidos pela ERSE para o ano, "
                   "não seguem o mercado.")

# ---------- 4) recomendações (fatura + ERSE + OMIE)
if f is not None:
    st.write("")
    if p.get("da_fatura"):
        ui.cartao_meu_tarifario(p, f["total"] * 30 / p["dias"])
    st.subheader("Recomendações para ti")
    st.caption("Com base na tua fatura, nas tarifas da ERSE e no mercado OMIE dos últimos 7 dias. "
               "Valores por mês (30 dias), sem IVA nem taxas.")
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
        st.subheader("As ofertas mais baratas para ti")
        if top:
            vista = st.segmented_control("Ver", ["Por mês", "No 1.º ano"], default="Por mês",
                                         key="f_vista_ofertas", label_visibility="collapsed") or "Por mês"
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
                    meses = pf.campo(st.number_input, "Meses que faltam da campanha", "meses_campanha",
                                     "f_meses_campanha", padrao=12, min_value=0, max_value=12, step=1,
                                     help="Vê na fatura ou no contrato até quando dura o desconto. "
                                          "Depois, conta o preço sem desconto.")
                    sem = mensal(p["consumo_kwh"] * base["energia"], base["potencia_dia"] * p["dias"])
                    atual = atual_mes * meses + sem * (12 - meses)
                ui.podio_ofertas([(o, v * 12) for o, v in linhas], atual, "no 1.º ano",
                                 p.get("comercializador"))
            else:
                ui.podio_ofertas(linhas, atual_mes, "por mês", p.get("comercializador"))
            st.caption(
                f"A melhor oferta de cada empresa para o teu consumo e potência, com as ofertas de preço "
                f"fixo publicadas pela ERSE (atualizadas a {data_ofertas:%d/%m/%Y}). Só eletricidade, "
                "para qualquer casa: ficam de fora as ofertas duais, indexadas ou só para sócios. "
                + ("Com IVA e taxas. " if p.get("com_impostos") else "Sem IVA nem taxas. ")
                + "Confirma sempre as condições na ficha da oferta.")
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
    st.download_button("Guardar o resultado em PDF", resumo_pdf, file_name="simulacao-eletricidade.pdf",
                       mime="application/pdf", icon=":material/download:", key="f_pdf")
    st.caption("O PDF tem só os números e as recomendações: nada de nomes, moradas ou o ficheiro da fatura.")
