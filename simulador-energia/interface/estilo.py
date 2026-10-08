"""Identidade visual: paleta, fontes e CSS próprio.

Paleta tirada da foto de referência:
carmim do fundo · dourado do fio · bronze do tom de pele · vinho-noir do cabelo/barba.
As cores base do Streamlit estão em .streamlit/config.toml; aqui ficam as
mesmas cores como variáveis CSS (--lc-*) para os componentes próprios.
"""
import streamlit as st

MARCA = "Simulador Energético"

PALETAS = {
    "dark": {
        "bg": "#120A0D", "surface": "#1E1115", "surface-2": "#2A171D",
        "border": "#3A2228", "text": "#F4ECE6", "muted": "#B9A59D",
        "primary": "#C8283C", "primary-deep": "#6E0E1C",
        "gold": "#D9B45B", "bronze": "#B9805E",
        "ok": "#5BBF8E", "warn": "#D9B45B", "err": "#E0485A",
        "gold-texto": "#D9B45B", "ok-texto": "#5BBF8E",
    },
    "light": {
        "bg": "#FBF6F2", "surface": "#FFFFFF", "surface-2": "#F3E8E1",
        "border": "#E4D2C7", "text": "#1E1216", "muted": "#6E5A55",
        "primary": "#A8192E", "primary-deep": "#5C0B18",
        "gold": "#A8842E", "bronze": "#8F5B3E",
        "ok": "#2F8A5E", "warn": "#A8842E", "err": "#A8192E",
        # texto pequeno no tema claro: o dourado e o verde normais ficam abaixo de 4,5:1
        "gold-texto": "#7A5C1A", "ok-texto": "#23704B",
    },
}


def tema_atual():
    """'dark' ou 'light', conforme o tema ativo no browser (por omissão: dark)."""
    try:
        tipo = st.context.theme.type
    except Exception:
        tipo = None
    return tipo if tipo in PALETAS else "dark"


def paleta():
    return PALETAS[tema_atual()]


_CSS = """
:root {{ {tokens} }}

/* Fundo com brilho carmim suave no canto — dá profundidade sem distrair */
.stApp {{
  background:
    radial-gradient(900px 420px at 100% -8%, color-mix(in srgb, var(--lc-primary) 22%, transparent), transparent 65%),
    radial-gradient(700px 380px at -10% 110%, color-mix(in srgb, var(--lc-gold) 10%, transparent), transparent 60%),
    var(--lc-bg);
}}
.block-container {{ padding: 5.2rem clamp(1rem, 3vw, 3.5rem) 2rem; max-width: none; }}

/* ---------- Navegação no topo ---------- */
[data-testid="stTopNavLink"], [data-testid="stTopNavSection"] {{
  border-radius: 999px; padding: .5rem 1.1rem !important; transition: all .15s ease;
}}
[data-testid="stTopNavLink"] p, [data-testid="stTopNavSection"] p {{
  font-size: 1.02rem !important; font-weight: 700 !important;
}}
/* "Início" só fica em carmim quando é a página aberta; o menu "Ferramentas" (o 1.º grupo) tem
   sempre a borda carmim: é aí que estão as ferramentas */
[data-testid="stTopNavLink"], [data-testid="stTopNavSection"] {{
  border: 1px solid var(--lc-border) !important; background: var(--lc-surface) !important;
}}
[data-testid="stTopNavLink"][aria-current="page"] {{
  background: linear-gradient(135deg, var(--lc-primary), var(--lc-primary-deep)) !important;
  border-color: transparent !important; box-shadow: 0 8px 22px -12px var(--lc-primary);
}}
[data-testid="stTopNavLink"][aria-current="page"] :is(p, [data-testid="stIconMaterial"]) {{ color: #FFF7F2 !important; }}
.rc-overflow-item:nth-child(2) [data-testid="stTopNavSection"] {{
  border: 2px solid var(--lc-primary) !important;
  background: color-mix(in srgb, var(--lc-primary) 14%, var(--lc-surface)) !important;
}}
@media (min-width: 768px) and (max-width: 1180px) {{
  [data-testid="stTopNavLink"], [data-testid="stTopNavSection"] {{ padding: .4rem .75rem !important; }}
  [data-testid="stTopNavLink"] p, [data-testid="stTopNavSection"] p {{ font-size: .95rem !important; }}
}}

/* Telemóvel: o Streamlit troca o menu do topo por um ícone ">>" sem texto; passa a ser "☰ Menu" */
[data-testid="stExpandSidebarButton"] {{
  display: inline-flex !important; align-items: center; gap: .45rem; min-height: 44px; width: auto !important;
  padding: 0 1rem 0 .85rem !important; border-radius: 999px !important;
  background: linear-gradient(135deg, var(--lc-primary), var(--lc-primary-deep)) !important;
  color: #FFF7F2 !important; box-shadow: 0 8px 22px -12px var(--lc-primary);
}}
[data-testid="stExpandSidebarButton"] > span {{ display: none; }}   /* o ícone ">>" e o seu contentor */
[data-testid="stExpandSidebarButton"]::before {{ content: "☰"; font-size: 1.15rem; line-height: 1; }}
[data-testid="stExpandSidebarButton"]::after {{ content: "Menu"; font-weight: 700; font-size: 1rem; }}
[data-testid="stSidebarNavLink"] {{ min-height: 44px; }}
[data-testid="stSidebarNavLink"] span {{ font-size: 1.02rem; }}
@media (max-width: 767.98px) {{
  /* menu aberto: o seletor de tema não tapa o botão de fechar */
  .stApp:has([data-testid="stSidebar"][aria-expanded="true"]) .st-key-tema_mosaico {{ visibility: hidden; }}
  .block-container {{ padding-top: 4.6rem !important; }}
  .lc-tema {{ grid-template-columns: repeat(3, 40px); }}
  .lc-tema button, .lc-tema-ind {{ width: 40px; height: 40px; }}
  .lc-tema[data-estado="System"] .lc-tema-ind {{ transform: translateX(42px); }}
  .lc-tema[data-estado="Dark"] .lc-tema-ind {{ transform: translateX(84px); }}
}}

/* ---------- Botões-ligação (Começar, próximo passo, ajuda, em breve) ---------- */
.st-key-cta_inicio {{ margin: .4rem 0 0; }}
.st-key-cta_inicio [data-testid="stPageLink-NavLink"] {{
  min-height: 52px; width: fit-content; padding: 0 1.6rem !important; border-radius: 999px;
  background: linear-gradient(135deg, var(--lc-primary), var(--lc-primary-deep));
  box-shadow: 0 12px 28px -14px var(--lc-primary);
}}
.st-key-cta_inicio [data-testid="stPageLink-NavLink"] :is(span, p, [data-testid="stIconMaterial"]) {{
  color: #FFF7F2 !important; font-weight: 700; font-size: 1.1rem;
}}
:is(.st-key-aprender, .st-key-em_breve, .st-key-rodape_ajuda, .st-key-proximo_ligacoes) [data-testid="stPageLink-NavLink"] {{
  min-height: 44px; padding: 0 1rem !important; border: 1px solid var(--lc-border); border-radius: 999px;
  background: var(--lc-surface);
}}
.st-key-em_breve [data-testid="stPageLink-NavLink"] {{ border-style: dashed; }}
.st-key-proximo_ligacoes [data-testid="stPageLink-NavLink"]:first-child {{
  background: linear-gradient(135deg, var(--lc-primary), var(--lc-primary-deep)); border-color: transparent;
}}
.st-key-proximo_ligacoes [data-testid="stPageLink"]:first-child [data-testid="stPageLink-NavLink"] :is(span, p, [data-testid="stIconMaterial"]) {{
  color: #FFF7F2 !important; font-weight: 700;
}}
.st-key-proximo_passo {{ border-color: color-mix(in srgb, var(--lc-gold) 45%, var(--lc-border)) !important; }}
.st-key-proximo_passo .lc-card-flat p {{ color: var(--lc-text); font-size: 1rem; line-height: 1.55; margin-top: .3rem; }}
.st-key-rodape_ajuda {{ margin-top: 2.2rem; }}

/* ---------- Separadores (ex.: as 3 partes da Fatura): parecem botões, não texto solto ---------- */
[data-testid="stTabs"] [role="tablist"] {{ flex-wrap: wrap; gap: .45rem; border-bottom: none; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-border"] {{ display: none; }}
[data-testid="stTab"] {{
  min-height: 48px; padding: .35rem 1.1rem !important; border: 1px solid var(--lc-border) !important;
  border-radius: 999px; background: var(--lc-surface);
}}
[data-testid="stTab"] p {{ font-size: 1.05rem !important; font-weight: 700; }}
[data-testid="stTab"][aria-selected="true"] {{
  background: linear-gradient(135deg, var(--lc-primary), var(--lc-primary-deep)); border-color: transparent !important;
}}
[data-testid="stTab"][aria-selected="true"] :is(p, [data-testid="stIconMaterial"]) {{ color: #FFF7F2 !important; }}

/* caixa de carregar ficheiros: o Streamlit escreve-a em inglês ("Upload", "15MB per file") */
[data-testid="stFileUploaderDropzone"] button {{ min-height: 44px; }}
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p {{ font-size: 0 !important; }}
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p::after {{
  content: "Escolher ficheiro"; font-size: 1rem; font-weight: 600;
}}
[data-testid="stFileUploaderDropzoneInstructions"] span {{ font-size: 0 !important; }}
[data-testid="stFileUploaderDropzoneInstructions"] span::after {{
  content: "ou arrasta-o para aqui · até 15 MB cada"; font-size: .95rem;
}}

/* ajuda (?) dos campos maior e mais fácil de tocar; legendas legíveis */
[data-testid="stTooltipIcon"] svg {{ width: 1.25rem; height: 1.25rem; }}
[data-testid="stCaptionContainer"] {{ font-size: .95rem; }}
[data-testid="stWidgetLabel"] p {{ font-size: 1rem; }}

/* ---------- Botão claro/escuro: mosaico fixo no canto ---------- */
.st-key-tema_mosaico {{
  position: fixed !important; top: .6rem; right: clamp(.8rem, 2vw, 1.6rem); z-index: 1000001;
  width: auto !important;
}}
/* seletor de tema: pílula com 3 estados e indicador que desliza */
.lc-tema {{
  position: relative; display: inline-grid; grid-template-columns: repeat(3, 34px); gap: 2px; padding: 3px;
  background: var(--lc-surface); border: 1px solid var(--lc-border); border-radius: 999px;
  box-shadow: 0 10px 24px -16px rgba(0,0,0,.6);
}}
.lc-tema button {{
  all: unset; box-sizing: border-box; width: 34px; height: 30px; display: grid; place-items: center;
  border-radius: 999px; cursor: pointer; color: var(--lc-muted); position: relative; z-index: 1;
  transition: color .25s ease;
}}
.lc-tema button:hover {{ color: var(--lc-text); }}
.lc-tema button:focus-visible {{ outline: 2px solid var(--lc-gold); outline-offset: 1px; }}
.lc-tema button[aria-checked="true"] {{ color: #fff; }}
.lc-tema button svg {{ width: 17px; height: 17px; transition: transform .5s cubic-bezier(.34,1.56,.64,1); }}
.lc-tema button[aria-checked="true"] svg {{ transform: rotate(360deg) scale(1.08); }}
.lc-tema-ind {{
  position: absolute; top: 3px; left: 3px; width: 34px; height: 30px; border-radius: 999px;
  background: linear-gradient(135deg, var(--lc-primary), var(--lc-gold));
  box-shadow: 0 4px 14px -6px var(--lc-primary); transition: transform .38s cubic-bezier(.65,0,.35,1);
}}
.lc-tema[data-estado="System"] .lc-tema-ind {{ transform: translateX(36px); }}
.lc-tema[data-estado="Dark"] .lc-tema-ind {{ transform: translateX(72px); }}
@media (prefers-reduced-motion: reduce) {{ .lc-tema *, .lc-tema-ind {{ transition: none !important; }} }}

/* ---------- Cartões das ferramentas: o cartão inteiro é a ligação ---------- */
[class*="st-key-cartao_"] {{ position: relative; transition: transform .18s ease, box-shadow .18s ease;
  background: var(--lc-surface); border-color: color-mix(in srgb, var(--lc-primary) 40%, var(--lc-border)) !important; }}
@media (hover: hover) and (pointer: fine) {{
  [class*="st-key-cartao_"]:hover {{ transform: translateY(-3px); box-shadow: 0 16px 34px -24px var(--lc-primary); }}
}}
/* o "Abrir" parece um botão (sem position no link: a camada ::after tem de cobrir o cartão) */
[class*="st-key-cartao_"] [data-testid="stPageLink-NavLink"] {{
  min-height: 44px; width: fit-content; padding: 0 1.2rem !important; border-radius: 999px;
  background: linear-gradient(135deg, var(--lc-primary), var(--lc-primary-deep));
}}
[class*="st-key-cartao_"] [data-testid="stPageLink-NavLink"] :is(span, p, [data-testid="stIconMaterial"]) {{
  color: #FFF7F2 !important; font-weight: 700;
}}
/* os contentores internos do Streamlit são "relative": ficam estáticos para a camada cobrir o cartão */
[class*="st-key-cartao_"] [data-testid="stElementContainer"] {{ position: static !important; }}
[class*="st-key-cartao_"] [data-testid="stPageLink-NavLink"]::after {{
  content: ""; position: absolute; inset: 0; z-index: 2; cursor: pointer;
}}

/* glossário: termo sublinhado com balão */
.lc-termo {{ border-bottom: 1px dotted var(--lc-gold); cursor: help; position: relative; outline: none; }}
.lc-termo:hover::after, .lc-termo:focus::after {{
  content: attr(data-def); position: absolute; left: 50%; top: calc(100% + 8px); transform: translateX(-50%);
  width: max-content; max-width: min(280px, 80vw); z-index: 50; white-space: normal; text-align: left;
  background: var(--lc-surface-2); color: var(--lc-text); border: 1px solid var(--lc-border);
  border-radius: 10px; padding: .55rem .7rem; font-size: .82rem; line-height: 1.4; font-weight: 400;
  box-shadow: 0 12px 28px -14px rgba(0,0,0,.55);
}}
.lc-card.lc-aberto {{ overflow: visible; }}
.lc-faq-resposta {{ color: var(--lc-text); line-height: 1.6; }}
.lc-evento {{ display: grid; grid-template-columns: 88px 1fr; gap: .9rem; align-items: start; }}
.lc-evento-data {{ text-align: center; border-right: 1px solid var(--lc-border); padding-right: .8rem; }}
.lc-evento-dia {{ font-family: Sora, sans-serif; font-weight: 800; font-size: 1.8rem; line-height: 1; color: var(--lc-gold); }}
.lc-evento-mes {{ font-size: .78rem; color: var(--lc-muted); text-transform: uppercase; letter-spacing: .08em; }}
.lc-evento h4 {{ margin: 0 0 .2rem !important; }}

/* período atual */
.lc-agora h4 {{ margin: .25rem 0 0 !important; }}
.lc-agora p {{ margin: .1rem 0 0 !important; color: var(--lc-muted); font-size: .85rem; }}
.lc-agora-hora {{ font-family: Sora, sans-serif; font-weight: 800; font-size: 1.6rem; }}
.lc-agora-barato {{ border-color: color-mix(in srgb, var(--lc-ok) 55%, var(--lc-border)) !important; }}
.lc-agora-caro {{ border-color: color-mix(in srgb, var(--lc-err) 55%, var(--lc-border)) !important; }}

/* cartão "O meu tarifário" */
.lc-meu {{ margin: -.4rem 0 1.2rem; border-color: color-mix(in srgb, var(--lc-gold) 45%, var(--lc-border)) !important; }}
.lc-meu-topo {{ display: flex; justify-content: space-between; gap: .3rem 1rem; flex-wrap: wrap; align-items: baseline; }}
.lc-meu-fonte {{ font-size: .8rem; color: var(--lc-muted); }}
.lc-meu-corpo {{ display: flex; flex-wrap: wrap; gap: .8rem 2rem; align-items: center; justify-content: space-between; margin-top: .4rem; }}
.lc-meu h4 {{ margin: 0 0 .35rem !important; }}
.lc-meu .lc-chips {{ display: flex; flex-wrap: wrap; gap: .3rem; }}
.lc-meu-precos {{ display: flex; flex-direction: column; gap: .15rem; font-size: .9rem; color: var(--lc-muted); }}
.lc-meu-precos b {{ color: var(--lc-text); font-weight: 600; }}
.lc-meu-valor {{ font-family: Sora, sans-serif; font-weight: 800; font-size: 1.6rem; }}
.lc-meu-valor small {{ font-size: .78rem; font-weight: 500; color: var(--lc-muted); margin-left: .35rem; }}
/* o antigo aviso simples já não é usado, mas fica para compatibilidade */

/* pódio das ofertas mais baratas */
.lc-podio {{ display: flex; flex-direction: column; gap: .35rem; }}
.lc-podio-1 {{ border-color: var(--lc-gold) !important; box-shadow: 0 18px 40px -28px var(--lc-gold); }}
.lc-podio-medalha {{ font-size: 1.9rem; line-height: 1; font-family: Sora, sans-serif; font-weight: 800; color: var(--lc-gold); }}
.lc-podio h4 {{ margin: .2rem 0 0 !important; }}
.lc-podio-oferta {{ color: var(--lc-muted); font-size: .88rem; margin: 0 !important; }}
.lc-podio-valor {{ font-family: Sora, sans-serif; font-weight: 800; font-size: 1.7rem; color: var(--lc-text); }}
.lc-podio-valor small {{ font-size: .8rem; font-weight: 500; color: var(--lc-muted); margin-left: .35rem; }}
.lc-podio .lc-pos {{ color: var(--lc-ok-texto); font-weight: 700; }}
.lc-podio-lugar {{ font-size: .95rem; font-family: Inter, sans-serif; font-weight: 700; color: var(--lc-gold-texto); margin-left: .4rem; vertical-align: middle; }}
.lc-podio .lc-neg {{ color: var(--lc-err); font-weight: 700; }}
.lc-podio-nota {{ font-size: .8rem; color: var(--lc-muted); }}
.lc-podio .lc-chips {{ display: flex; flex-wrap: wrap; gap: .3rem; }}

/* secções em construção, página Sobre */
.lc-construcao {{ opacity: .9; }}
[class*="st-key-cartao_breve_"]:hover .lc-construcao {{ opacity: 1; }}
.lc-lista {{ display: inline-block; text-align: left; margin: .2rem auto 0; color: var(--lc-muted); }}
.lc-autor {{ display: flex; gap: 1.2rem; align-items: center; flex-wrap: wrap; margin-bottom: 1rem; }}
.lc-autor-logo img {{ width: 88px; height: 88px; display: block; filter: drop-shadow(0 10px 18px rgba(200,40,60,.25)); }}
.lc-social {{ display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .6rem; }}
.lc-social a {{
  display: inline-flex; align-items: center; gap: .4rem; padding: .35rem .8rem; border-radius: 999px;
  border: 1px solid var(--lc-border); color: var(--lc-text) !important; text-decoration: none !important;
  font-weight: 600; font-size: .88rem; transition: border-color .2s ease, transform .2s ease;
}}
.lc-social a:hover {{ border-color: var(--lc-gold); transform: translateY(-2px); }}
.lc-social img {{ width: 16px; height: 16px; }}

/* cabeçalho de cartão com etiqueta: quebra de linha em vez de sair do cartão */
.lc-topo {{ display: flex; justify-content: space-between; align-items: center; gap: .4rem .5rem; flex-wrap: wrap; }}
.lc-card {{ overflow: hidden; }}

/* ---------- Aviso "a usar a tua fatura" ---------- */
.lc-aviso {{
  display: flex; gap: .6rem; align-items: center; flex-wrap: wrap;
  padding: .6rem .9rem; margin: -.4rem 0 1.2rem; border-radius: 14px; font-size: .9rem;
  background: color-mix(in srgb, var(--lc-gold) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--lc-gold) 35%, transparent);
}}
.lc-aviso b {{ color: var(--lc-gold-texto); }}

/* ---------- Recomendações ---------- */
.lc-rec {{ display: flex; gap: .9rem; align-items: flex-start; }}
.lc-rec .lc-rec-valor {{
  flex: none; min-width: 6.2rem; text-align: center; padding: .55rem .6rem; border-radius: 14px;
  background: color-mix(in srgb, var(--lc-ok) 12%, transparent); color: var(--lc-ok-texto);
  font-family: Sora, sans-serif; font-weight: 800; line-height: 1.1;
}}
.lc-rec .lc-rec-valor small {{ display: block; font-family: Inter, sans-serif; font-weight: 600; font-size: .85rem; }}
.lc-rec .lc-rec-info {{ background: color-mix(in srgb, var(--lc-gold) 12%, transparent); color: var(--lc-gold-texto); }}
.lc-rec a {{ color: var(--lc-gold-texto); font-weight: 600; }}

/* ---------- Hero ---------- */
.lc-hero {{
  position: relative; overflow: hidden;
  padding: 2.4rem 2.2rem; border-radius: 26px;
  background:
    radial-gradient(600px 260px at 85% 10%, color-mix(in srgb, var(--lc-gold) 28%, transparent), transparent 70%),
    linear-gradient(135deg, var(--lc-primary) 0%, var(--lc-primary-deep) 70%);
  color: #FFF7F2;
  box-shadow: 0 24px 60px -30px color-mix(in srgb, var(--lc-primary) 80%, transparent);
}}
.lc-hero::before {{
  content: ""; position: absolute; inset: 0 0 auto 0; height: 3px;
  background: linear-gradient(90deg, transparent, var(--lc-gold), transparent);
}}
.lc-hero .lc-kicker {{
  font-size: .78rem; letter-spacing: .18em; text-transform: uppercase;
  color: #FFE9B8; font-weight: 600;
}}
.lc-hero h1 {{
  font-family: Sora, Inter, sans-serif; font-weight: 800; color: #FFF7F2;
  font-size: clamp(2rem, 4.5vw, 3.2rem); line-height: 1.05; margin: .35rem 0 .6rem; padding: 0;
}}
.lc-hero p {{ font-size: 1.05rem; max-width: 60ch; opacity: .9; margin: 0; }}
.lc-chips {{ display: flex; flex-wrap: wrap; gap: .45rem; margin-top: 1.2rem; }}
.lc-chips:empty {{ display: none; }}
.lc-chip {{
  font-size: .85rem; font-weight: 600; padding: .3rem .75rem; border-radius: 999px;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22);
  backdrop-filter: blur(6px);
}}

/* ---------- Cabeçalho de passo ---------- */
.lc-step-head {{ display: flex; align-items: flex-start; gap: 1rem; margin: .2rem 0 1.6rem; }}
.lc-step-text {{ flex: 1; min-width: 0; }}
.lc-step-title {{ display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; }}
.lc-step-num {{
  flex: none; font-family: Sora, sans-serif; font-weight: 800; font-size: 1.5rem;
  width: 3.2rem; height: 3.2rem; border-radius: 16px; display: grid; place-items: center;
  color: var(--lc-gold); background: color-mix(in srgb, var(--lc-gold) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--lc-gold) 40%, transparent);
}}
.lc-step-head h2 {{ font-family: Sora, sans-serif; margin: 0; padding: 0; font-size: 1.9rem; }}
.lc-step-head p {{ margin: .15rem 0 0; color: var(--lc-muted); }}

/* ---------- Cartões ---------- */
.lc-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }}
.lc-card {{
  background: var(--lc-surface); border: 1px solid var(--lc-border);
  border-radius: 20px; padding: 1.15rem 1.25rem;
  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}}
@media (hover: hover) and (pointer: fine) {{
  .lc-card:hover {{
    transform: translateY(-2px);
    border-color: color-mix(in srgb, var(--lc-primary) 55%, var(--lc-border));
    box-shadow: 0 14px 30px -22px var(--lc-primary);
  }}
}}
.lc-card h4 {{ font-family: Sora, sans-serif; margin: .2rem 0 .35rem; padding: 0; font-size: 1.05rem; }}
.lc-card p {{ margin: 0; color: var(--lc-muted); font-size: .97rem; }}
.lc-card .lc-n {{ font-family: Sora, sans-serif; font-weight: 800; color: var(--lc-gold-texto); font-size: .85rem; letter-spacing: .08em; }}
.lc-card-flat {{ padding: .2rem .1rem .4rem; }}
.lc-card-flat h4 {{ font-family: Sora, sans-serif; margin: .35rem 0 .3rem; padding: 0; font-size: 1.05rem; }}
.lc-card-flat p {{ margin: 0; color: var(--lc-muted); font-size: .97rem; }}
.lc-card-flat .lc-n {{ font-family: Sora, sans-serif; font-weight: 800; color: var(--lc-gold-texto); font-size: .85rem; letter-spacing: .1em; }}

/* ---------- Métricas ---------- */
.lc-metric {{
  background: var(--lc-surface); border: 1px solid var(--lc-border);
  border-radius: 20px; padding: 1rem 1.2rem;
}}
.lc-metric .lc-label {{ font-size: .95rem; color: var(--lc-muted); font-weight: 600; }}
.lc-metric .lc-value {{ font-family: Sora, sans-serif; font-weight: 800; font-size: 2rem; line-height: 1.15; margin-top: .25rem; }}
.lc-metric .lc-unit {{ font-size: 1rem; font-weight: 600; color: var(--lc-muted); margin-left: .25rem; }}
.lc-metric.lc-destaque {{
  border: 1px solid transparent;
  background:
    linear-gradient(var(--lc-surface), var(--lc-surface)) padding-box,
    linear-gradient(135deg, var(--lc-primary), var(--lc-gold)) border-box;
}}
.lc-metric.lc-destaque .lc-value {{ color: var(--lc-gold); }}
.lc-metric.lc-vazio .lc-value {{ color: var(--lc-muted); }}

/* ---------- Estados ---------- */
.lc-badge {{
  white-space: nowrap; flex: none;
  display: inline-flex; align-items: center; gap: .35rem;
  font-size: .82rem; font-weight: 700; letter-spacing: .02em;
  padding: .22rem .6rem; border-radius: 999px; border: 1px solid;
}}
.lc-badge::before {{ content: ""; width: .45rem; height: .45rem; border-radius: 50%; background: currentColor; }}
.lc-ok   {{ color: var(--lc-ok-texto); background: color-mix(in srgb, var(--lc-ok) 12%, transparent); }}
.lc-todo {{ color: var(--lc-muted); background: color-mix(in srgb, var(--lc-muted) 10%, transparent); }}
.lc-rever{{ color: var(--lc-gold-texto); background: color-mix(in srgb, var(--lc-warn) 12%, transparent); }}
.lc-erro {{ color: var(--lc-err);   background: color-mix(in srgb, var(--lc-err) 12%, transparent); }}

/* ---------- Ferramentas ---------- */
.lc-emoji {{ font-size: 1.7rem; line-height: 1; }}
.lc-breve {{ text-align: center; padding: 2.4rem 1.5rem; border-style: dashed; max-width: 560px; margin: .5rem auto 1rem; }}
.lc-breve .lc-emoji {{ font-size: 2.4rem; margin-bottom: .4rem; }}
.lc-breve h4 {{ font-size: 1.2rem; }}
.lc-breve:hover {{ transform: none; box-shadow: none; }}

/* ---------- Rodapé ---------- */
.lc-footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--lc-border);
  color: var(--lc-muted); font-size: .82rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem; }}
.lc-footer b {{ color: var(--lc-gold-texto); font-weight: 600; }}

@media (max-width: 640px) {{
  .block-container {{ padding: 5.5rem 1rem 2rem; }}
  .lc-rec {{ flex-direction: column; }}
  .lc-hero {{ padding: 1.6rem 1.3rem; border-radius: 20px; }}
  .lc-hero .lc-kicker {{ letter-spacing: .12em; }}
  .lc-step-head {{ gap: .75rem; }}
  .lc-step-num {{ width: 2.6rem; height: 2.6rem; font-size: 1.25rem; border-radius: 12px; }}
  .lc-step-head h2 {{ font-size: 1.45rem; }}
  .lc-metric .lc-value {{ font-size: 1.6rem; }}
}}
"""


def aplicar_estilo():
    """Injeta as variáveis da paleta ativa e o CSS dos componentes."""
    tokens = " ".join(f"--lc-{nome}: {cor};" for nome, cor in paleta().items())
    st.html(f"<style>{_CSS.format(tokens=tokens)}</style>")
