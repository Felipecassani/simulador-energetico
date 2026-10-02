"""Carregar os consumos da E-REDES (um ou vários ficheiros) e pôr os dados em todas as ferramentas.

Ao carregar, a repartição real (vazio e ponta) passa logo para o perfil; o consumo e os dias do
ficheiro só substituem os da fatura se a pessoa pedir (são períodos diferentes).
Os ficheiros são lidos em memória e não ficam guardados.
"""
import pandas as pd
import streamlit as st

from interface import componentes as ui
from interface import perfil as pf
from interface.dados import omie_recente
from nucleo import eredes


def _juntar(ficheiros):
    """Lê todos os ficheiros e junta os quartos de hora (sem repetidos)."""
    por_instante, falhados, estimados = {}, [], 0
    for f in ficheiros:
        try:
            por_instante.update(dict(eredes.ler(f.name, f.getvalue())))
            estimados += eredes.ler.estimados
        except Exception:  # formato desconhecido
            falhados.append(f.name)
    _juntar.estimados = estimados
    return sorted(por_instante.items()), falhados


def secao(prefixo):
    """Expander com o envio dos ficheiros e o resumo. `prefixo` separa as keys de cada página."""
    analise = st.session_state.get("eredes_analise")
    with st.expander("Contador inteligente? Carrega os consumos da E-REDES" + (" · em uso" if analise else ""),
                     icon=":material/upload_file:", expanded=False):
        st.caption("No Balcão Digital da E-REDES (balcaodigital.e-redes.pt) descarrega os consumos de 15 em "
                   "15 minutos, em Excel ou CSV. Podes carregar vários ficheiros (por exemplo, um por mês). "
                   "São lidos neste computador e não ficam guardados.")
        ficheiros = st.file_uploader("Ficheiros da E-REDES", type=["xlsx", "csv"], accept_multiple_files=True,
                                     key=f"{prefixo}_eredes", label_visibility="collapsed")
        if ficheiros:
            assinatura = tuple(sorted(f.file_id for f in ficheiros))
            if st.session_state.get("eredes_assinatura") != assinatura:
                registos, falhados = _juntar(ficheiros)
                st.session_state["eredes_assinatura"] = assinatura
                st.session_state["eredes_falhados"] = falhados
                if registos:
                    analise = eredes.analisar(registos)
                    st.session_state["eredes_analise"] = analise
                    st.session_state["eredes_registos"] = registos
                    st.session_state["eredes_estimados"] = _juntar.estimados
                    # a repartição real passa já para todas as ferramentas
                    pf.aplicar(pct_vazio=round(analise["pct_vazio"], 1),
                               pct_ponta=round(analise["pct_ponta"], 1),
                               perfil_da_fatura=True, ponta_na_fatura=True)
                    st.rerun()
        for nome in st.session_state.get("eredes_falhados", []):
            st.warning(f"Não consegui ler {nome}. Confirma que é o ficheiro dos consumos de 15 em 15 "
                       "minutos da E-REDES.", icon=":material/error:")
        if analise:
            _resumo(analise, prefixo)


def _resumo(analise, prefixo):
    kva_atual = pf.perfil()["kva"]
    st.success(f"A usar a tua repartição real em todas as ferramentas: {ui.numero(analise['pct_vazio'])} % "
               f"em vazio e {ui.numero(analise['pct_ponta'])} % em ponta.", icon=":material/task_alt:")
    ui.grelha([
        ui.metrica("Consumo", ui.numero(analise["total_kwh"]), f"kWh em {analise['dias']} dias"),
        ui.metrica("Em vazio", ui.numero(analise["pct_vazio"]), "%"),
        ui.metrica("Em ponta", ui.numero(analise["pct_ponta"]), "%"),
        ui.metrica("Pico", ui.numero(analise["pico_kw"], 1), "kW (média de 15 min)"),
    ], largura_min=150)
    grafico = pd.DataFrame({"Hora": [f"{h:02d}h" for h in range(24)], "kWh por dia": analise["media_por_hora"]})
    st.bar_chart(grafico, x="Hora", y="kWh por dia", height=200, color="#C8283C")
    st.caption(f"Consumo médio em cada hora do dia, de {analise['inicio']:%d/%m} a {analise['fim']:%d/%m/%Y}.")
    estimados = st.session_state.get("eredes_estimados", 0)
    if estimados:
        st.caption(f"Atenção: {estimados} dos valores do ficheiro são estimados pela E-REDES, não lidos no contador.")
    if analise["pico_kw"] < 0.5 * kva_atual:
        st.info(f"O teu maior pico foi {ui.numero(analise['pico_kw'], 1)} kW, menos de metade dos "
                f"{ui.numero(kva_atual, 2)} kVA contratados: talvez possas descer de potência. Os picos de "
                "segundos (forno, chaleira) não aparecem na média de 15 minutos, por isso deixa folga.",
                icon=":material/bolt:")
    registos = st.session_state.get("eredes_registos")
    mercado_er = omie_recente(analise["fim"], min(31, (analise["fim"] - analise["inicio"]).days + 1))
    if registos and mercado_er is not None:
        pond = eredes.preco_ponderado(registos, mercado_er[0])
        if pond:
            ajuda = pond["ponderado"] < pond["simples"]
            st.caption(f"No mercado desses dias, o teu consumo pagaria em média {ui.numero(pond['ponderado'] / 10, 2)} "
                       f"c€/kWh, contra {ui.numero(pond['simples'] / 10, 2)} c€/kWh da média simples: num indexado "
                       f"quarto-horário o teu perfil {'ajuda' if ajuda else 'não ajuda'}.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Usar também o consumo e os dias do ficheiro", key=f"{prefixo}_eredes_consumo",
                     icon=":material/sync:",
                     help="Substitui o consumo e os dias da fatura pelos do ficheiro da E-REDES."):
            pf.aplicar(consumo_kwh=round(analise["total_kwh"], 1), dias=int(analise["dias"]))
            st.rerun()
    with c2:
        if st.button("Deixar de usar os dados da E-REDES", key=f"{prefixo}_eredes_limpar",
                     icon=":material/close:"):
            for k in ("eredes_analise", "eredes_registos", "eredes_assinatura", "eredes_falhados",
                      "eredes_estimados"):
                st.session_state.pop(k, None)
            st.rerun()
