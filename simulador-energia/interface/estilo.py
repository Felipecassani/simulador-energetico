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
        # uma cor por ferramenta: fatura, poupar, comparar, preço hora a hora, bi-horário
        "c1": "#E0485A", "c2": "#5BBF8E", "c3": "#D9B45B", "c4": "#4FB3C4", "c5": "#8C8CF0",
    },
    "light": {
        "bg": "#FBF6F2", "surface": "#FFFFFF", "surface-2": "#F3E8E1",
        "border": "#E4D2C7", "text": "#1E1216", "muted": "#6E5A55",
        "primary": "#A8192E", "primary-deep": "#5C0B18",
        "gold": "#A8842E", "bronze": "#8F5B3E",
        "ok": "#2F8A5E", "warn": "#A8842E", "err": "#A8192E",
        # texto pequeno no tema claro: o dourado e o verde normais ficam abaixo de 4,5:1
        "gold-texto": "#7A5C1A", "ok-texto": "#23704B",
        "c1": "#A8192E", "c2": "#23704B", "c3": "#8C6A1F", "c4": "#1C6F7C", "c5": "#4B4BB8",
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
@import url("https://fonts.googleapis.com/css2?family=Caveat:wght@600&display=swap");   /* assinatura manuscrita */
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
:is(.st-key-aprender, .st-key-em_breve, .st-key-rodape_ajuda) [data-testid="stPageLink-NavLink"] {{
  min-height: 44px; padding: 0 1rem !important; border: 1px solid var(--lc-border); border-radius: 999px;
  background: var(--lc-surface);
}}
.st-key-em_breve [data-testid="stPageLink-NavLink"] {{ border-style: dashed; }}
.st-key-rodape_ajuda {{ margin-top: 2.2rem; }}

/* ---------- Separadores (ex.: as 3 partes da Fatura): parecem botões, não texto solto ---------- */
[data-testid="stTabs"] [role="tablist"] {{ flex-wrap: wrap; gap: .45rem; border-bottom: none; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-border"],
[data-testid="stTabs"] .react-aria-SelectionIndicator {{ display: none !important; }}
[data-testid="stTabs"] [role="tablist"], [data-testid="stTabs"] [role="tablist"] > * {{ box-shadow: none !important; border-bottom: none !important; }}
[data-testid="stTabs"] [role="tablist"]::after, [data-testid="stTabs"] [role="tablist"]::before {{ display: none !important; }}
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
/* rótulos compridos (caixas, interruptores) mudam de linha em vez de sair do ecrã do telemóvel */
:is([data-testid="stCheckbox"], [data-testid="stToggle"], [data-testid="stWidgetLabel"], [data-testid="stRadio"]) label p {{
  white-space: normal !important; overflow-wrap: anywhere;
}}
:is([data-testid="stCheckbox"], [data-testid="stToggle"]) label {{ max-width: 100%; }}

/* logótipo no topo, com o nome «Simulador Energético» legível */
[data-testid="stHeaderLogo"] {{ height: 2.6rem !important; max-width: none !important; width: auto !important; }}
/* telemóvel: logótipo com o nome um pouco mais pequeno, para caber com o Menu e o botão de tema */
@media (max-width: 767.98px) {{
  [data-testid="stHeaderLogo"] {{ height: 2.2rem !important; }}
}}

/* ---------- Botão claro/escuro: mosaico fixo no canto ---------- */
.st-key-tema_mosaico {{
  position: fixed !important; top: .6rem; right: clamp(.8rem, 2vw, 1.6rem); z-index: 1000001;
  width: auto !important;
}}
/* botão de tema: um só, alterna entre claro e escuro a cada clique */
.lc-tema {{
  all: unset; box-sizing: border-box; height: 44px; display: inline-flex; align-items: center; gap: .45rem;
  padding: 0 1rem 0 .85rem; cursor: pointer; font-weight: 700; font-size: .95rem;
  border-radius: 999px; color: var(--lc-gold-texto); background: var(--lc-surface);
  border: 1px solid var(--lc-border); box-shadow: 0 10px 24px -16px rgba(0,0,0,.6);
  transition: transform .25s ease, border-color .2s ease;
}}
.lc-tema:hover {{ border-color: var(--lc-gold); }}
.lc-tema:hover svg {{ transform: rotate(-20deg); transition: transform .25s ease; }}
.lc-tema:focus-visible {{ outline: 2px solid var(--lc-gold); outline-offset: 2px; }}
.lc-tema svg {{ width: 20px; height: 20px; flex: none; }}
.lc-tema-txt {{ color: var(--lc-text); }}
@media (max-width: 767.98px) {{          /* telemóvel: só o ícone (não cabe o texto) */
  .lc-tema {{ width: 44px; padding: 0; justify-content: center; }}
  .lc-tema-txt {{ display: none; }}
}}
@media (prefers-reduced-motion: reduce) {{ .lc-tema {{ transition: none !important; }} }}

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

/* Início: a grelha das ferramentas fica regular (4 · 2×2 · 1) e os cartões com a mesma altura,
   com o botão sempre alinhado em baixo */
.st-key-grelha_ferramentas {{
  display: grid !important; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1rem; align-items: stretch;
}}
@media (max-width: 1100px) {{ .st-key-grelha_ferramentas {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (max-width: 640px) {{ .st-key-grelha_ferramentas {{ grid-template-columns: 1fr; }} }}
.st-key-grelha_ferramentas > * {{ min-width: 0; height: 100%; }}
[class*="st-key-cartao_"] {{ height: 100%; justify-content: space-between; }}
[class*="st-key-cartao_"] > [data-testid="stElementContainer"]:first-child {{ flex: 1 1 auto; }}
/* o cartão de destaque (por onde se começa): texto à esquerda, botão à direita */
.st-key-cartao_1_destaque {{
  flex-direction: row !important; align-items: center !important; gap: 1.5rem !important; flex-wrap: wrap;
  border-width: 2px !important; border-color: var(--lc-primary) !important;
  background: linear-gradient(120deg, color-mix(in srgb, var(--lc-primary) 16%, var(--lc-surface)), var(--lc-surface)) !important;
  margin-bottom: .4rem;
}}
.st-key-cartao_1_destaque > [data-testid="stElementContainer"]:first-child {{ flex: 1 1 360px; }}
.st-key-cartao_1_destaque h4 {{ font-size: 1.35rem !important; margin: 0 !important; }}
.st-key-cartao_1_destaque .lc-topo {{ align-items: center; margin-bottom: .35rem; }}
.st-key-cartao_1_destaque .lc-topo {{ justify-content: flex-start; gap: .7rem; }}
.st-key-cartao_1_destaque > [data-testid="stElementContainer"]:last-child {{ align-self: center; }}
.st-key-cartao_1_destaque [data-testid="stPageLink-NavLink"] {{ min-height: 52px; padding: 0 1.6rem !important; }}
.st-key-cartao_1_destaque [data-testid="stPageLink-NavLink"] :is(span, p) {{ font-size: 1.08rem !important; }}
/* as três partes da conta: emoji grande e mesma altura */
.lc-parte .lc-emoji, .lc-passo .lc-emoji {{ display: inline-grid; place-items: center; width: 3rem; height: 3rem;
  border-radius: 16px; font-size: 1.6rem; margin-bottom: .45rem; background: color-mix(in srgb, var(--lc-gold) 16%, transparent); }}

/* barra "para onde vai o teu dinheiro" */
.lc-dinheiro {{ margin: .6rem 0 1rem; }}
.lc-dinheiro .lc-n {{ font-family: Sora, sans-serif; font-weight: 800; color: var(--lc-gold-texto); font-size: .85rem; letter-spacing: .06em; }}
.lc-barra {{ display: flex; height: 18px; border-radius: 999px; overflow: hidden; margin: .5rem 0 .6rem; background: var(--lc-surface-2); }}
.lc-barra span {{ display: block; height: 100%; }}
.lc-seg-energia {{ background: var(--lc-primary); }}
.lc-seg-potencia {{ background: var(--lc-gold); }}
.lc-seg-impostos {{ background: var(--lc-bronze); }}
.lc-dinheiro ul {{ list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: .3rem 1.4rem; font-size: .95rem; }}
.lc-ponto {{ display: inline-block; width: .8rem; height: .8rem; border-radius: 50%; margin-right: .4rem; vertical-align: -.05rem; }}

/* ---------- cor de cada ferramenta (cartões da Início e cabeçalho da página) ---------- */
.st-key-cartao_1_destaque, .st-key-cartao_1, .lc-cor-1 {{ --lc-cor: var(--lc-c1); }}
.st-key-cartao_2, .lc-cor-2 {{ --lc-cor: var(--lc-c2); }}
.st-key-cartao_3, .lc-cor-3 {{ --lc-cor: var(--lc-c3); }}
.st-key-cartao_4, .lc-cor-4 {{ --lc-cor: var(--lc-c4); }}
.st-key-cartao_5, .lc-cor-5 {{ --lc-cor: var(--lc-c5); }}
[class*="st-key-cartao_"]:not([class*="st-key-cartao_breve"]) {{
  border-top: 5px solid var(--lc-cor) !important;
}}
[class*="st-key-cartao_"] .lc-emoji {{
  display: inline-grid; place-items: center; width: 3rem; height: 3rem; border-radius: 16px; font-size: 1.6rem;
  background: color-mix(in srgb, var(--lc-cor, var(--lc-gold)) 18%, transparent);
}}
.lc-step-head[class*="lc-cor-"] .lc-step-num {{
  color: var(--lc-cor); border-color: color-mix(in srgb, var(--lc-cor) 50%, transparent);
  background: color-mix(in srgb, var(--lc-cor) 16%, transparent);
}}
.lc-step-head[class*="lc-cor-"] {{ border-left: 5px solid var(--lc-cor); padding-left: 1rem; }}

/* texto com palavras técnicas sublinhadas (ui.texto) */
.lc-texto p {{ margin: 0 0 .5rem; line-height: 1.6; }}
.lc-texto ul {{ margin: .2rem 0 .6rem 1.1rem; padding: 0; }}
.lc-texto li {{ margin: .15rem 0; line-height: 1.55; }}

/* nota "ⓘ Saber mais": a explicação aparece num balão (rato ou toque) */
.lc-nota {{
  display: inline-flex; align-items: center; gap: .3rem; position: relative; cursor: help; outline: none;
  font-size: .88rem; font-weight: 600; color: var(--lc-gold-texto); padding: .15rem .6rem; border-radius: 999px;
  background: color-mix(in srgb, var(--lc-gold) 12%, transparent); margin: .1rem 0 .3rem;
}}
.lc-nota:hover::after, .lc-nota:focus::after {{
  content: attr(data-def); position: absolute; left: 0; top: calc(100% + 8px); z-index: 60;
  width: max-content; max-width: min(360px, 86vw); white-space: normal; text-align: left;
  background: var(--lc-surface-2); color: var(--lc-text); border: 1px solid var(--lc-border);
  border-radius: 12px; padding: .65rem .8rem; font-size: .9rem; line-height: 1.45; font-weight: 400;
  box-shadow: 0 14px 30px -14px rgba(0,0,0,.6);
}}
[data-testid="stHtml"]:has(.lc-nota), [data-testid="stElementContainer"]:has(.lc-nota) {{ overflow: visible !important; }}

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
/* hero com ilustração: texto à esquerda, desenho à direita (no telemóvel só o texto) */
.lc-hero-com-img {{ display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; }}
.lc-hero-img {{ width: clamp(150px, 22vw, 260px); height: auto; flex: none; filter: drop-shadow(0 18px 30px rgba(0,0,0,.25)); }}
@media (max-width: 640px) {{ .lc-hero-img {{ display: none; }} }}

/* prova: números reais calculados com os dados oficiais */
.lc-prova .lc-metric {{ text-align: center; }}
.lc-passo .lc-n, .lc-parte .lc-n {{ display: block; }}
@media (max-width: 640px) {{             /* telemóvel: os 3 números lado a lado, compactos */
  .lc-prova .lc-grid {{ gap: .5rem; }}
  .lc-prova .lc-metric {{ padding: .7rem .4rem; border-radius: 16px; }}
  .lc-prova .lc-label {{ font-size: .78rem; }}
  .lc-prova .lc-value {{ font-size: 1.45rem; }}
  .lc-prova .lc-unit-linha {{ font-size: .75rem; }}
}}
.lc-prova .lc-value {{ color: var(--lc-gold-texto); }}
/* selos de confiança */
.lc-selos {{ display: flex; flex-wrap: wrap; gap: .5rem; justify-content: center; margin: .2rem 0 .4rem; }}
.lc-selo {{ display: inline-flex; align-items: center; gap: .35rem; padding: .4rem .85rem; border-radius: 999px;
  font-size: .9rem; font-weight: 600; color: var(--lc-text); background: var(--lc-surface);
  border: 1px solid var(--lc-border); }}
.lc-selo b {{ color: var(--lc-ok-texto); }}
/* chamada final */
.st-key-cta_final {{
  text-align: center; padding: 2rem 1.2rem !important; border-radius: 26px; align-items: center;
  background: radial-gradient(500px 200px at 50% 0%, color-mix(in srgb, var(--lc-gold) 22%, transparent), transparent 70%),
              linear-gradient(135deg, var(--lc-primary), var(--lc-primary-deep));
}}
.st-key-cta_final h2 {{ color: #FFF7F2 !important; font-family: Sora, sans-serif; margin: 0 0 .3rem !important; }}
.st-key-cta_final p {{ color: #FFE9B8 !important; margin: 0 !important; }}
.st-key-cta_final [data-testid="stPageLink-NavLink"] {{
  min-height: 52px; padding: 0 1.8rem !important; border-radius: 999px; background: #FFF7F2;
}}
.st-key-cta_final [data-testid="stPageLink-NavLink"] :is(span, p, [data-testid="stIconMaterial"]) {{
  color: var(--lc-primary-deep) !important; font-weight: 800; font-size: 1.1rem;
}}
.st-key-cta_final [data-testid="stElementContainer"] {{ width: auto !important; }}
.lc-micro {{ font-size: .9rem; color: var(--lc-muted); margin: .2rem 0 0 .3rem; }}

/* ================= composição «fotográfica»: guiar o olhar para o caminho certo ================= */
/* 1) ponto focal: o botão principal é o elemento mais luminoso, com um brilho que pulsa devagar */
@keyframes lc-foco {{ 0%, 100% {{ box-shadow: 0 12px 28px -14px var(--lc-primary), 0 0 0 0 color-mix(in srgb, var(--lc-gold) 55%, transparent); }}
                      50% {{ box-shadow: 0 12px 28px -14px var(--lc-primary), 0 0 0 10px color-mix(in srgb, var(--lc-gold) 0%, transparent); }} }}
.st-key-cta_inicio [data-testid="stPageLink-NavLink"], .st-key-cta_final [data-testid="stPageLink-NavLink"] {{
  animation: lc-foco 2.6s ease-in-out infinite;
}}
/* 3) linhas entre passos: 01 → 02 → 03 (Como funciona) e na visita guiada */
.lc-grid:has(.lc-passo) {{ position: relative; }}
.lc-card.lc-passo {{ position: relative; overflow: visible; }}
.lc-passo:not(:last-child)::after {{
  content: "→"; position: absolute; right: -0.95rem; top: 50%; transform: translateY(-50%); z-index: 2;
  width: 1.6rem; height: 1.6rem; border-radius: 50%; display: grid; place-items: center; font-weight: 800;
  background: var(--lc-gold); color: #1E1216; font-size: .9rem;
}}
/* 4) profundidade de campo: o secundário fica um pouco atenuado e ganha nitidez ao passar o rato */
@media (hover: hover) and (pointer: fine) {{
  :is(.st-key-em_breve, .st-key-aprender, .st-key-rodape_ajuda, .lc-selos) {{ opacity: .72; transition: opacity .25s ease; }}
  :is(.st-key-em_breve, .st-key-aprender, .st-key-rodape_ajuda, .lc-selos):hover {{ opacity: 1; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .st-key-cta_inicio [data-testid="stPageLink-NavLink"], .st-key-cta_final [data-testid="stPageLink-NavLink"] {{ animation: none; }}
}}

/* ================= animações: convidam a continuar (só com movimento permitido) ================= */
.st-key-animacoes {{ display: none !important; }}
@media (prefers-reduced-motion: no-preference) {{
  /* entrada suave dos cartões ao descer a página (a classe só é posta pelo script: sem ele, tudo visível) */
  .lc-anim {{ opacity: 0; transform: translateY(18px) scale(.98); }}
  .lc-anim.lc-visto {{ opacity: 1; transform: none; transition: opacity .55s ease, transform .55s cubic-bezier(.2,.8,.2,1); }}
  /* barra «para onde vai o teu dinheiro» cresce da esquerda */
  .lc-barra span {{ transform-origin: left; animation: lc-cresce 1s cubic-bezier(.2,.8,.2,1) both; }}
  .lc-barra span:nth-child(2) {{ animation-delay: .15s; }}
  .lc-barra span:nth-child(3) {{ animation-delay: .3s; }}
  @keyframes lc-cresce {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
  /* resultado da calculadora aparece com um pequeno salto */
  .lc-relampago-res {{ animation: lc-salto .6s cubic-bezier(.34,1.56,.64,1) both; }}
  @keyframes lc-salto {{ from {{ opacity: 0; transform: translateY(10px) scale(.95); }} to {{ opacity: 1; transform: none; }} }}
  /* ícones das ferramentas abanam ao passar o rato */
  @keyframes lc-abana {{ 0%, 100% {{ transform: rotate(0); }} 25% {{ transform: rotate(-10deg) scale(1.08); }} 75% {{ transform: rotate(8deg) scale(1.08); }} }}
  [class*="st-key-cartao_"]:hover .lc-emoji, .lc-parte:hover .lc-emoji, .lc-passo:hover .lc-emoji {{ animation: lc-abana .6s ease; }}
  /* botões afundam ao clicar */
  [data-testid="stPageLink-NavLink"], [data-testid^="stBaseButton"], .lc-tema {{ transition: transform .12s ease, filter .2s ease; }}
  [data-testid="stPageLink-NavLink"]:active, [data-testid^="stBaseButton"]:active {{ transform: scale(.96); }}
  [data-testid="stPageLink-NavLink"]:hover {{ filter: brightness(1.06); }}
  /* separadores: sobem um pouco ao passar o rato */
  [data-testid="stTab"] {{ transition: transform .15s ease; }}
  [data-testid="stTab"]:hover {{ transform: translateY(-2px); }}
  /* pódio: a medalha de ouro brilha */
  .lc-podio-1 .lc-podio-medalha span[aria-hidden] {{ display: inline-block; animation: lc-brilho 2.4s ease-in-out infinite; }}
  @keyframes lc-brilho {{ 0%, 100% {{ transform: rotate(0) scale(1); }} 50% {{ transform: rotate(-8deg) scale(1.15); }} }}
}}

/* ================= cara humana: ícones de traço (não emojis) e a nota do autor ================= */
.lc-ic {{
  font-family: "Material Symbols Rounded"; font-weight: normal; font-style: normal; font-size: 1.35em;
  line-height: 1; letter-spacing: normal; text-transform: none; display: inline-block; white-space: nowrap;
  font-feature-settings: "liga"; -webkit-font-smoothing: antialiased; vertical-align: -.22em;
}}
.lc-emoji .lc-ic, .lc-step-num .lc-ic {{ font-size: 1.7rem; vertical-align: 0; color: var(--lc-cor, var(--lc-gold-texto)); }}
.lc-step-num .lc-ic {{ color: inherit; }}
.lc-selo .lc-ic {{ font-size: 1.15rem; color: var(--lc-ok-texto); }}
.lc-relampago-titulo .lc-ic, .lc-sazonal-data .lc-ic {{ color: var(--lc-gold-texto); }}
.lc-nota-autor {{
  display: flex; gap: 1.1rem; align-items: flex-start; max-width: 760px; margin: 1.6rem auto .4rem;
  padding: 1.2rem 1.4rem; border-radius: 22px; background: var(--lc-surface); border: 1px solid var(--lc-border);
}}
.lc-nota-autor img {{ width: 56px; height: 56px; border-radius: 16px; flex: none; }}
.lc-nota-autor p {{ margin: 0; font-size: 1.02rem; line-height: 1.6; color: var(--lc-text); }}
.lc-assinatura {{ display: block; margin-top: .3rem; font-family: Caveat, "Segoe Script", "Bradley Hand", cursive;
  font-size: 1.9rem; font-weight: 600; color: var(--lc-primary); line-height: 1; }}

/* calculadora relâmpago */
.st-key-relampago {{
  margin: .8rem 0 .4rem; padding: 1.1rem 1.2rem !important; border-radius: 22px;
  background: var(--lc-surface); border: 2px solid color-mix(in srgb, var(--lc-gold) 55%, var(--lc-border));
}}
.lc-relampago-titulo {{ font-family: Sora, sans-serif; font-weight: 800; font-size: 1.25rem; margin-bottom: .2rem; }}
.st-key-relampago [data-testid="stNumberInput"] input {{ font-size: 1.4rem !important; font-weight: 700; min-height: 52px; }}
.lc-relampago-res {{ font-size: 1.15rem; margin: .4rem 0 .2rem; }}
.lc-relampago-res b {{ font-family: Sora, sans-serif; font-size: 2rem; color: var(--lc-ok-texto); }}
.lc-relampago-tipo {{ display: inline-block; margin-left: .4rem; padding: .1rem .55rem; border-radius: 999px; font-size: .8rem;
  font-weight: 700; color: var(--lc-gold-texto); background: color-mix(in srgb, var(--lc-gold) 14%, transparent); vertical-align: middle; }}
/* aviso sazonal */
.lc-sazonal {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: .3rem .7rem; margin: .7rem 0 .2rem;
  padding: .7rem 1rem; border-radius: 16px; background: color-mix(in srgb, var(--lc-gold) 12%, var(--lc-surface));
  border: 1px solid color-mix(in srgb, var(--lc-gold) 45%, transparent); font-size: .95rem; }}
.lc-sazonal-data {{ font-weight: 800; color: var(--lc-gold-texto); }}
.lc-sazonal span:last-child {{ color: var(--lc-muted); }}
/* visita guiada: 3 passos ligados por setas */
.st-key-visita {{ padding: 1rem !important; border-radius: 20px; border: 2px dashed color-mix(in srgb, var(--lc-gold) 55%, transparent); }}
.lc-visita {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.4rem; }}
.lc-visita > div {{ position: relative; display: flex; flex-direction: column; gap: .15rem; }}
.lc-visita > div:not(:last-child)::after {{ content: "→"; position: absolute; right: -1.1rem; top: .3rem;
  font-weight: 800; color: var(--lc-gold-texto); }}
.lc-visita span {{ display: inline-grid; place-items: center; width: 2rem; height: 2rem; border-radius: 50%;
  background: var(--lc-primary); color: #FFF7F2; font-weight: 800; }}
.lc-visita small {{ color: var(--lc-muted); }}
@media (max-width: 640px) {{
  .lc-visita {{ grid-template-columns: 1fr; gap: .7rem; }}
  .lc-visita > div:not(:last-child)::after {{ content: "↓"; right: auto; left: .6rem; top: auto; bottom: -.75rem; }}
  .lc-passo:not(:last-child)::after {{ content: "↓"; right: auto; left: 50%; top: auto; bottom: -1.1rem; transform: translateX(-50%); }}
}}
/* «Ajudou-te?» e partilhar */
.st-key-ajudou {{ align-items: center; gap: .6rem; margin-top: 1rem; }}
.lc-ajudou {{ font-weight: 700; }}
[class*="st-key-partilhar_"] {{ gap: .6rem; margin: .6rem 0; flex-wrap: wrap; }}
/* destaques no cabeçalho das ferramentas: números reais em pílulas da cor da ferramenta */
.lc-destaques {{ display: flex; flex-wrap: wrap; gap: .45rem; margin-top: .7rem; }}
.lc-realce {{
  display: inline-flex; align-items: baseline; gap: .35rem; padding: .35rem .8rem; border-radius: 999px;
  font-size: .9rem; color: var(--lc-text);
  background: color-mix(in srgb, var(--lc-cor, var(--lc-gold)) 14%, var(--lc-surface));
  border: 1px solid color-mix(in srgb, var(--lc-cor, var(--lc-gold)) 40%, transparent);
}}
.lc-realce b {{ font-family: Sora, sans-serif; font-weight: 800; font-size: 1rem; color: var(--lc-cor, var(--lc-gold-texto)); }}
/* faixa final: o que se aprendeu + próximo passo */
.lc-cta-kicker {{ font-family: Sora, sans-serif; font-weight: 800; font-size: .8rem; letter-spacing: .12em; color: #FFE9B8; }}
.st-key-cta_final .lc-cta-txt {{ color: #FFF7F2 !important; font-size: 1.05rem; line-height: 1.55;
  max-width: 70ch; margin: .4rem auto 0 !important; }}
.st-key-cta_final .st-key-proximo_ligacoes {{ justify-content: center; gap: .6rem; }}
.st-key-proximo_ligacoes [data-testid="stPageLink-NavLink"] {{ background: #FFF7F2 !important; border: none !important; }}
.st-key-proximo_ligacoes [data-testid="stPageLink"]:not(:first-child) [data-testid="stPageLink-NavLink"] {{
  background: transparent !important; border: 1px solid rgba(255,247,242,.6) !important;
}}
.st-key-proximo_ligacoes [data-testid="stPageLink"]:not(:first-child) :is(span, p, [data-testid="stIconMaterial"]) {{
  color: #FFF7F2 !important;
}}
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
.lc-grid {{ display: flex; flex-wrap: wrap; gap: 1rem; align-items: stretch; --lc-min: 200px; --lc-cols: 4; }}
.lc-grid > * {{
  box-sizing: border-box; min-width: 0; align-self: stretch;
  flex: 1 1 max(min(var(--lc-min), 100%), calc((100% - (var(--lc-cols) - 1) * 1rem) / var(--lc-cols) - 1px));
}}
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
.lc-metric .lc-unit-linha {{ display: block; margin: .15rem 0 0; font-size: .92rem; line-height: 1.3; }}
.lc-metric.lc-metric-texto .lc-value {{ font-size: 1.25rem; line-height: 1.3; }}
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
