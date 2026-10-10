"""Palavra-passe opcional para quem abre o site de fora.

No meu computador (localhost) o site abre sem pedir nada. De fora, pede a palavra-passe guardada
em .streamlit/secrets.toml ([acesso] senha = "..."), que nunca vai para o repositório.
Se não houver palavra-passe, o acesso de fora fica fechado por defeito; para o abrir a todos
é preciso escrever [acesso] exigir = false (é o que o site público usa).
Depois de entrar, a sessão fica aberta até a página ser recarregada.
"""
import hmac
import threading
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
    """True se o pedido não chegou direto por localhost (por exemplo, através de um link público).

    Dois sinais: o anfitrião pedido (um link público mantém o seu nome) e os cabeçalhos que um
    proxy acrescenta (X-Forwarded-For…), que nunca existem num acesso direto ao computador.
    """
    nomes = {k.lower() for k in headers}
    if any(p in nomes for p in PROXY):
        return True
    host = anfitriao(headers)
    return bool(host) and host not in LOCAIS


JANELA = 15 * 60          # segundos
MAX_FALHAS_IP = 5          # por endereço, na janela
MAX_FALHAS_TOTAL = 40      # de todos os endereços juntos (quem troca de IP)


class Tentativas:
    """Falhas recentes partilhadas por todas as sessões do servidor (recarregar a página não apaga)."""

    def __init__(self):
        self.lock, self.por_ip = threading.Lock(), {}

    def _recentes(self, agora):
        for ip in list(self.por_ip):
            self.por_ip[ip] = [t for t in self.por_ip[ip] if agora - t < JANELA]
            if not self.por_ip[ip]:
                del self.por_ip[ip]

    def bloqueado(self, ip, agora=None):
        """Segundos até poder tentar outra vez (0 = pode)."""
        agora = time.time() if agora is None else agora
        with self.lock:
            self._recentes(agora)
            meus = self.por_ip.get(ip, [])
            todos = sorted(t for ts in self.por_ip.values() for t in ts)
            if len(meus) >= MAX_FALHAS_IP:
                return int(JANELA - (agora - meus[-MAX_FALHAS_IP])) + 1
            if len(todos) >= MAX_FALHAS_TOTAL:
                return int(JANELA - (agora - todos[-MAX_FALHAS_TOTAL])) + 1
            return 0

    def falhou(self, ip, agora=None):
        with self.lock:
            self.por_ip.setdefault(ip, []).append(time.time() if agora is None else agora)

    def acertou(self, ip):
        with self.lock:
            self.por_ip.pop(ip, None)


@st.cache_resource
def _tentativas():
    return Tentativas()


def ip_de(headers):
    """Endereço de quem pede (o 1.º do X-Forwarded-For, no Cloud); "local" sem proxy."""
    xff = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for") or ""
    return xff.split(",")[0].strip() or "local"


def senha_certa(tentativa, senha):
    """Comparação em tempo constante (não deixa adivinhar letra a letra pelo tempo de resposta)."""
    return bool(senha) and hmac.compare_digest(tentativa.encode(), senha.encode())


def _acesso():
    """Secção [acesso] dos segredos (aceita "Acesso": o Safari pode pôr maiúscula ao colar)."""
    try:
        for chave in st.secrets:
            if chave.lower() == "acesso":
                return {k.lower(): v for k, v in dict(st.secrets[chave]).items()}
    except Exception:                            # sem secrets.toml
        pass
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
        registo, ip = _tentativas(), ip_de(st.context.headers)
        espera = registo.bloqueado(ip)
        if espera:
            st.error(f"Demasiadas tentativas erradas. Tenta outra vez daqui a {espera // 60 + 1} minutos.",
                     icon=":material/lock_clock:")
            st.stop()
        falhas = st.session_state.get("acesso_falhas", 0)
        if falhas >= TENTATIVAS_SEM_ESPERA:
            time.sleep(min(30, 2 ** (falhas - TENTATIVAS_SEM_ESPERA + 1)))   # trava tentativas em série
        if senha_certa(tentativa, senha):
            registo.acertou(ip)
            st.session_state["acesso_ok"] = True
            st.session_state.pop("acesso_falhas", None)
            st.rerun()
        registo.falhou(ip)
        st.session_state["acesso_falhas"] = falhas + 1
        st.error("Palavra-passe errada.", icon=":material/error:")
    st.caption("Nada do que carregares fica guardado: as faturas são lidas só em memória.")
    st.stop()
