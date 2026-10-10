"""Animações que convidam a continuar: números que contam até ao valor, cartões que entram ao
descer a página. Um só script para o site inteiro (chamado em app.py).

Regras: o conteúdo nunca depende do script (sem ele, tudo aparece normalmente); quem pediu menos
movimento no sistema (prefers-reduced-motion) não vê animações; o texto do script não pode ter
"<" seguido de letra (o DOMPurify do st.html apagava-o — ver tests/test_app.py).
"""
import streamlit as st

_SCRIPT = """<script>
(function () {
  if (window.lcAnimar) { window.lcAnimar(); return; }
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) { window.lcAnimar = function () {}; return; }
  const ALVOS = ".lc-card, .lc-metric, .lc-realce, .lc-selo, [class*='st-key-cartao_']";

  function contar(el) {
    if (el.dataset.lcContado) return;
    const no = el.firstChild;
    if (!no || no.nodeType !== 3) return;
    const texto = no.nodeValue.trim();
    const limpo = texto.replace(/\\s/g, "").replace(",", ".");
    if (!/^[0-9.]+$/.test(limpo)) return;
    const alvo = parseFloat(limpo);
    if (isNaN(alvo) || alvo === 0) return;
    el.dataset.lcContado = "1";
    const casas = texto.includes(",") ? texto.split(",")[1].length : 0;
    const formato = (v) => v.toLocaleString("pt-PT", { minimumFractionDigits: casas, maximumFractionDigits: casas });
    const inicio = performance.now(), duracao = 1000;
    function passo(agora) {
      const p = Math.min(1, (agora - inicio) / duracao);
      no.nodeValue = formato(alvo * (1 - Math.pow(1 - p, 3)));
      if (p !== 1) requestAnimationFrame(passo); else no.nodeValue = texto;
    }
    requestAnimationFrame(passo);
  }

  const vigia = new IntersectionObserver((entradas) => {
    entradas.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add("lc-visto");
      e.target.querySelectorAll(".lc-value, .lc-relampago-res b").forEach(contar);
      vigia.unobserve(e.target);
    });
  }, { threshold: 0.15 });

  window.lcAnimar = function () {
    document.querySelectorAll(ALVOS).forEach((el) => {
      if (el.dataset.lcAnim) return;
      el.dataset.lcAnim = "1";
      const irmaos = el.parentElement ? Array.from(el.parentElement.children) : [];
      el.style.transitionDelay = Math.min(irmaos.indexOf(el), 6) * 70 + "ms";
      el.classList.add("lc-anim");
      vigia.observe(el);
    });
    document.querySelectorAll(".lc-relampago-res b").forEach(contar);
  };
  let espera = null;
  new MutationObserver(() => { clearTimeout(espera); espera = setTimeout(window.lcAnimar, 80); })
    .observe(document.body, { childList: true, subtree: true });
  window.lcAnimar();
})();
</script>"""


def ativar():
    """Põe o script das animações na página (uma vez por execução; ele próprio evita repetir)."""
    with st.container(key="animacoes"):
        st.html(_SCRIPT, unsafe_allow_javascript=True)
