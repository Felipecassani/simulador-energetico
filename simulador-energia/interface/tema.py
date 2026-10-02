"""Seletor de tema com 3 estados: claro, sistema e escuro (fixo no canto).

O Streamlit guarda a escolha de tema no browser (localStorage), uma entrada por
página: "stActiveTheme-<caminho>-v2", com o valor "Light", "Dark" ou "System".
O seletor grava a escolha em todas as páginas, cobre o ecrã com um círculo da cor
nova (a partir do botão) e recarrega. Recarregar abre uma sessão nova, por isso os
campos voltam aos valores iniciais (não passamos dados pessoais pelo endereço).
"""
import base64
import json

import streamlit as st

from interface.estilo import PALETAS

_SOL = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2'
        'M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>')
_ECRA = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="2.5"/>'
         '<path d="M8.5 20h7M12 16v4"/></svg>')
_LUA = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linejoin="round"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7z"/></svg>')

ESTADOS = [("Light", "Claro", _SOL), ("System", "Igual ao sistema", _ECRA), ("Dark", "Escuro", _LUA)]

_HTML = """
<div class="lc-tema" id="lc-tema" role="radiogroup" aria-label="Tema do site" data-estado="System">
  <span class="lc-tema-ind" aria-hidden="true"></span>
  {botoes}
</div>
<script>
(function () {{
  const chaves = {chaves};
  const fundos = {fundos};
  const icones = {icones};
  const grupo = document.getElementById("lc-tema");
  if (!grupo) return;
  // o st.html retira os svg (mesmo dentro do script): vêm em base64 e entram aqui
  grupo.querySelectorAll("button").forEach(b => {{ if (!b.innerHTML.trim()) b.innerHTML = atob(icones[b.dataset.estado]); }});
  const atual = (() => {{
    try {{ return JSON.parse(localStorage.getItem("stActiveTheme-" + location.pathname + "-v2")) || "System"; }}
    catch (e) {{ return "System"; }}
  }})();
  const marcar = (estado) => {{
    grupo.dataset.estado = estado;
    grupo.querySelectorAll("button").forEach(b => b.setAttribute("aria-checked", b.dataset.estado === estado));
  }};
  marcar(atual);
  grupo.querySelectorAll("button").forEach(b => b.onclick = () => {{
    const estado = b.dataset.estado;
    if (estado === grupo.dataset.estado) return;
    marcar(estado);
    try {{ chaves.forEach(k => localStorage.setItem(k, JSON.stringify(estado))); }} catch (e) {{}}
    const escuro = estado === "Dark" || (estado === "System" && matchMedia("(prefers-color-scheme: dark)").matches);
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) {{ location.reload(); return; }}
    const r = b.getBoundingClientRect();
    const x = r.left + r.width / 2, y = r.top + r.height / 2;
    const veu = document.createElement("div");
    veu.style.cssText = "position:fixed;inset:0;z-index:1000002;pointer-events:none;" +
      "background:" + (escuro ? fundos.dark : fundos.light) + ";" +
      "clip-path:circle(0px at " + x + "px " + y + "px);transition:clip-path .5s cubic-bezier(.65,0,.35,1)";
    document.body.appendChild(veu);
    requestAnimationFrame(() => requestAnimationFrame(() => {{
      veu.style.clipPath = "circle(150vmax at " + x + "px " + y + "px)";
    }}));
    setTimeout(() => location.reload(), 520);
  }});
}})();
</script>
"""


def seletor_tema(caminhos):
    """Mostra o seletor no canto superior direito. `caminhos`: url de cada página."""
    botoes = "".join(
        f'<button type="button" role="radio" aria-checked="false" data-estado="{estado}" '
        f'title="Tema: {nome.lower()}" aria-label="Tema: {nome.lower()}"></button>'
        for estado, nome, _ in ESTADOS)
    html = _HTML.format(
        botoes=botoes,
        chaves=json.dumps([f"stActiveTheme-{c}-v2" for c in caminhos]),
        fundos=json.dumps({t: p["bg"] for t, p in PALETAS.items()}),
        icones=json.dumps({estado: base64.b64encode(icone.encode()).decode() for estado, _, icone in ESTADOS}))
    with st.container(key="tema_mosaico"):          # fixo no canto (CSS em estilo.py)
        st.html(html, unsafe_allow_javascript=True)
