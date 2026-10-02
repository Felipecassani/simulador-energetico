"""Dados oficiais com cache (OMIE e ERSE) para as páginas.

O OMIE atualiza uma vez por dia (o dia seguinte sai por volta das 12h de Lisboa);
guardamos 1 hora. A ERSE muda uma vez por ano; a leitura ao vivo do documento
oficial só acontece quando a pessoa carrega em "Verificar na ERSE".
"""
from datetime import date, datetime, timedelta

import streamlit as st

from nucleo import mercado, ofertas as of, tarifas


# As falhas também ficam em cache (10 min): sem isto, cada clique voltava a pedir à rede.
@st.cache_data(ttl=600, show_spinner=False)
def omie_dia(dia):
    """Preços OMIE de um dia, ou None se ainda não houver (ou não houver rede)."""
    try:
        return mercado.obter_omie(dia)
    except mercado.SemRede:
        return None


@st.cache_data(ttl=600, show_spinner=False)
def omie_recente(fim, dias):
    """(preços, dias em falta, hora) dos últimos `dias` dias até `fim`, ou None."""
    try:
        precos, falhados = mercado.obter_omie_varios(fim, dias)
    except mercado.SemRede:
        return None
    return precos, falhados, datetime.now().strftime("%H:%M")


def omie_hoje_e_amanha():
    """(preços de hoje, preços de amanhã ou None). Lança mercado.SemRede sem acesso."""
    hoje = date.today()
    precos_hoje = omie_dia(hoje)
    if precos_hoje is None:
        raise mercado.SemRede("OMIE indisponível")
    return precos_hoje, omie_dia(hoje + timedelta(days=1))


def medias_omie(dias=7):
    """Médias OMIE por período das opções horárias nos últimos dias, ou (None, None)."""
    resultado = omie_recente(date.today(), dias)
    if resultado is None:
        return None, None
    precos, falhados, hora = resultado
    return tarifas.medias_omie_por_periodo(precos), {"dias": dias, "falhados": falhados,
                                                     "hora": hora}


@st.cache_data(ttl=86400, show_spinner=False)
def _erse_online():
    return mercado.obter_erse_online()


def erse():
    """Tarifas ERSE: a versão lida ao vivo nesta sessão, se existir, senão a cópia local."""
    return st.session_state.get("erse_online") or mercado.carregar_erse_local()


def verificar_erse():
    """Lê o documento oficial agora. Devolve (dados, lista de preços que mudaram)."""
    online = _erse_online()
    mudancas = mercado.diferencas_erse(online, mercado.carregar_erse_local())
    st.session_state["erse_online"] = online
    return online, mudancas


@st.cache_data(show_spinner=False)
def _ofertas_de(caminho, _mudou):
    return of.ler_zip(open(caminho, "rb").read())


def ofertas_erse():
    """(ofertas, data do ficheiro) da cópia local mais recente; ([], None) se não houver."""
    caminho = of.ficheiro_local()
    if caminho is None:
        return [], None
    return _ofertas_de(str(caminho), caminho.stat().st_mtime), of.data_do_ficheiro(caminho)
