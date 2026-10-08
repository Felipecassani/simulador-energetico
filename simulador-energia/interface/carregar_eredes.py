"""Carregar os consumos da E-REDES (um ou vários ficheiros) e pôr os dados em todas as ferramentas.

Ao carregar, a repartição real (vazio e ponta) passa logo para o perfil; o consumo e os dias do
ficheiro só substituem os da fatura se a pessoa pedir (são períodos diferentes).
Os ficheiros são lidos só nesse momento (no servidor, em memória) e não ficam guardados.
"""
import pandas as pd
import streamlit as st

from interface import componentes as ui
from interface import perfil as pf
from interface.dados import omie_recente
from nucleo import eredes, periodos


MAX_FICHEIROS = 24          # um ano em ficheiros mensais, com folga para repetidos


def _juntar(ficheiros):
    """Lê os ficheiros e junta os quartos de hora (sem repetidos): (registos, falhados, estimados)."""
    por_instante, falhados, estimados = {}, [], 0
    for f in ficheiros[:MAX_FICHEIROS]:
        try:
            registos, n = eredes.ler_com_estimados(f.name, f.getvalue())
            por_instante.update(dict(registos))
            estimados += n
        except Exception:  # formato desconhecido, ficheiro grande demais
            falhados.append(f.name)
    return sorted(por_instante.items()), falhados, estimados


def secao(prefixo):
    """Expander com o envio dos ficheiros e o resumo. `prefixo` separa as keys de cada página."""
    analise = st.session_state.get("eredes_analise")
    with st.expander("Opcional · Consumos do contador inteligente (E-REDES)" + (" · em uso" if analise else ""),
                     icon=":material/upload_file:", expanded=False):
        st.caption("Podes saltar esta parte. A E-REDES é a empresa dos contadores e da rede, não é quem te vende "
                   "a luz. Se tens contador inteligente, entra no Balcão Digital da E-REDES "
                   "(balcaodigital.e-redes.pt), descarrega os teus consumos em Excel e carrega o ficheiro aqui: "
                   "o simulador fica a saber a que horas gastas. Podes juntar até um ano, um ficheiro por mês, "
                   "e ver o teu ano em «O teu ano», na ferramenta «A minha fatura». Os ficheiros são lidos só "
                   "neste momento e não ficam guardados.")
        if prefixo != "f":                          # na própria «A minha fatura» a ligação não faz falta
            st.page_link("paginas/fatura.py", label="Abrir «A minha fatura»", icon=":material/receipt_long:")
        ficheiros = st.file_uploader("Escolhe os ficheiros da E-REDES (Excel ou CSV)", type=["xlsx", "csv"],
                                     accept_multiple_files=True, key=f"{prefixo}_eredes",
                                     help="Carrega no botão «Escolher ficheiro» e escolhe os ficheiros que "
                                          "descarregaste do Balcão Digital da E-REDES. Podes escolher vários "
                                          "de uma vez.")
        if len(ficheiros) > MAX_FICHEIROS:
            st.info(f"Carregaste {len(ficheiros)} ficheiros: leio os primeiros {MAX_FICHEIROS}.", icon=":material/info:")
        assinatura = tuple(sorted(f.file_id for f in ficheiros)) if ficheiros else None
        if ficheiros and assinatura == st.session_state.get("eredes_ignorados"):
            st.caption("Deixaste de usar estes ficheiros. Para voltares a usar os consumos da E-REDES, tira-os "
                       "da caixa e carrega-os de novo, ou carrega outros.")
        elif ficheiros:
            if st.session_state.get("eredes_assinatura") != assinatura:
                registos, falhados, estimados = _juntar(ficheiros)
                st.session_state["eredes_assinatura"] = assinatura
                st.session_state["eredes_falhados"] = falhados
                if registos:
                    analise = eredes.analisar(registos)
                    st.session_state["eredes_analise"] = analise
                    st.session_state["eredes_registos"] = registos
                    st.session_state["eredes_estimados"] = estimados
                    st.session_state["eredes_padroes"] = eredes.padroes(registos)   # para "O teu ano"
                    # a repartição real passa já para todas as ferramentas
                    pf.aplicar(pct_vazio=round(analise["pct_vazio"], 1),
                               pct_ponta=round(analise["pct_ponta"], 1),
                               perfil_da_fatura=True, ponta_na_fatura=True)
                    st.rerun()
        for nome in st.session_state.get("eredes_falhados", []):
            st.warning(f"Não consegui ler {ui.nome_ficheiro(nome)}. Confirma que é o ficheiro de consumos que "
                       "descarregaste do Balcão Digital da E-REDES.", icon=":material/error:")
        if analise:
            _resumo(analise, prefixo)


def _resumo(analise, prefixo):
    kva_atual = pf.perfil()["kva"]
    kva_texto = f"{float(kva_atual):g}".replace(".", ",")
    horas_baratas = f"das {periodos.VAZIO_INICIO.hour}h às {periodos.VAZIO_FIM.hour}h"
    st.success(f"Pronto: já sei a que horas gastas. {ui.numero(analise['pct_vazio'])} % do consumo é no vazio "
               f"({horas_baratas}, as horas mais baratas) e {ui.numero(analise['pct_ponta'])} % na ponta (as horas "
               "mais caras). Todas as ferramentas passam a usar estes valores.", icon=":material/task_alt:")
    ui.grelha([
        ui.metrica("Eletricidade gasta", ui.numero(analise["total_kwh"]), f"kWh em {analise['dias']} dias"),
        ui.metrica("Nas horas baratas (vazio)", ui.numero(analise["pct_vazio"]), "%"),
        ui.metrica("Nas horas mais caras (ponta)", ui.numero(analise["pct_ponta"]), "%"),
        ui.metrica("Maior consumo de uma vez", ui.numero(analise["pico_kw"], 1), "kW"),
    ], largura_min=150)
    grafico = pd.DataFrame({"Hora": [f"{h:02d}h" for h in range(24)], "kWh por dia": analise["media_por_hora"]})
    st.bar_chart(grafico, x="Hora", y="kWh por dia", height=200, color="#C8283C")
    st.caption(f"Quanto gastas, em média, em cada hora do dia, de {analise['inicio']:%d/%m} a "
               f"{analise['fim']:%d/%m/%Y}.")
    estimados = st.session_state.get("eredes_estimados", 0)
    if estimados:
        st.caption(f"Atenção: {estimados} dos valores do ficheiro são estimados pela E-REDES, não lidos no contador.")
    if analise["pico_kw"] < 0.5 * kva_atual:
        st.info(f"O teu maior consumo de uma vez foi {ui.numero(analise['pico_kw'], 1)} kW, menos de metade dos "
                f"{kva_texto} kVA contratados: talvez possas baixar a potência. Deixa alguma folga: os picos "
                "muito curtos (forno, chaleira) não aparecem nestes ficheiros.", icon=":material/bolt:")
    registos = st.session_state.get("eredes_registos")
    mercado_er = omie_recente(analise["fim"], min(31, (analise["fim"] - analise["inicio"]).days + 1))
    if registos and mercado_er is not None:
        pond = eredes.preco_ponderado(registos, mercado_er[0])
        if pond:
            ajuda = pond["ponderado"] < pond["simples"]
            st.caption(f"Só para tarifários indexados que cobram cada quarto de hora ao preço do mercado: com o "
                       f"teu consumo, pagarias em média {ui.numero(pond['ponderado'] / 10, 2)} cêntimos por kWh "
                       f"pela parte do mercado. A média do mercado nesses dias foi "
                       f"{ui.numero(pond['simples'] / 10, 2)} cêntimos: as horas em que gastas são "
                       f"{'mais baratas' if ajuda else 'mais caras'} do que a média.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Usar o consumo e os dias deste ficheiro em vez dos da fatura", key=f"{prefixo}_eredes_consumo",
                     icon=":material/sync:",
                     help="Troca a eletricidade gasta e os dias da fatura pelos dos ficheiros da E-REDES."):
            pf.aplicar(consumo_kwh=round(analise["total_kwh"], 1), dias=int(analise["dias"]))
            st.rerun()
    with c2:
        if st.button("Deixar de usar estes ficheiros", key=f"{prefixo}_eredes_limpar",
                     icon=":material/close:"):
            # os ficheiros podem continuar na caixa: ficam postos de parte até mudarem
            st.session_state["eredes_ignorados"] = st.session_state.get("eredes_assinatura")
            for k in ("eredes_analise", "eredes_registos", "eredes_assinatura", "eredes_falhados",
                      "eredes_estimados", "eredes_padroes"):
                st.session_state.pop(k, None)
            # a repartição real sai do perfil; a Fatura volta a pôr a da fatura mais recente (se houver)
            pf.aplicar(pct_vazio=pf.PADRAO["pct_vazio"], pct_ponta=pf.PADRAO["pct_ponta"],
                       perfil_da_fatura=False, ponta_na_fatura=True)
            st.session_state.pop("fatura_principal", None)
            st.rerun()
