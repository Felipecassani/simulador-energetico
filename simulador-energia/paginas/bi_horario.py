"""Ferramenta 5 — «Bi-horário compensa?»: simples, bi ou tri-horário, com preço fixo ou indexado.

Para qualquer pessoa: primeiro explica o que são as opções, depois pede os números (1.), dá o
resultado numa frase (2.) e no fim mostra as horas de cada período (3.). Os avisos que mudam a
decisão (estimativa, sem IVA, indexado sem perdas e margem) aparecem antes do resultado.
"""
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from interface import componentes as ui
from interface import carregar_eredes
from interface import perfil as pf
from interface.dados import erse, medias_omie
from interface.graficos import CONFIG, grafico_opcoes
from nucleo import impostos, periodos, roteiro, tarifas

NOITE = f"das {periodos.VAZIO_INICIO.hour}h às {periodos.VAZIO_FIM.hour}h"


def _kva(kva):
    """6.9 → '6,9' e 3.45 → '3,45', como aparece na fatura."""
    return ui.numero(kva, 2).rstrip("0").rstrip(",")


def _nome(linha):
    return (f"{periodos.NOMES[linha['opcao']]} com "
            + ("preço fixo" if linha["modalidade"] == "fixo" else "preço indexado"))


def _diferenca(v):
    """Poupança em palavras, sem sinais: «poupas 2,10 €», «pagas mais 1,30 €» ou «igual»."""
    if v > 0.005:
        return f"poupas {ui.euros(v)} €"
    if v < -0.005:
        return f"pagas mais {ui.euros(-v)} €"
    return "igual"


passo = roteiro.passo(5)
ui.cabecalho_ferramenta(passo, roteiro.disponivel(5))
ui.aviso_fatura(pf.perfil())
tarifa = erse()
agora = datetime.now(periodos.LISBOA)
estacao = periodos.epoca(agora)

with st.expander("O que são simples, bi-horário e tri-horário?", icon=":material/help:", expanded=True):
    ui.texto(
        "Na fatura aparece como «Simples», «Bi-horária» ou «Tri-horária», perto da potência contratada.\n\n"
        "- **Simples:** o mesmo preço a qualquer hora.\n"
        f"- **Bi-horário:** mais barato {NOITE} (o «vazio») e mais caro no resto do dia.\n"
        "- **Tri-horário:** mais barato à noite, mais caro em 4 horas por dia (a «ponta») e com um preço "
        "intermédio no resto (as «cheias»).\n\n"
        "**Preço fixo** quer dizer que o preço de cada kWh fica igual durante meses. **Indexado** quer "
        "dizer que o preço segue o mercado e muda sempre.")

# ---------- 1. os números da pessoa
st.subheader(":material/edit_note: 1. Os teus números")
ui.nota("Copia-os da tua fatura. Se já preencheste «A minha fatura», já estão aqui.")
col_a, col_b = st.columns(2, gap="large")
with col_a:
    consumo = pf.campo(st.number_input, "Quanto gastaste (kWh)", "consumo_kwh", "b_consumo",
                       min_value=0.0, step=10.0,
                       help="Está na fatura, com «kWh» à frente (por exemplo «258 kWh»), perto das leituras "
                            "do contador. Se já preencheste «A minha fatura», este valor já vem de lá.")
    dias = pf.campo(st.number_input, "Quantos dias a fatura cobre", "dias", "b_dias", min_value=1, step=1,
                    help="Na fatura aparece o período, por exemplo «de 01/09 a 30/09»: são 30 dias. "
                         "Costuma ser entre 28 e 31.")
    kva = pf.campo(st.selectbox, "Potência contratada (kVA)", "kva", "b_kva",
                   options=pf.ESCALOES_KVA, format_func=lambda k: f"{_kva(k)} kVA",
                   help="Está na fatura, nos dados do contrato, com «kVA» à frente. Muitas casas têm 6,9 kVA. "
                        "É quanto podes ligar ao mesmo tempo, e pagas um valor fixo por dia por ela.")
with col_b:
    vazio = pf.campo(st.slider, f"Que parte gastas à noite, {NOITE}?", "pct_vazio", "b_vazio",
                     min_value=0.0, max_value=100.0, step=1.0, format="%.0f %%",
                     help="Se já tens bi-horário, a fatura mostra o consumo em «vazio». Exemplo: 120 kWh em "
                          "vazio num total de 300 kWh dá 40 %. Se não sabes, deixa 40 % e ajusta: sobe se pões "
                          "máquinas a lavar à noite, aqueces a água à noite ou carregas o carro à noite.")
    limite = float(100 - vazio)          # vazio + ponta nunca passam de 100 %
    if pf.perfil()["pct_ponta"] > limite:
        pf.atualizar(pct_ponta=limite)
    if st.session_state.get(pf.chave("b_ponta"), 0) > limite:
        st.session_state[pf.chave("b_ponta")] = limite
    if limite > 0:
        ponta = pf.campo(st.slider, "E nas horas mais caras (ponta)?", "pct_ponta", "b_ponta",
                         min_value=0.0, max_value=limite, step=1.0, format="%.0f %%",
                         help="Só conta para o tri-horário. São 4 horas por dia. Agora, no horário de "
                              f"{'verão' if estacao == 'verao' else 'inverno'}: "
                              f"{periodos.texto_intervalos('tri', 'ponta', estacao)} (vê todas as horas no "
                              "fim da página). Se não sabes, deixa 15 %. A noite e a ponta juntas não passam "
                              "de 100 %.")
    else:
        ponta = 0.0

medias, info = medias_omie(7)
if medias is not None:
    with st.expander("Só para contratos indexados: perdas e margem (opcional)", icon=":material/tune:"):
        perdas = pf.campo(st.number_input, "Perdas (%)", "perdas_pct", "b_perdas", padrao=0.0,
                          min_value=0.0, max_value=50.0, step=0.5,
                          help="Percentagem que a empresa soma ao preço do mercado pela energia que se perde "
                               "nos fios até tua casa. Está na ficha do teu contrato. Se não sabes, põe 16 %, "
                               "a média calculada com os valores da ERSE.")
        margem = pf.campo(st.number_input, "Margem da empresa (€ por kWh)", "margem_kwh", "b_margem",
                          padrao=0.0, min_value=0.0, step=0.001, format="%.4f",
                          help="Valor que a empresa soma a cada kWh. Na ficha da oferta aparece, por exemplo, "
                               "como 0,0100 €/kWh, ou seja, 1 cêntimo. Se deixares 0, o indexado parece mais "
                               "barato do que é.")
else:
    perdas = margem = 0.0

# consumos reais da E-REDES (contador inteligente): opção para quem não sabe as percentagens
carregar_eredes.secao("b")

linhas = tarifas.comparar_opcoes(consumo, vazio, ponta, dias, kva, tarifa,
                                 medias_omie=medias, perdas_pct=perdas, margem_eur_kwh=margem)
st.session_state["opcoes_linhas"] = linhas

# ---------- 2. o resultado
st.write("")
st.subheader(":material/payments: 2. Quanto pagarias")
p = pf.perfil()
st.info("Estes valores ainda não têm IVA nem taxas, por isso a tua conta real é mais alta. A ordem do mais "
        "barato ao mais caro quase não muda.", icon=":material/receipt:")
if not p.get("perfil_da_fatura"):
    st.warning("Atenção: estas contas usam uma estimativa do que gastas à noite e na ponta. Antes de mudares de "
               "contrato, confirma esses valores na fatura ou com os consumos da E-REDES (em cima).",
               icon=":material/warning:")
sem_margem = medias is not None and not perdas and not margem
if sem_margem:
    st.warning("Nas opções «indexado» ainda faltam as perdas e a margem da empresa. Põe-nas em «Só para "
               "contratos indexados: perdas e margem», em cima. Se não as souberes, põe 16 % de perdas. Sem "
               "elas, o indexado parece mais barato do que é.", icon=":material/warning:")

melhor = linhas[0]
ponta_estimada = p.get("perfil_da_fatura") and not p.get("ponta_na_fatura", True)
if ponta_estimada and melhor["opcao"] == "tri":
    st.warning("A tua fatura não diz quanto gastas nas horas mais caras (ponta): o resultado do tri-horário "
               "é uma **estimativa**.", icon=":material/warning:")
simples_fixo = melhor["opcao"] == "simples" and melhor["modalidade"] == "fixo"
if simples_fixo:
    # sem fatura não sabemos que contrato a pessoa tem («simples» e «fixo» são só os valores por omissão)
    ja_tem = p.get("da_fatura") and p.get("opcao") == "simples" and p.get("modalidade") == "fixo"
    if ja_tem:
        fim = ": não precisas de mudar."
    elif p.get("da_fatura"):
        fim = ". Tens outro horário ou um contrato indexado: mudar para este pode compensar."
    else:
        fim = (". Se já o tens, não precisas de mudar. Se tens outro horário ou um contrato indexado, "
               "mudar para este pode compensar.")
    st.success("Com estes números, o mais barato é o **Simples com preço fixo** (o mesmo preço a qualquer "
               "hora)" + fim, icon=":material/check_circle:")
else:
    st.success(f"Com estes números, o mais barato é o **{_nome(melhor)}**: pagarias "
               f"**{ui.euros(melhor['total'])} €** em {dias} dias, menos "
               f"**{ui.euros(melhor['poupanca_vs_simples_fixo'])} €** do que no Simples com preço fixo.",
               icon=":material/savings:")
metricas = [
    ui.metrica("A opção mais barata", _nome(melhor), ""),
    ui.metrica("Pagarias", ui.euros(melhor["total"]), f"€ em {dias} dias", destaque=True),
]
if not simples_fixo:
    metricas.append(ui.metrica("Poupas em relação ao Simples com preço fixo",
                               ui.euros(melhor["poupanca_vs_simples_fixo"]), "€"))
ui.grelha(metricas, largura_min=170)
if p.get("com_impostos"):
    ci = impostos.com_impostos(melhor["energia"], melhor["potencia"], consumo, dias, kva,
                               p.get("familia_numerosa", False))
    ui.nota(f"Com IVA e taxas, a opção mais barata fica em cerca de {ui.euros(ci['total'])} €.")

ui.texto("**O custo de cada opção**, da mais barata para a mais cara")
st.plotly_chart(grafico_opcoes(linhas, altura=320, dias=dias), config=CONFIG, width="stretch")
ui.nota("Cada barra junta a energia que gastas e a parte fixa (potência), que é igual em todas as opções. "
           "O número no fim da barra é o total.")
with st.expander("Ver as contas de todas as opções", icon=":material/table:"):
    tabela = pd.DataFrame([{
        "Opção": f"{periodos.NOMES[l['opcao']]} · "
                 + ("preço fixo" if l["modalidade"] == "fixo" else "indexado"),
        "Energia gasta (€)": l["energia"], "Parte fixa (€)": l["potencia"], "Total (€)": l["total"],
        "Em relação ao Simples com preço fixo": _diferenca(l["poupanca_vs_simples_fixo"]),
    } for l in linhas])
    st.table(ui.tabela_formatada(tabela), hide_index=True)
if medias is not None:
    ui.nota(f"Como fizemos as contas: «preço fixo» usa os preços oficiais da ERSE de {tarifa['ano']} para "
               f"{_kva(kva)} kVA, não os da tua empresa; «indexado» usa o preço médio do mercado nos últimos "
               f"{info['dias']} dias, mais as perdas e a margem que puseste. A parte fixa (potência) é igual em "
               "todas.")
else:
    ui.nota(f"Como fizemos as contas: «preço fixo» usa os preços oficiais da ERSE de {tarifa['ano']} para "
               f"{_kva(kva)} kVA, não os da tua empresa. Agora não consigo ir buscar os preços do mercado: só "
               "aparecem as opções de preço fixo.")

# ---------- 3. as horas de cada período
st.write("")
st.subheader(":material/schedule: 3. A que horas é mais barato")
ui.texto("**Agora mesmo**, para quem tem bi-horário ou tri-horário:")
ui.periodo_atual()

blocos = [
    f'<div class="lc-card"><span class="lc-n">BI-HORÁRIO · TODO O ANO</span><h4>Vazio · mais barato</h4>'
    f'<p>{periodos.texto_intervalos("bi", "vazio")}</p><h4>Fora de vazio · preço normal</h4>'
    f'<p>{periodos.texto_intervalos("bi", "fora_vazio")}</p></div>',
]
for nome_epoca, rotulo in (("inverno", "INVERNO · FIM DE OUTUBRO A FIM DE MARÇO"),
                           ("verao", "VERÃO · FIM DE MARÇO A FIM DE OUTUBRO")):
    atual = " · agora" if nome_epoca == estacao else ""
    blocos.append(
        f'<div class="lc-card"><span class="lc-n">TRI-HORÁRIO · {rotulo}{escape(atual.upper())}</span>'
        f'<h4>Ponta · mais caro</h4><p>{periodos.texto_intervalos("tri", "ponta", nome_epoca)}</p>'
        f'<h4>Cheias · preço intermédio</h4><p>{periodos.texto_intervalos("tri", "cheias", nome_epoca)}</p>'
        f'<h4>Vazio · mais barato</h4><p>{periodos.texto_intervalos("tri", "vazio", nome_epoca)}</p></div>')
ui.grelha(blocos, largura_min=220)
ui.nota("Estes horários são iguais todos os dias, também ao fim de semana: é o «ciclo diário», o mais comum "
           "nas casas. O inverno e o verão mudam quando se muda a hora. Se a tua fatura diz «ciclo semanal», "
           "as horas são outras.")
