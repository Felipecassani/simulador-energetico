"""Ferramenta 4 — Gráficos: mercado, opções horárias, consumo e tarifários."""
import streamlit as st

from interface import componentes as ui
from interface import perfil as pf
from interface.dados import erse, medias_omie, omie_hoje_e_amanha
from interface.graficos import (CONFIG, grafico_consumo, grafico_omie, grafico_opcoes,
                                grafico_tarifarios)
from datetime import datetime

from nucleo import calculos, mercado, periodos, roteiro, tarifas

passo = roteiro.passo(4)
ui.cabecalho_ferramenta(passo, roteiro.disponivel(4))
ui.aviso_fatura(pf.perfil())
p = pf.perfil()
tarifa = erse()
st.caption(f"Com os teus dados: {ui.numero(p['consumo_kwh'])} kWh em {p['dias']} dias, "
           f"{ui.numero(p['kva'], 2)} kVA, {ui.numero(p['pct_vazio'])} % em vazio "
           f"(muda-os na Fatura ou em Opções horárias).")

# ---------- 1. preço hora a hora
st.subheader("O preço da eletricidade, hora a hora")
try:
    hoje, amanha = omie_hoje_e_amanha()
except mercado.SemRede:
    st.info("Sem ligação ao OMIE agora: este gráfico volta quando houver rede.",
            icon=":material/wifi_off:")
else:
    st.plotly_chart(grafico_omie(hoje, amanha), config=CONFIG, width="stretch")
    st.caption("Mercado grossista OMIE em Portugal (antes de redes, margem e impostos). A faixa "
               "dourada é o vazio, o período mais barato das tarifas bi e tri-horárias; no mercado, as "
               "horas mais baratas são muitas vezes a meio do dia (solar) e de madrugada.")

    # melhor janela: as horas seguidas mais baratas
    st.write("")
    st.markdown("**A melhor janela** · as horas seguidas mais baratas no mercado")
    horas = st.slider("Quantas horas seguidas precisas?", 1, 8, 3, key="g_janela",
                      help="Por exemplo: 2 h para a máquina da loiça, 3 h para a roupa, 6 h para o carro.")
    agora = datetime.now(periodos.LISBOA)
    cartoes = []
    for rotulo, precos, desde in (("Hoje (a partir de agora)", hoje, agora), ("Amanhã", amanha, None)):
        janela = mercado.melhor_janela(precos, horas, desde) if precos else None
        if janela:
            ini, fim, media = janela
            cartoes.append(ui.metrica(rotulo, f"{ini.astimezone(periodos.LISBOA):%Hh%M}–"
                                              f"{fim.astimezone(periodos.LISBOA):%Hh%M}",
                                      f"média {ui.numero(media / 10, 2)} c€/kWh"))
        else:
            cartoes.append(ui.metrica(rotulo, "—", "ainda sem preços" if precos is None else
                                      "já não há horas suficientes hoje", vazio=True))
    ui.grelha(cartoes, largura_min=200)
    st.caption("Só faz diferença no preço se o teu tarifário for indexado à hora ou ao quarto de hora; "
               "em preço fixo ou indexado à média do mês, o que conta são os períodos da tua opção horária.")

# ---------- 2. custo de cada opção
st.write("")
esquerda, direita = st.columns([1.5, 1], gap="large")
medias, _ = medias_omie(7)
linhas = tarifas.comparar_opcoes(p["consumo_kwh"], p["pct_vazio"], p["pct_ponta"], p["dias"],
                                 p["kva"], tarifa, medias_omie=medias,
                                 perdas_pct=p.get("perdas_pct") or 0.0,
                                 margem_eur_kwh=p.get("margem_kwh") or 0.0)
with esquerda:
    st.subheader("Quanto custa cada opção")
    st.plotly_chart(grafico_opcoes(linhas), config=CONFIG, width="stretch")
with direita:
    st.subheader("Onde vai o teu consumo")
    consumos = tarifas.distribuir_consumo(p["consumo_kwh"], p["pct_vazio"], p["pct_ponta"])["tri"]
    st.plotly_chart(grafico_consumo(consumos), config=CONFIG, width="stretch")

# ---------- 3. tarifários comparados
st.write("")
st.subheader("Os tarifários comparados")
# recalculado sempre com os dados atuais (as ofertas vêm do perfil, preenchidas em Tarifários)
fixos = tarifas.precos_fixos(tarifa, p["kva"])
potencia = tarifas.preco_potencia(tarifa, p["kva"])
lista = [{"nome": "Regulada ERSE · fixo", "preco_energia": fixos["simples"]["simples"],
          "preco_diario": potencia},
         {"nome": "A tua fatura", "preco_energia": p["preco_energia"],
          "preco_diario": p["preco_diario"]}]
if medias is not None:
    indexado = tarifas.precos_indexados(medias, tarifa, p.get("perdas_pct") or 0.0,
                                        p.get("margem_kwh") or 0.0)["simples"]["simples"]
    lista.append({"nome": "Indexado OMIE", "preco_energia": indexado, "preco_diario": potencia})
ofertas = 0
for i in range(3):
    if (p.get(f"oferta_{i}_energia") or 0) > 0:
        ofertas += 1
        lista.append({"nome": p.get(f"oferta_{i}_nome") or f"Oferta {'ABC'[i]}",
                      "preco_energia": p[f"oferta_{i}_energia"],
                      "preco_diario": p.get(f"oferta_{i}_potencia") or 0.0})
tabela = calculos.tabela_comparativa(calculos.comparar_tarifarios(p["consumo_kwh"], p["dias"], lista))
if not ofertas:
    st.caption("Acrescenta as tuas ofertas na ferramenta Tarifários para as veres aqui.")
st.plotly_chart(grafico_tarifarios(tabela), config=CONFIG, width="stretch")
st.dataframe(ui.tabela_formatada(tabela), hide_index=True, width="stretch")
st.caption(f"Fontes: tarifa regulada ERSE {tarifa['ano']} ({tarifa['origem']}) e mercado OMIE dos "
           "últimos 7 dias · valores sem IVA nem taxas.")
