"""Ferramenta 4 — «Preço hora a hora»: o mercado hora a hora, as opções horárias e os tarifários.

Para qualquer pessoa: três secções numeradas, cada uma diz primeiro a quem interessa e dá o
resultado numa frase. Os avisos que mudam a decisão (só para indexados, estimativa, sem IVA)
aparecem antes dos gráficos, não numa legenda no fim.
"""
import re
from datetime import datetime

import streamlit as st

from interface import componentes as ui
from interface import perfil as pf
from interface.dados import erse, medias_omie, omie_hoje_e_amanha
from interface.graficos import (CONFIG, grafico_consumo, grafico_omie, grafico_opcoes,
                                grafico_tarifarios)
from nucleo import calculos, mercado, periodos, roteiro, tarifas

NOITE = f"das {periodos.VAZIO_INICIO.hour}h às {periodos.VAZIO_FIM.hour}h"
CONTRATO = "O teu contrato"
OFICIAL = "Preço oficial (tarifa regulada)"
MERCADO = "Preço do mercado (indexado)"
# nomes das colunas só na tabela mostrada (o núcleo e o gráfico usam os originais)
COLUNAS = {"Tarifário": "Contrato", "Energia (€)": "Energia gasta (€)", "Potência (€)": "Parte fixa (€)",
           "Diferença (€)": "A mais que o mais barato (€)"}


def _texto(texto):
    """Parágrafo com as palavras do glossário sublinhadas (toca para ver o que querem dizer) e **negrito**."""
    st.html("<p>" + re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", ui.com_glossario(texto)) + "</p>")


def _kva(kva):
    """6.9 → '6,9' e 3.45 → '3,45', como aparece na fatura."""
    return ui.numero(kva, 2).rstrip("0").rstrip(",")


def _hora(instante):
    return f"{instante.astimezone(periodos.LISBOA):%Hh%M}"


def _nome_opcao(linha):
    return (f"{periodos.NOMES[linha['opcao']]} "
            + ("com preço fixo" if linha["modalidade"] == "fixo" else "indexado (segue o mercado)"))


def _limpo(nome):
    """Nome escrito pela pessoa (ex.: uma oferta) sem marcas que o texto formatado interpretaria."""
    return re.sub(r"[`*_\[\]#<>!|~\\$]", " ", str(nome)).strip()


passo = roteiro.passo(4)
ui.cabecalho_ferramenta(passo, roteiro.disponivel(4))
ui.aviso_fatura(pf.perfil())
p = pf.perfil()
tarifa = erse()
indexado = p.get("modalidade") == "indexado"

ui.texto("Nesta página vês três coisas: **1.** a que horas a eletricidade está mais barata no "
            "mercado; **2.** quanto pagarias com cada tipo de horário; **3.** o teu contrato ao lado "
            "de outros preços.")
exemplo = not p.get("da_fatura") and all(p[k] == pf.PADRAO[k]
                                         for k in ("consumo_kwh", "dias", "kva", "pct_vazio"))
if exemplo:
    ui.texto(f"Nesta casa de exemplo, **{ui.numero(p['pct_vazio'])} %** do que se gasta é à noite, "
                f"{NOITE}, e a potência é **{_kva(p['kva'])} kVA**.")
else:
    ui.texto(f"As contas usam os teus números: gastas **{ui.numero(p['consumo_kwh'])} kWh em "
                f"{p['dias']} dias**, tens **{_kva(p['kva'])} kVA** de potência contratada e "
                f"**{ui.numero(p['pct_vazio'])} %** do que gastas é à noite, {NOITE}.")
st.page_link("paginas/bi_horario.py", label="Mudar estes números", icon=":material/edit:",
             help="Abre «Bi-horário compensa?», onde estão todos estes números.")

# ---------- 1. o preço do mercado, hora a hora
st.write("")
st.subheader("1. A que horas a eletricidade está mais barata no mercado")
if indexado:
    _texto("O teu contrato é **indexado**: o preço que pagas acompanha esta linha. Se o teu contrato cobrar "
           "cada hora ao preço do mercado, ligar as máquinas quando a linha está mais baixa faz baixar a tua "
           "conta.")
else:
    _texto("Esta linha é o preço a que as empresas compram a eletricidade em cada hora. **Só mexe na "
           "tua conta se o teu contrato for indexado** (procura esta palavra na fatura). Com preço fixo, "
           "o mais comum, pagas o mesmo por kWh a qualquer hora, ou menos à noite se tiveres bi-horário.")
try:
    hoje, amanha = omie_hoje_e_amanha()
except mercado.SemRede:
    st.info("Agora não consigo ir buscar os preços do mercado. O problema não é teu: tenta outra vez "
            "daqui a pouco.", icon=":material/wifi_off:")
else:
    barata = min(hoje, key=lambda x: x[1])
    cara = max(hoje, key=lambda x: x[1])
    ui.texto(f"Hoje, o preço mais baixo é às **{_hora(barata[0])}** ({ui.numero(barata[1] / 10, 2)} "
                f"cêntimos por kWh) e o mais alto às **{_hora(cara[0])}** "
                f"({ui.numero(cara[1] / 10, 2)} cêntimos por kWh). É o preço antes das redes, da margem e "
                "dos impostos: pagas sempre mais do que isto.")
    st.plotly_chart(grafico_omie(hoje, amanha), config=CONFIG, width="stretch")
    ui.nota(f"As faixas sombreadas com a palavra «vazio» são as horas {NOITE}, as mais baratas para quem tem bi-horário. No mercado, as "
               "horas mais baratas costumam ser a meio do dia, quando há muito sol, e de madrugada. "
               + ("A linha a tracejado é a de amanhã." if amanha
                  else "Os preços de amanhã saem por volta do meio-dia."))

    # as horas seguidas mais baratas (para pôr as máquinas a trabalhar)
    st.write("")
    ui.texto("**Quando ligar as máquinas** · as horas seguidas mais baratas do mercado")
    st.info("Isto só te poupa dinheiro se o teu contrato cobrar cada hora, ou cada 15 minutos, ao preço "
            "do mercado. Com preço fixo, ou com um indexado que usa a média do mês, a hora a que ligas as "
            f"máquinas não muda o preço. Aí o que conta é o vazio, {NOITE}, se tiveres bi-horário.",
            icon=":material/lightbulb:")
    horas = st.slider("Quantas horas demora o que queres ligar?", 1, 8, 3, key="g_janela", format="%d h",
                      help="Exemplos: máquina da loiça, cerca de 2 horas; máquina da roupa, 3 horas; "
                           "carregar um carro elétrico, 6 horas. Mostro-te as horas seguidas mais "
                           "baratas de hoje e de amanhã.")
    agora = datetime.now(periodos.LISBOA)
    cartoes = []
    for rotulo, precos, desde, sem_horas in (
            ("Hoje, a partir de agora", hoje, agora, "Hoje já não há tantas horas seguidas: vê amanhã"),
            ("Amanhã", amanha, None, "Os preços de amanhã saem por volta do meio-dia")):
        janela = mercado.melhor_janela(precos, horas, desde) if precos else None
        if janela:
            ini, fim, media = janela
            cartoes.append(ui.metrica(rotulo, f"{_hora(ini)} às {_hora(fim)}",
                                      f"preço médio: {ui.numero(media / 10, 2)} cêntimos por kWh"))
        else:
            cartoes.append(ui.metrica(rotulo, "—", sem_horas, vazio=True))
    ui.grelha(cartoes, largura_min=200)

# ---------- 2. quanto custa cada tipo de horário
st.write("")
st.subheader("2. Quanto pagarias com cada tipo de horário")
medias, _ = medias_omie(7)
perdas, margem = p.get("perdas_pct") or 0.0, p.get("margem_kwh") or 0.0
sem_margem = medias is not None and not perdas and not margem
linhas = tarifas.comparar_opcoes(p["consumo_kwh"], p["pct_vazio"], p["pct_ponta"], p["dias"],
                                 p["kva"], tarifa, medias_omie=medias,
                                 perdas_pct=perdas, margem_eur_kwh=margem)
st.info("Os valores em euros desta página ainda não têm IVA nem taxas, por isso são mais baixos do que "
        "a tua conta. Servem para comparar: o que aqui é mais barato quase sempre também o é com impostos.",
        icon=":material/receipt:")
avisos = []
ponta_estimada = p.get("perfil_da_fatura") and not p.get("ponta_na_fatura", True)
if not p.get("perfil_da_fatura"):
    avisos.append("A parte que gastas à noite e nas horas mais caras é uma **estimativa**. Confirma-a na "
                  "fatura ou com os consumos do teu contador.")
elif ponta_estimada:
    avisos.append("A tua fatura não diz quanto gastas nas horas mais caras (ponta): o resultado do "
                  "tri-horário é uma **estimativa**.")
if sem_margem:
    avisos.append("Nas opções «indexado» ainda faltam as **perdas e a margem** da empresa, que não "
                  "puseste: na prática ficam mais caras do que aqui.")
if avisos:
    st.warning("**Antes de mudares de contrato:**\n\n" + "\n".join(f"- {a}" for a in avisos),
               icon=":material/warning:")
    st.page_link("paginas/bi_horario.py", label="Acertar estes valores em «Bi-horário compensa?»",
                 icon=":material/tune:")

melhor = linhas[0]
referencia = next(l for l in linhas if l["opcao"] == "simples" and l["modalidade"] == "fixo")
if melhor is referencia:
    ui.texto(f"Com estes números, o mais barato é o **Simples com preço fixo**, o mais comum: cerca de "
                f"**{ui.euros(melhor['total'])} €** em {p['dias']} dias."
                + (" Mudar de horário não te compensa." if p.get("da_fatura") and p.get("opcao") == "simples"
                   and p.get("modalidade") == "fixo"
                   else " Tens outro horário ou um contrato indexado: mudar para este pode compensar."
                   if p.get("da_fatura")
                   else " Se já o tens, não precisas de mudar. Se tens outro horário ou um contrato indexado, "
                        "mudar para este pode compensar."))
else:
    ui.texto(f"Com estes números, o mais barato é o **{_nome_opcao(melhor)}**: cerca de "
                f"**{ui.euros(melhor['total'])} €** em {p['dias']} dias. O Simples com preço fixo, o mais "
                f"comum, custaria {ui.euros(referencia['total'])} €.")

esquerda, direita = st.columns([1.5, 1], gap="large")
with esquerda:
    ui.texto("**O custo de cada opção**, da mais barata para a mais cara")
    st.plotly_chart(grafico_opcoes(linhas, dias=p["dias"]), config=CONFIG, width="stretch")
    ui.nota("Cada barra junta a energia que gastas e a parte fixa (potência), que pagas todos os dias "
               "e é igual em todas as opções. O número no fim da barra é o total.")
with direita:
    ui.texto("**A que horas gastas a tua eletricidade**")
    consumos = tarifas.distribuir_consumo(p["consumo_kwh"], p["pct_vazio"], p["pct_ponta"])["tri"]
    st.plotly_chart(grafico_consumo(consumos, altura=340), config=CONFIG, width="stretch")
    ui.nota(("O que gastas à noite vem da tua fatura; a parte da ponta é uma estimativa. " if ponta_estimada
                else "Estas percentagens vêm da tua fatura ou do teu contador. " if p.get("perfil_da_fatura")
                else "Estas percentagens são uma estimativa: muda-as em «Bi-horário compensa?». ")
               + "Quanto mais gastas no vazio, mais te compensa o bi-horário.")

# ---------- 3. o contrato da pessoa ao lado de outros preços
st.write("")
st.subheader("3. O teu contrato ao lado de outros preços")
# recalculado sempre com os dados atuais (as ofertas vêm do perfil, preenchidas em «Comparar ofertas»)
fixos = tarifas.precos_fixos(tarifa, p["kva"])
potencia = tarifas.preco_potencia(tarifa, p["kva"])
oficial = fixos["simples"]["simples"]
lista = [{"nome": OFICIAL, "preco_energia": oficial, "preco_diario": potencia}]
igual_ao_oficial = (abs(p["preco_energia"] - oficial) < 1e-9 and abs(p["preco_diario"] - potencia) < 1e-9)
mostrar_contrato = bool(p.get("da_fatura")) or not igual_ao_oficial   # sem fatura seriam duas barras iguais
if mostrar_contrato:
    lista.append({"nome": CONTRATO, "preco_energia": p["preco_energia"], "preco_diario": p["preco_diario"]})
if medias is not None:
    preco_mercado = tarifas.precos_indexados(medias, tarifa, perdas, margem)["simples"]["simples"]
    lista.append({"nome": MERCADO, "preco_energia": preco_mercado, "preco_diario": potencia})
ofertas = 0
for i in range(3):
    if (p.get(f"oferta_{i}_energia") or 0) > 0:
        ofertas += 1
        lista.append({"nome": p.get(f"oferta_{i}_nome") or f"Oferta {'ABC'[i]}",
                      "preco_energia": p[f"oferta_{i}_energia"],
                      "preco_diario": p.get(f"oferta_{i}_potencia") or 0.0})
tabela = calculos.tabela_comparativa(calculos.comparar_tarifarios(p["consumo_kwh"], p["dias"], lista))

partes = ([CONTRATO.lower()] if mostrar_contrato else []) + ["o preço oficial da tarifa regulada"] \
    + (["o preço do mercado"] if medias is not None else []) \
    + (["as propostas que juntaste em «Comparar ofertas»"] if ofertas else [])
if len(partes) > 1:
    _texto("O mesmo consumo com preços diferentes: " + ", ".join(partes[:-1]) + " e " + partes[-1]
           + ". Aqui as contas usam um preço igual a qualquer hora, sem horários.")
if not mostrar_contrato:
    ui.nota("Ainda não puseste os preços do teu contrato: por agora são iguais ao preço oficial. "
               "Carrega a tua fatura em «A minha fatura» e o teu contrato aparece aqui.")

primeiro = tabela.iloc[0]
if len(tabela) == 1:
    frase = (f"Por agora só há um preço para comparar, o oficial da tarifa regulada: "
             f"**{ui.euros(primeiro['Total (€)'])} €** em {p['dias']} dias. Junta o teu contrato ou "
             "propostas de outras empresas para veres a diferença.")
elif mostrar_contrato and primeiro["Tarifário"] == CONTRATO:
    frase = (f"O teu contrato já é o mais barato desta lista: **{ui.euros(primeiro['Total (€)'])} €** "
             f"em {p['dias']} dias.")
else:
    frase = (f"O mais barato desta lista é «{_limpo(primeiro['Tarifário'])}»: "
             f"**{ui.euros(primeiro['Total (€)'])} €** em {p['dias']} dias.")
    if mostrar_contrato:
        dif = float(tabela.loc[tabela["Tarifário"] == CONTRATO, "Diferença (€)"].iloc[0])
        frase += (f" O teu contrato fica **{ui.euros(dif)} € acima**." if dif > 0.005
                  else " O teu contrato custa o mesmo.")
if primeiro["Tarifário"] == MERCADO and sem_margem:
    frase += (" Atenção: ao preço do mercado ainda faltam as perdas e a margem da empresa, por isso na "
              "prática fica mais caro.")
ui.texto(frase)
st.plotly_chart(grafico_tarifarios(tabela, dias=p["dias"]), config=CONFIG, width="stretch")
st.table(ui.tabela_formatada(tabela.rename(columns=COLUNAS)), hide_index=True)
if not ofertas:
    ui.nota("Recebeste propostas de outras empresas? Põe-nas em «Comparar ofertas» e aparecem aqui.")
    st.page_link("paginas/tarifarios.py", label="Juntar as propostas que recebi", icon=":material/add:")
ui.nota(f"De onde vêm os preços: tarifa oficial da ERSE de {tarifa['ano']}"
           + (" e preço médio do mercado na última semana." if medias is not None else "."))
