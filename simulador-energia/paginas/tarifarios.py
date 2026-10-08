"""Ferramenta 3 — Comparar ofertas: há um tarifário mais barato do que o teu?

Ordem pensada para quem não percebe de energia: 1. os teus dados → 2. as ofertas mais baratas →
3. comparar uma proposta (opcional) → «Para saber mais» (mercado, tarifa regulada, indexados),
em blocos fechados. O IVA e as taxas só mudam o que se mostra, nunca as contas.
"""
import re
from datetime import date

import pandas as pd
import streamlit as st

from interface import componentes as ui
from interface import perfil as pf
from interface.dados import erse, medias_omie, ofertas_erse, omie_hoje_e_amanha, verificar_erse
from interface.graficos import CONFIG, grafico_omie
from nucleo import calculos, impostos, indexados, mercado, ofertas as of, periodos, roteiro, tarifas

passo = roteiro.passo(3)
ui.cabecalho_ferramenta(passo, roteiro.disponivel(3))
ui.aviso_fatura(pf.perfil())
p = pf.perfil()
da_fatura = bool(p.get("da_fatura"))
tarifa = erse()

st.caption("São 3 passos: confirma os teus dados, vê as ofertas mais baratas e, se recebeste uma "
           "proposta de outra empresa, compara-a. No fim da página há mais informação, se quiseres.")


def _texto(valor):
    """Nome vindo de fora (ERSE ou escrito pela pessoa) sem caracteres de formatação do markdown."""
    return re.sub(r"[*_`\[\]\\$<>~|#]", " ", str(valor)).strip()


def _paragrafo(texto):
    """Parágrafo de introdução com as palavras do glossário sublinhadas (balão ao tocar)."""
    st.html(f"<p>{ui.com_glossario(texto)}</p>")


# ---------- 1. os teus dados (mudam todas as contas da página)
st.write("")
st.subheader("1. Os teus dados")
c1, c2, c3 = st.columns(3)
with c1:
    kva = pf.campo(st.selectbox, "Potência contratada", "kva", "t_kva", options=pf.ESCALOES_KVA,
                   format_func=lambda k: f"{ui.numero(k, 2)} kVA",
                   help="Está na fatura, nos dados do contrato. Por exemplo: «Potência contratada: "
                        "6,90 kVA». Muda o preço por dia e as ofertas que aparecem. Se não sabes, "
                        "deixa 6,90 kVA, uma das mais comuns.")
with c2:
    consumo = pf.campo(st.number_input, "Consumo (kWh)", "consumo_kwh", "t_consumo",
                       min_value=0.0, step=10.0,
                       help="Quanta eletricidade gastaste. Na fatura aparece em kWh, junto às leituras "
                            "do contador. Por exemplo: 300 kWh. É o mesmo valor de «A minha fatura»: "
                            "se o mudares aqui, muda lá também.")
with c3:
    dias = pf.campo(st.number_input, "Dias que a fatura cobre", "dias", "t_dias", min_value=1, step=1,
                    help="Quantos dias a fatura cobre. Conta-os pelas datas «de … a …» no topo da "
                         "fatura. Por exemplo: 30.")
ROTULO_IVA = "Incluir IVA e taxas"   # igual em «A minha fatura»
com_iva = pf.campo(st.toggle, ROTULO_IVA, "com_impostos",
                   "t_impostos", padrao=False,
                   help="Desligado: só o preço da energia e da potência, como nas propostas das "
                        "empresas. Ligado: junta o IVA e as outras taxas, para comparares com o total "
                        "da tua fatura em papel.")

fixos = tarifas.precos_fixos(tarifa, kva)
potencia_dia = tarifas.preco_potencia(tarifa, kva)
familia = p.get("familia_numerosa", False)
nota_iva = "com IVA e taxas" if com_iva else "sem IVA nem taxas"


def total_periodo(energia, potencia):
    """Custo no período, com ou sem IVA e taxas (só muda o que se mostra)."""
    if com_iva:
        return impostos.com_impostos(energia, potencia, consumo, dias, kva, familia)["total"]
    return energia + potencia


def por_mes(energia, potencia):
    """€ por mês (30 dias) a partir da energia e da potência do período."""
    return total_periodo(energia, potencia) * 30 / dias


energia_atual, potencia_atual = consumo * p["preco_energia"], p["preco_diario"] * dias
atual_mes = por_mes(energia_atual, potencia_atual)

# ---------- 2. as ofertas mais baratas (dados oficiais da ERSE)
st.write("")
st.subheader("2. As ofertas mais baratas para ti")
lista_erse, data_erse = ofertas_erse()
com_perfil = p.get("perfil_da_fatura", False)
pv = p["pct_vazio"] if com_perfil else None
pp = p["pct_ponta"] if com_perfil and p.get("ponta_na_fatura", True) else None


def _cor(valor, minimo, maximo):
    """Do verde (mais barato) ao vermelho (mais caro), translúcido para os dois temas."""
    r = 0 if maximo == minimo else (valor - minimo) / (maximo - minimo)
    verde, carmim = (47, 138, 94), (200, 40, 60)
    rgb = [round(a + (b - a) * r) for a, b in zip(verde, carmim)]
    return f"background-color: rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.22)"


if not lista_erse:
    st.info("Agora não consigo mostrar a lista oficial de ofertas da ERSE. Tenta mais tarde.",
            icon=":material/cloud_off:")
else:
    if not com_iva:
        st.info("Atenção: estes valores não têm IVA nem taxas. Por isso são mais baixos do que o total "
                f"da tua fatura em papel. Para os veres com tudo, liga «{ROTULO_IVA}» no passo 1.",
                icon=":material/info:")
    top = of.mais_baratas(lista_erse, consumo, dias, kva, pv, pp)
    if top:
        linhas = [(o, por_mes(c - o.potencia_dia * dias, o.potencia_dia * dias)) for o, c in top]
        melhor, valor = linhas[0]
        poupanca = atual_mes - valor
        hoje_pagas = "Hoje pagas" if da_fatura else "Com os preços preenchidos, pagas"
        if poupanca > 0.005:
            conclusao = f"Podes poupar até **{ui.euros(poupanca)} € por mês**."
        else:
            conclusao = ("Nenhuma oferta de preço fixo fica mais barata do que "
                         + ("o que pagas hoje." if da_fatura else "os preços preenchidos."))
        st.markdown(f"Com o teu consumo, a oferta mais barata é **{_texto(melhor.comercializador)} – "
                    f"{_texto(melhor.nome)}**: {ui.euros(valor)} € por mês. {hoje_pagas} cerca de "
                    f"{ui.euros(atual_mes)} € por mês. {conclusao}")
        ui.podio_ofertas(linhas, atual_mes, "por mês", p.get("comercializador"),
                         com_fatura=bool(p.get("da_fatura")))
        st.caption(f"A melhor oferta de cada empresa, só de eletricidade e para qualquer casa. Valores por "
                   f"mês, {nota_iva}. Antes de mudar, confirma as condições no site da empresa.")
    else:
        st.info("Não encontrei ofertas de preço fixo para esta potência contratada.",
                icon=":material/search_off:")

    st.write("")
    with st.expander("Todas as ofertas do mercado (lista completa, com filtros)", icon=":material/list:"):
        st.caption("Filtros (opcional): escolhe o que queres ver na lista.")
        empresas = sorted({o.comercializador for o in lista_erse if o.com != "TUR"})
        esconder = st.multiselect("Esconder empresas", empresas, key="t_esconder",
                                  placeholder="Nenhuma: mostra todas",
                                  help="Escolhe empresas que não queres ver na lista.")
        f1, f2, f3 = st.columns(3)
        with f1:
            sem_fid = st.toggle("Mostrar só ofertas sem fidelização", key="t_sem_fid",
                                help="Fidelização é um tempo mínimo de contrato. Se saíres antes, podes "
                                     "ter de pagar. Liga isto para ver só ofertas sem esse compromisso.")
        with f2:
            duais = st.toggle("Mostrar também ofertas com gás", key="t_duais",
                              help="Ofertas que só podes ter se contratares também o gás com a mesma "
                                   "empresa.")
        with f3:
            restritas = st.toggle("Mostrar também ofertas só para alguns clientes", key="t_restritas",
                                  help="Por exemplo: só para sócios, para quem já é cliente de outro "
                                       "serviço ou para quem tem carro elétrico.")
        todas = of.mais_baratas(lista_erse, consumo, dias, kva, pv, pp, n=None, por_empresa=False,
                                incluir_duais=duais, incluir_restricoes=restritas,
                                so_sem_fidelizacao=sem_fid, excluir=set(esconder))
        if todas:
            mensal = [por_mes(c - o.potencia_dia * dias, o.potencia_dia * dias) for o, c in todas]
            notas = (("obriga a ter gás", "dual"), ("só para alguns clientes", "restricoes"),
                     ("tem benefícios à parte, como saldo ou devoluções, que não entram na conta",
                      "reembolsos"))
            tabela_of = pd.DataFrame([{
                "Empresa": o.comercializador, "Oferta": o.nome, "Opção horária": periodos.NOMES[o.opcao],
                "Por mês (€)": v, "Fidelização": "sim" if o.fidelizacao else "não",
                "Notas": " · ".join(texto for texto, campo in notas if getattr(o, campo)),
                "Condições": o.ligacao if o.ligacao.startswith("http") else None,
            } for (o, _), v in zip(todas, mensal)])
            texto_tab = ui.tabela_formatada(tabela_of)
            minimo, maximo = min(mensal), max(mensal)
            estilo = texto_tab.style.apply(
                lambda _: [_cor(v, minimo, maximo) for v in mensal], subset=["Por mês (€)"])
            st.dataframe(estilo, hide_index=True, width="stretch", height=420, column_config={
                "Opção horária": st.column_config.TextColumn(
                    "Opção horária", help="Simples: o mesmo preço a qualquer hora. Bi-horário e "
                                          "tri-horário: preços diferentes conforme a hora."),
                "Por mês (€)": st.column_config.TextColumn(
                    "Por mês (€)", help=f"Quanto pagarias por mês com o teu consumo, {nota_iva}."),
                "Fidelização": st.column_config.TextColumn(
                    "Fidelização", help="Tempo mínimo de contrato. «sim»: sair antes pode ter custos."),
                "Notas": st.column_config.TextColumn("Notas", help="O que deves saber antes de escolher."),
                "Condições": st.column_config.LinkColumn(
                    "Condições", display_text="ver no site",
                    help="As condições da oferta no site da empresa, numa janela nova."),
            })
            st.caption(f"Todas as ofertas do mercado com estas escolhas: {len(todas)} de preço fixo para "
                       f"{ui.numero(kva, 2)} kVA, da mais barata (no topo) para a mais cara. Preços "
                       f"oficiais da ERSE, atualizados a "
                       f"{data_erse:%d/%m/%Y}. Valores por mês, {nota_iva}. Benefícios à parte, como saldo "
                       "em cartão ou devoluções, não estão incluídos.")
        else:
            st.info("Nenhuma oferta aparece com estas escolhas. Tira empresas da lista «Esconder empresas» "
                    "ou desliga «Mostrar só ofertas sem fidelização».", icon=":material/filter_alt_off:")

# ---------- 3. comparar uma proposta de outra empresa (opcional)
st.write("")
st.subheader("3. Tens uma proposta de outra empresa? (opcional)")
st.caption("Escreve os preços da proposta e vê-a ao lado " + ("da tua fatura" if da_fatura else
           "dos teus preços") + ". Uma proposta só entra na comparação quando escreves o preço da "
           "energia.")


def _proposta(i):
    """Uma caixa de proposta (nome, energia, potência); None enquanto não tiver preço da energia."""
    letra = "ABC"[i]
    with st.container(border=True):
        n1, n2, n3 = st.columns([1.3, 1, 1])
        with n1:
            nome = pf.campo(st.text_input, "Nome da empresa ou da proposta", f"oferta_{i}_nome",
                            f"t_nome_{i}", padrao=f"Oferta {letra}",
                            help="Só para a reconheceres na tabela. Por exemplo: Empresa X.")
        with n2:
            pe = pf.campo(st.number_input, "Preço da energia (€ por kWh)", f"oferta_{i}_energia",
                          f"t_pe_{i}", padrao=0.0, min_value=0.0, step=0.001, format="%.4f",
                          help="Quanto custa cada kWh, sem IVA. Está na proposta ou na «ficha "
                               "padronizada» da oferta, no site da empresa. Exemplo: 0,1654.")
        with n3:
            pd_ = pf.campo(st.number_input, "Preço da potência (€ por dia)", f"oferta_{i}_potencia",
                           f"t_pd_{i}", padrao=0.0, min_value=0.0, step=0.001, format="%.4f",
                           help="Quanto pagas por dia pela potência, mesmo sem gastar. Usa o valor para "
                                f"a tua potência, {ui.numero(kva, 2)} kVA. Exemplo: 0,3659.")
    if pe > 0:
        return {"nome": nome or f"Oferta {letra}", "preco_energia": pe, "preco_diario": pd_}
    return None


propostas = [_proposta(0)]
with st.expander("Comparar mais propostas", icon=":material/add:"):
    propostas += [_proposta(1), _proposta(2)]
caixa_comparacao = st.container()     # a tabela é desenhada no fim: o indexado vem de «Para saber mais»

# ---------- para saber mais (fechado: não é preciso para comparar)
st.write("")
st.subheader("Para saber mais")
st.caption("Não precisas disto para comparar. Abre só o que te interessar.")

with st.expander("O preço do mercado hoje (interessa a quem tem tarifário indexado)",
                 icon=":material/show_chart:"):
    _paragrafo("É o preço a que as empresas compram a eletricidade no mercado ibérico (OMIE), hora a "
               "hora. Se o teu contrato tem preço fixo, isto não muda a tua fatura.")
    try:
        hoje, amanha = omie_hoje_e_amanha()
    except mercado.SemRede:
        st.warning("Não consegui ver o preço do mercado agora. O resto da página funciona na mesma.",
                   icon=":material/wifi_off:")
    else:
        r_hoje = mercado.resumo_omie(hoje)
        unidade = "cêntimos por kWh"
        metricas = [ui.metrica("Preço médio hoje", ui.euros(r_hoje["media"] / 10), unidade, destaque=True),
                    ui.metrica("Na hora mais barata", ui.euros(r_hoje["min"] / 10), unidade),
                    ui.metrica("Na hora mais cara", ui.euros(r_hoje["max"] / 10), unidade)]
        if amanha:
            metricas.append(ui.metrica("Preço médio amanhã",
                                       ui.euros(mercado.resumo_omie(amanha)["media"] / 10), unidade))
        ui.grelha(metricas, largura_min=150)
        st.plotly_chart(grafico_omie(hoje, amanha, altura=260), config=CONFIG, width="stretch")
        st.caption(f"Preço de cada hora, hoje{' e amanhã' if amanha else ''}, em hora de Portugal. A zona "
                   f"sombreada a dourado são as horas de vazio, das {periodos.VAZIO_INICIO.hour}h às "
                   f"{periodos.VAZIO_FIM.hour}h. Ainda faltam as redes, os custos da empresa e os "
                   f"impostos. Por exemplo, {ui.euros(r_hoje['media'] / 10)} cêntimos por kWh é o mesmo "
                   f"que {ui.preco(r_hoje['media'] / 1000)} € por kWh, a unidade que vês na fatura.")

with st.expander("Os preços da tarifa regulada (ERSE)", icon=":material/account_balance:"):
    _paragrafo("A tarifa regulada é o preço fixo definido pela ERSE, a entidade que regula a "
               "eletricidade. Serve de referência: se pagas mais do que isto, é provável que haja "
               "ofertas mais baratas.")
    tabela_erse = pd.DataFrame([
        {"Opção horária": periodos.NOMES[o],
         "Horas": "Todas as horas" if per == "simples"
         else f"{periodos.NOMES[per]} · {ui.DICA_PERIODO.get(per, '')}",
         "Preço por kWh (€)": preco}
        for o in tarifas.OPCOES for per, preco in fixos[o].items()])
    col_tab, col_info = st.columns([1.4, 1], gap="large")
    with col_tab:
        st.table(ui.tabela_formatada(tabela_erse, {"Preço por kWh (€)": 4}), hide_index=True)
    with col_info:
        ui.grelha([ui.metrica("Preço da potência", ui.preco(potencia_dia), "€ por dia")], largura_min=150)
        st.caption(f"Pagas este valor todos os dias, mesmo sem gastar. É o preço para "
                   f"{ui.numero(kva, 2)} kVA.")
        data = "/".join(reversed(tarifa["extraido_em"].split("-")))
        st.caption(f"Preços oficiais da ERSE para {tarifa.get('ano', date.today().year)}, atualizados a "
                   f"{data}. Sem IVA nem taxas.")
        if st.button("Confirmar no site da ERSE se os preços mudaram", icon=":material/sync:",
                     help="Vai ao site da ERSE e compara os preços oficiais com os que estou a usar. "
                          "Demora alguns segundos."):
            with st.spinner("A abrir o site da ERSE…"):
                try:
                    _, mudancas = verificar_erse()
                except Exception:   # sem rede, descarga cortada, documento ilegível…
                    st.session_state["erse_msg"] = ("aviso", "Não consegui abrir o site da ERSE agora. "
                                                    "Continuo com os preços oficiais que já tinha guardados.")
                else:
                    n = len(mudancas)
                    st.session_state["erse_msg"] = (
                        ("aviso", f"A ERSE mudou {n} {'preço' if n == 1 else 'preços'}. A tabela já mostra "
                                  "os preços novos.") if mudancas else
                        ("ok", "Está tudo certo: os preços são os mesmos que a ERSE publica."))
            st.rerun()               # a tabela e a legenda voltam a ser desenhadas com os dados lidos
        tipo, texto = st.session_state.pop("erse_msg", (None, None))
        if tipo == "ok":
            st.success(texto, icon=":material/task_alt:")
        elif tipo == "aviso":
            st.warning(texto, icon=":material/info:")

medias, info_omie = medias_omie(7)
indexado = None
with st.expander("Comparar também com um tarifário indexado (preço que muda com o mercado)",
                 icon=":material/tune:"):
    if medias is None:
        st.caption("Sem o preço do mercado agora, não consigo estimar o indexado. Tenta mais tarde.")
    else:
        _paragrafo("Num tarifário indexado, o preço da energia acompanha o mercado. Se tens uma proposta "
                   "assim, escreve as perdas e a margem que vêm nas condições do contrato: a estimativa "
                   "aparece na tabela do passo 3.")
        i1, i2 = st.columns(2)
        with i1:
            perdas = pf.campo(st.number_input, "Perdas (%)", "perdas_pct", "t_perdas", padrao=0.0,
                              min_value=0.0, max_value=50.0, step=0.5,
                              help="Só para tarifários indexados. É uma percentagem que vem nas "
                                   "condições do contrato, por exemplo 16. Se não sabes, deixa 0.")
        with i2:
            margem = pf.campo(st.number_input, "Margem da empresa (€ por kWh)", "margem_kwh",
                              "t_margem", padrao=0.0, min_value=0.0, step=0.001, format="%.4f",
                              help="O que a empresa junta ao preço do mercado em cada kWh. Vem nas "
                                   "condições do contrato; às vezes chama-se «fee» ou «spread». Se não "
                                   "sabes, deixa 0.")
        preco_idx = tarifas.precos_indexados(medias, tarifa, perdas, margem)["simples"]["simples"]
        minimo_idx = perdas == 0 and margem == 0
        indexado = {"nome": "Indexado (mínimo possível)" if minimo_idx else "Indexado (estimativa)",
                    "preco_energia": preco_idx, "preco_diario": potencia_dia}
        st.caption(f"Com o preço do mercado dos últimos {info_omie['dias']} dias, um indexado ficaria em "
                   f"cerca de {ui.preco(preco_idx)} € por kWh, sem IVA."
                   + (" Com perdas e margem a 0, este é o valor mais baixo possível: na prática é mais "
                      "caro." if minimo_idx else ""))

with st.expander("Ofertas com preço que muda todos os meses (indexadas)", icon=":material/trending_up:"):
    st.caption("Ofertas indexadas · estimativa por empresa, com o preço do mercado dos últimos 30 dias.")
    medias30, info30 = medias_omie(30)
    if medias30 is None:
        st.info("Não consegui ver o preço do mercado agora. Tenta daqui a pouco.", icon=":material/wifi_off:")
    else:
        _paragrafo("Num tarifário indexado, o preço da energia acompanha o mercado e muda todos os meses.")
        st.info("É só uma estimativa, feita com o preço médio do mercado nos últimos 30 dias. No próximo "
                "mês pode ser mais ou menos.", icon=":material/info:")
        omie_mwh = medias30["simples"]["simples"]
        tar = tarifa["tar"]["energia_eur_kwh"]["simples"]["simples"]
        potencias = of.potencia_indexadas(lista_erse, kva, [(f.comercializador, f.procurar)
                                                            for f in indexados.FORMULAS])
        potencias[None] = potencia_dia
        linhas_idx = indexados.estimar(omie_mwh, date.today().month, tar, consumo, dias, potencias)
        tabela_idx = pd.DataFrame([{
            "Empresa": f.comercializador, "Oferta": f.oferta, "Preço por kWh (€)": preco,
            "Por mês (€)": por_mes(preco * consumo, custo - preco * consumo),
            "Nota": "valor aproximado" if f.aproximado else "",
            "Condições": f.fonte} for f, preco, custo in linhas_idx])
        st.dataframe(ui.tabela_formatada(tabela_idx, {"Preço por kWh (€)": 4}), hide_index=True,
                     width="stretch", column_config={
                         "Preço por kWh (€)": st.column_config.TextColumn(
                             "Preço por kWh (€)", help="Preço estimado de cada kWh, sem IVA."),
                         "Por mês (€)": st.column_config.TextColumn(
                             "Por mês (€)", help=f"Quanto pagarias por mês com o teu consumo, {nota_iva}."),
                         "Nota": st.column_config.TextColumn(
                             "Nota", help="«valor aproximado»: a empresa não publica todos os números, "
                                          "por isso usei valores médios."),
                         "Condições": st.column_config.LinkColumn(
                             "Condições", display_text="ver no site",
                             help="As condições publicadas pela empresa, numa janela nova."),
                     })
        st.caption(f"Valores por mês, {nota_iva}. Preço médio do mercado nos últimos {info30['dias']} "
                   f"dias: {ui.numero(omie_mwh / 10, 1)} cêntimos por kWh. Cada empresa publica a sua "
                   f"regra de preço (consultada a {indexados.FORMULAS[0].consultado}). O preço da "
                   "potência é o de cada empresa, quando a ERSE o publica; senão, o da tarifa regulada. "
                   "Estes valores costumam ficar acima da linha «Indexado» do passo 3, porque já contam "
                   "as perdas e a margem de cada empresa.")

# ---------- 3. (continuação) a tabela da comparação, por baixo das propostas
with caixa_comparacao:
    nome_atual = "A tua fatura" if da_fatura else "Os teus preços"
    lista = [{"nome": "Tarifa regulada (ERSE)", "preco_energia": fixos["simples"]["simples"],
              "preco_diario": potencia_dia}]
    if indexado:
        lista.append(indexado)
    lista.append({"nome": nome_atual, "preco_energia": p["preco_energia"],
                  "preco_diario": p["preco_diario"]})
    lista += [x for x in propostas if x]
    resultados = calculos.comparar_tarifarios(consumo, dias, lista)

    if indexado:
        st.info(f"A linha «{indexado['nome']}» é só uma conta aproximada para um tarifário com preço que "
                "muda todos os meses (indexado). "
                + ("Na prática, sai mais caro do que isto. " if minimo_idx else "")
                + "Se não tens uma proposta assim, podes ignorá-la.", icon=":material/info:")
    # o total de cada linha, já com IVA e taxas se o interruptor estiver ligado: a frase e a tabela
    # usam estes mesmos números
    totais = [total_periodo(r["energia"], r["potencia"]) for r in resultados]
    # a frase compara o que a pessoa paga com a linha mais barata das outras
    outro, total_outro = min(((r, t) for r, t in zip(resultados, totais) if r["nome"] != nome_atual),
                             key=lambda par: par[1])
    nome_outro = _texto(outro["nome"])
    total_atual = total_periodo(energia_atual, potencia_atual)
    diferenca = total_atual - total_outro
    if diferenca > 0.005:
        quem = "Com a tua fatura" if da_fatura else "Com os teus preços"
        st.markdown(f"Com {ui.numero(consumo)} kWh em {dias} dias, o mais barato desta tabela é "
                    f"**{nome_outro}**: {ui.euros(total_outro)} €, {nota_iva}. {quem}, também "
                    f"{nota_iva}, pagas {ui.euros(total_atual)} €. São {ui.euros(diferenca)} € a mais "
                    f"do que com **{nome_outro}**.")
    elif diferenca < -0.005:
        st.markdown("Com estes valores, " + ("a tua fatura já é a mais barata" if da_fatura
                                              else "os teus preços já são os mais baratos")
                    + f" desta tabela: pagas menos {ui.euros(-diferenca)} € do que com "
                      f"**{nome_outro}**, {nota_iva}.")
    else:
        st.markdown("Com estes valores, " + ("a tua fatura custa" if da_fatura else "os teus preços custam")
                    + f" o mesmo que **{nome_outro}**, o mais barato desta tabela.")

    tabela = calculos.tabela_comparativa(resultados)
    if com_iva:
        # a diferença passa a ser a do total com IVA, para bater certo com a frase de cima
        tabela.insert(4, "Total com IVA e taxas (€)", totais)
        tabela["Diferença (€)"] = [t - min(totais) for t in totais]
        tabela = tabela.sort_values("Total com IVA e taxas (€)", kind="stable").reset_index(drop=True)
    tabela = tabela.rename(columns={      # só aqui: os nomes de origem são usados noutras páginas
        "Potência (€)": "Potência, parte fixa (€)",
        "Total (€)": f"Sem IVA, em {dias} dias (€)" if com_iva else f"Total em {dias} dias (€)",
        "Diferença (€)": "A mais do que o mais barato (€)"})
    st.dataframe(ui.tabela_formatada(tabela), hide_index=True, width="stretch")
    st.caption("Do mais barato para o mais caro, com o mesmo consumo e os mesmos dias para todos. "
               + ("As colunas «Total com IVA e taxas» e «A mais do que o mais barato» já têm o IVA e as "
                  "taxas; as outras não. " if com_iva else "Sem IVA nem taxas. ")
               + "O preço não é tudo: vê também a fidelização e o que cada oferta inclui.")
