"""Ferramenta 3 — Tarifários: mercado (OMIE), tarifa regulada (ERSE) e comparação."""
import pandas as pd
import streamlit as st

from interface import componentes as ui
from interface import perfil as pf
from interface.dados import erse, medias_omie, ofertas_erse, omie_hoje_e_amanha, verificar_erse
from interface.graficos import CONFIG, grafico_omie
from datetime import date

from nucleo import calculos, indexados, mercado, ofertas as of, periodos, roteiro, tarifas

passo = roteiro.passo(3)
ui.cabecalho_ferramenta(passo, roteiro.disponivel(3))
ui.aviso_fatura(pf.perfil())
p = pf.perfil()

# ---------- mercado hoje (OMIE)
st.subheader("Mercado hoje · OMIE")
try:
    hoje, amanha = omie_hoje_e_amanha()
except mercado.SemRede:
    st.warning("Não consegui ligar ao OMIE agora. As comparações usam só a tarifa regulada.",
               icon=":material/wifi_off:")
else:
    r_hoje = mercado.resumo_omie(hoje)
    metricas = [ui.metrica("Média hoje", ui.euros(r_hoje["media"] / 10), "c€/kWh", destaque=True),
                ui.metrica("Mais barato", ui.euros(r_hoje["min"] / 10), "c€/kWh"),
                ui.metrica("Mais caro", ui.euros(r_hoje["max"] / 10), "c€/kWh")]
    if amanha:
        metricas.append(ui.metrica("Média amanhã", ui.euros(mercado.resumo_omie(amanha)["media"] / 10),
                                   "c€/kWh"))
    ui.grelha(metricas, largura_min=150)
    st.plotly_chart(grafico_omie(hoje, amanha, altura=260), config=CONFIG, width="stretch")
    st.caption("Preço do mercado grossista em Portugal (OMIE), antes de redes, perdas, margem e "
               f"impostos · hora de Portugal · a faixa dourada marca as horas de vazio "
               f"({periodos.texto_vazio_curto()}).")

# ---------- tarifa regulada (ERSE)
st.write("")
st.subheader("Tarifa regulada · ERSE (preço fixo)")
tarifa = erse()
kva = pf.campo(st.selectbox, "Potência contratada", "kva", "t_kva", options=pf.ESCALOES_KVA,
               format_func=lambda k: f"{ui.numero(k, 2)} kVA", help="Está nos dados do contrato. Define o preço da potência na tarifa regulada.")
fixos = tarifas.precos_fixos(tarifa, kva)
tabela_erse = pd.DataFrame([
    {"Opção": periodos.NOMES[o], "Período": periodos.NOMES[per], "€/kWh": preco}
    for o in tarifas.OPCOES for per, preco in fixos[o].items()])
col_tab, col_info = st.columns([1.4, 1], gap="large")
with col_tab:
    st.dataframe(ui.tabela_formatada(tabela_erse, {"€/kWh": 4}), hide_index=True, width="stretch")
with col_info:
    ui.grelha([ui.metrica("Potência", ui.preco(tarifas.preco_potencia(tarifa, kva)), "€/dia")],
              largura_min=150)
    data = "/".join(reversed(tarifa["extraido_em"].split("-")))
    st.caption(f"{tarifa['fonte']} · {tarifa['regulada']['quadro']} · {tarifa['origem']}, "
               f"extraído em {data}. Sem IVA nem taxas.")
    if st.button("Verificar na ERSE agora", icon=":material/sync:"):
        with st.spinner("A ler o documento oficial da ERSE…"):
            try:
                _, mudancas = verificar_erse()
            except Exception:   # sem rede, descarga cortada, documento ilegível…
                st.session_state["erse_msg"] = ("aviso", "Não consegui ler a ERSE agora. Continuo "
                                                "com a cópia local, extraída do documento oficial.")
            else:
                st.session_state["erse_msg"] = (
                    ("aviso", f"A ERSE mudou {len(mudancas)} preço(s) face à cópia local. "
                              "A tabela já mostra os valores novos.") if mudancas else
                    ("ok", "Confere: os preços da ERSE são iguais aos que estou a usar."))
        st.rerun()               # a tabela e a legenda voltam a ser desenhadas com os dados lidos
    tipo, texto = st.session_state.pop("erse_msg", (None, None))
    if tipo == "ok":
        st.success(texto, icon=":material/task_alt:")
    elif tipo == "aviso":
        st.warning(texto, icon=":material/info:")

# ---------- comparar tarifários
st.write("")
st.subheader("Compara tarifários")
c1, c2 = st.columns(2)
with c1:
    consumo = pf.campo(st.number_input, "Consumo (kWh)", "consumo_kwh", "t_consumo",
                       min_value=0.0, step=10.0, help="A energia gasta no período, em kWh (vem da Fatura, se já a preencheste).")
with c2:
    dias = pf.campo(st.number_input, "Dias do período", "dias", "t_dias", min_value=1, step=1,
                    help="Número de dias do período da fatura.")

potencia_dia = tarifas.preco_potencia(tarifa, kva)
lista = [{"nome": "Regulada ERSE · fixo (simples)", "preco_energia": fixos["simples"]["simples"],
          "preco_diario": potencia_dia}]

medias, info_omie = medias_omie(7)
with st.expander("Tarifa indexada ao OMIE (estimativa)", icon=":material/show_chart:",
                 expanded=medias is not None):
    if medias is None:
        st.caption("Sem dados do OMIE agora: a estimativa indexada fica de fora.")
    else:
        i1, i2 = st.columns(2)
        with i1:
            perdas = pf.campo(st.number_input, "Perdas (%)", "perdas_pct", "t_perdas", padrao=0.0,
                              min_value=0.0, max_value=50.0, step=0.5,
                              help="Fator de perdas do teu contrato indexado. A ERSE não "
                                   "publica um valor único: vê as condições do contrato.")
        with i2:
            margem = pf.campo(st.number_input, "Margem do comercializador (€/kWh)", "margem_kwh",
                              "t_margem", padrao=0.0, min_value=0.0, step=0.001, format="%.4f",
                              help="Valor fixo que o comercializador soma ao preço do mercado.")
        indexado = tarifas.precos_indexados(medias, tarifa, perdas, margem)["simples"]["simples"]
        lista.append({"nome": "Indexado OMIE (simples)", "preco_energia": indexado,
                      "preco_diario": potencia_dia})
        st.caption(f"Estimativa com o mercado dos últimos {info_omie['dias']} dias e as tarifas de "
                   f"acesso da ERSE: {ui.preco(indexado)} €/kWh. Sem perdas nem margem é o valor "
                   "mais baixo possível.")

st.caption("Os teus tarifários (preços de outras ofertas que queiras comparar):")
ofertas = [{"nome": "A tua fatura", "preco_energia": pf.perfil()["preco_energia"],
            "preco_diario": pf.perfil()["preco_diario"]}]
for i, coluna in enumerate(st.columns(3)):
    letra = "ABC"[i]
    with coluna.container(border=True):
        nome = pf.campo(st.text_input, "Nome", f"oferta_{i}_nome", f"t_nome_{i}",
                        padrao=f"Oferta {letra}", help="Um nome para reconheceres esta oferta.")
        pe = pf.campo(st.number_input, "Energia (€/kWh)", f"oferta_{i}_energia", f"t_pe_{i}",
                      padrao=0.0, min_value=0.0, step=0.001, format="%.4f",
                      help="Preço de cada kWh nesta oferta, sem IVA (vem na proposta ou no site).")
        pd_ = pf.campo(st.number_input, "Potência (€/dia)", f"oferta_{i}_potencia", f"t_pd_{i}",
                       padrao=0.0, min_value=0.0, step=0.001, format="%.4f",
                       help="Preço diário da potência nesta oferta, para a tua potência contratada.")
        if pe > 0:
            ofertas.append({"nome": nome or f"Oferta {letra}", "preco_energia": pe,
                            "preco_diario": pd_})
lista += ofertas

resultados = calculos.comparar_tarifarios(consumo, dias, lista)
tabela = calculos.tabela_comparativa(resultados)
st.dataframe(ui.tabela_formatada(tabela), hide_index=True, width="stretch")
st.caption("Ordenado do mais barato para o mais caro com estes valores. O preço não é tudo: "
           "vê também as condições (fidelização, serviços incluídos, atualização de preços).")


# ---------- todas as ofertas do mercado (dados oficiais da ERSE)
def _cor(valor, minimo, maximo):
    """Do verde (mais barato) ao carmim (mais caro), translúcido para os dois temas."""
    r = 0 if maximo == minimo else (valor - minimo) / (maximo - minimo)
    verde, carmim = (47, 138, 94), (200, 40, 60)
    rgb = [round(a + (b - a) * r) for a, b in zip(verde, carmim)]
    return f"background-color: rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.22)"


lista_erse, data_erse = ofertas_erse()
if lista_erse:
    st.write("")
    st.subheader("Todas as ofertas do mercado")
    perfil = pf.perfil()
    com_perfil = perfil.get("perfil_da_fatura", False)
    pv = perfil["pct_vazio"] if com_perfil else None
    pp = perfil["pct_ponta"] if com_perfil and perfil.get("ponta_na_fatura", True) else None
    empresas = sorted({o.comercializador for o in lista_erse if o.com != "TUR"})
    f1, f2, f3, f4 = st.columns([1.6, 1, 1, 1])
    with f1:
        esconder = st.multiselect("Esconder empresas", empresas, key="t_esconder",
                                  placeholder="Nenhuma")
    with f2:
        sem_fid = st.toggle("Só sem fidelização", key="t_sem_fid")
    with f3:
        duais = st.toggle("Incluir duais", key="t_duais",
                          help="Ofertas que obrigam a contratar também o gás com a mesma empresa.")
    with f4:
        restritas = st.toggle("Incluir com restrições", key="t_restritas",
                              help="Ofertas só para sócios, clientes de outros serviços ou com carro elétrico.")
    todas = of.mais_baratas(lista_erse, consumo, dias, kva, pv, pp, n=None, por_empresa=False,
                            incluir_duais=duais, incluir_restricoes=restritas,
                            so_sem_fidelizacao=sem_fid, excluir=set(esconder))
    if todas:
        mensal = [c * 30 / dias for _, c in todas]
        tabela_of = pd.DataFrame([{
            "Empresa": o.comercializador, "Oferta": o.nome, "Opção": periodos.NOMES[o.opcao],
            "€/mês": v, "Fidelização": "sim" if o.fidelizacao else "não",
            "Notas": " · ".join(n for n, s in (("dual", o.dual), ("com restrições", o.restricoes),
                                              ("benefícios à parte", o.reembolsos)) if s),
            "Ficha": o.ligacao if o.ligacao.startswith("http") else None,
        } for (o, _), v in zip(todas, mensal)])
        texto_tab = ui.tabela_formatada(tabela_of)
        minimo, maximo = min(mensal), max(mensal)
        estilo = texto_tab.style.apply(
            lambda _: [_cor(v, minimo, maximo) for v in mensal], subset=["€/mês"])
        st.dataframe(estilo, hide_index=True, width="stretch", height=420,
                     column_config={"Ficha": st.column_config.LinkColumn("Ficha", display_text="abrir ↗")})
        st.caption(f"{len(todas)} ofertas de preço fixo para {ui.numero(kva, 2)} kVA, com o teu consumo, "
                   f"da mais barata (verde) para a mais cara (carmim). Dados da ERSE de "
                   f"{data_erse:%d/%m/%Y}; valores por mês, sem IVA nem taxas. Benefícios à parte "
                   "(saldo em cartões, devoluções) não entram no preço.")
    else:
        st.info("Nenhuma oferta com estes filtros.")

# ---------- indexados por empresa (fórmulas publicadas)
st.write("")
st.subheader("Ofertas indexadas · estimativa por empresa")
medias30, info30 = medias_omie(30)
if medias30 is None:
    st.info("Sem ligação ao mercado (OMIE) agora: volta a tentar daqui a pouco.", icon=":material/wifi_off:")
else:
    omie_mwh = medias30["simples"]["simples"]
    tar = tarifa["tar"]["energia_eur_kwh"]["simples"]["simples"]
    potencias = of.potencia_indexadas(lista_erse, kva, [(f.comercializador, f.procurar)
                                                        for f in indexados.FORMULAS])
    potencias[None] = tarifas.preco_potencia(tarifa, kva)
    linhas_idx = indexados.estimar(omie_mwh, date.today().month, tar, consumo, dias, potencias)
    tabela_idx = pd.DataFrame([{
        "Empresa": f.comercializador, "Oferta": f.oferta, "€/kWh": preco, "€/mês": custo * 30 / dias,
        "Como se calcula": f.descricao + (" (valores aproximados)" if f.aproximado else ""),
        "Fonte": f.fonte} for f, preco, custo in linhas_idx])
    st.dataframe(ui.tabela_formatada(tabela_idx, {"€/kWh": 4}), hide_index=True, width="stretch",
                 column_config={"Fonte": st.column_config.LinkColumn("Fonte", display_text="abrir ↗")})
    st.caption(f"Com a média do mercado dos últimos {info30['dias']} dias ({ui.numero(omie_mwh, 1)} €/MWh), "
               f"a tarifa de acesso da ERSE e as fórmulas publicadas por cada empresa (consultadas a "
               f"{indexados.FORMULAS[0].consultado}). A potência vem das ofertas da ERSE; sem ela, usa-se "
               "a da tarifa regulada. Valores por mês, sem IVA nem taxas. O mercado muda todos os dias.")
