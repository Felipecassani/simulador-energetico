"""Palavra-passe para quem entra de fora (link público do Tailscale Funnel).

Em localhost (o próprio Mac) o site abre sem pedir nada. De fora, pede a palavra-passe que está
em .streamlit/secrets.toml ([acesso] senha = "..."); no Streamlit Cloud, em Settings › Secrets.
Sem palavra-passe configurada, o acesso de fora fica fechado (falha fechada); para o abrir sem
palavra-passe é preciso dizê-lo de propósito: [acesso] exigir = false. Esse ficheiro nunca vai para o repositório (.gitignore).
A sessão fica autorizada até a página ser recarregada.
"""
import hmac
import time

import streamlit as st

LOCAIS = {"localhost", "127.0.0.1", "[::1]", "::1"}
TENTATIVAS_SEM_ESPERA = 3


def anfitriao(headers):
    """Nome do anfitrião pedido (sem a porta), em minúsculas."""
    host = (headers.get("Host") or headers.get("host") or "").strip().lower()
    if host.startswith("["):                     # IPv6: [::1]:8501
        return host.split("]")[0] + "]"
    return host.split(":")[0]


PROXY = ("x-forwarded-for", "x-forwarded-host", "tailscale-funnel-request")


def vem_de_fora(headers):
    """True se o pedido não chegou direto por localhost (ex.: pelo link do Funnel).

    Dois sinais: o anfitrião pedido (o Funnel mantém o nome público) e os cabeçalhos que um
    proxy acrescenta (X-Forwarded-For…), que nunca existem num acesso direto ao Mac.
    """
    nomes = {k.lower() for k in headers}
    if any(p in nomes for p in PROXY):
        return True
    host = anfitriao(headers)
    return bool(host) and host not in LOCAIS


def senha_certa(tentativa, senha):
    """Comparação em tempo constante (não deixa adivinhar letra a letra pelo tempo de resposta)."""
    return bool(senha) and hmac.compare_digest(tentativa.encode(), senha.encode())


def _acesso():
    try:
        return dict(st.secrets["acesso"])
    except Exception:                            # sem secrets.toml ou sem a secção [acesso]
        return {}


def _senha_configurada():
    return _acesso().get("senha")


def exigir_senha():
    """Para a página aqui se quem vem de fora ainda não deu a palavra-passe."""
    if st.session_state.get("acesso_ok") or not vem_de_fora(st.context.headers):
        return
    if _acesso().get("exigir") is False:         # ex.: app privada no Streamlit Cloud (já pede login)
        return
    senha = _senha_configurada()
    st.html('<section class="lc-hero"><div class="lc-kicker">Acesso de teste</div>'
            '<h1>Simulador Energético</h1><p>Este site está em testes. Escreve a palavra-passe que '
            'recebeste para entrar.</p></section>')
    if not senha:
        st.error("O acesso de fora está fechado neste momento.", icon=":material/lock:")
        st.stop()
    with st.form("acesso", border=True):
        tentativa = st.text_input("Palavra-passe", type="password")
        entrar = st.form_submit_button("Entrar", icon=":material/lock_open:", type="primary")
    if entrar:
        falhas = st.session_state.get("acesso_falhas", 0)
        if falhas >= TENTATIVAS_SEM_ESPERA:
            time.sleep(min(30, 2 ** (falhas - TENTATIVAS_SEM_ESPERA + 1)))   # trava tentativas em série
        if senha_certa(tentativa, senha):
            st.session_state["acesso_ok"] = True
            st.session_state.pop("acesso_falhas", None)
            st.rerun()
        st.session_state["acesso_falhas"] = falhas + 1
        st.error("Palavra-passe errada.", icon=":material/error:")
    st.caption("Nada do que carregares fica guardado: as faturas são lidas só em memória.")
    st.stop()
