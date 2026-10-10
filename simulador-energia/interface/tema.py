"""Botão de tema (fixo no canto): cada clique alterna entre claro e escuro.

Um só botão ocupa menos espaço do que três (no telemóvel cabe o logótipo com o nome). O ícone
mostra para onde se vai: lua no tema claro («mudar para escuro»), sol no escuro.

O Streamlit guarda a escolha de tema no browser (localStorage), uma entrada por
página: "stActiveTheme-<caminho>-v2", com o valor "Light" ou "Dark". O caminho é
o do browser, por isso no Streamlit Cloud leva o prefixo "/~/+" (descoberto no próprio browser).
O botão grava a escolha em todas as páginas, cobre o ecrã com um círculo da cor
nova (a partir do botão) e recarrega. Recarregar abre uma sessão nova, por isso os
campos voltam aos valores iniciais (não passamos dados pessoais pelo endereço).
"""
import base64
import json

import streamlit as st

from interface.estilo import PALETAS, tema_atual

_SOL = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2'
        'M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>')
_LUA = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linejoin="round"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7z"/></svg>')

_HTML = """
<button type="button" class="lc-tema" id="lc-tema" title="{rotulo}" aria-label="{rotulo}"><span class="lc-tema-txt">{texto}</span></button>
<script>
(function () {{
  // no Streamlit Cloud a app corre em /~/+/(página): o prefixo é o que sobra do endereço
  // depois de tirar o caminho da página (o mais comprido que encaixa; "/" encaixa sempre)
  const caminhos = {caminhos};
  const pagina = caminhos.filter(c => location.pathname.endsWith(c)).sort((a, b) => b.length - a.length)[0] || "/";
  const prefixo = location.pathname.slice(0, location.pathname.length - pagina.length);
  const chaves = caminhos.map(c => "stActiveTheme-" + prefixo + c + "-v2");
  const fundos = {fundos};
  const escuro = {escuro};                 // o tema que está à vista agora (vem do Streamlit)
  const botao = document.getElementById("lc-tema");
  if (!botao) return;
  // o st.html retira os svg (mesmo dentro do script): vêm em base64 e entram aqui
  if (!botao.querySelector("svg")) botao.insertAdjacentHTML("afterbegin", atob(escuro ? "{sol}" : "{lua}"));
  botao.onclick = () => {{
    const novo = escuro ? "Light" : "Dark";
    try {{ chaves.forEach(k => localStorage.setItem(k, JSON.stringify(novo))); }} catch (e) {{}}
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) {{ location.reload(); return; }}
    const r = botao.getBoundingClientRect();
    const x = r.left + r.width / 2, y = r.top + r.height / 2;
    const veu = document.createElement("div");
    veu.style.cssText = "position:fixed;inset:0;z-index:1000002;pointer-events:none;" +
      "background:" + (escuro ? fundos.light : fundos.dark) + ";" +
      "clip-path:circle(0px at " + x + "px " + y + "px);transition:clip-path .5s cubic-bezier(.65,0,.35,1)";
    document.body.appendChild(veu);
    requestAnimationFrame(() => requestAnimationFrame(() => {{
      veu.style.clipPath = "circle(150vmax at " + x + "px " + y + "px)";
    }}));
    setTimeout(() => location.reload(), 520);
  }};
}})();
</script>
"""


def seletor_tema(caminhos):
    """Mostra o botão de tema no canto superior direito. `caminhos`: url de cada página."""
    escuro = tema_atual() == "dark"
    html = _HTML.format(
        rotulo="Mudar para o tema claro" if escuro else "Mudar para o tema escuro",
        texto="Claro" if escuro else "Escuro",
        caminhos=json.dumps(list(caminhos)),
        fundos=json.dumps({t: p["bg"] for t, p in PALETAS.items()}),
        escuro="true" if escuro else "false",
        sol=base64.b64encode(_SOL.encode()).decode(),
        lua=base64.b64encode(_LUA.encode()).decode())
    with st.container(key="tema_mosaico"):          # fixo no canto (CSS em estilo.py)
        st.html(html, unsafe_allow_javascript=True)
