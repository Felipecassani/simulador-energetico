# Simulador Energético

[![Testes](https://github.com/Felipecassani/simulador-energetico/actions/workflows/testes.yml/badge.svg)](https://github.com/Felipecassani/simulador-energetico/actions/workflows/testes.yml)

*English version: [README.en.md](README.en.md)*

Um site gratuito que ajuda qualquer pessoa em Portugal a perceber a conta da luz e a descobrir se pode pagar menos.

**Experimentar:** https://simulador-energetico-8ufymt75zojdygw4tfgxjm.streamlit.app

<p>
  <img src="imagens/inicio-claro.png" alt="Página inicial no tema claro" width="49%">
  <img src="imagens/inicio-escuro.png" alt="Página inicial no tema escuro" width="49%">
</p>
<p>
  <img src="imagens/fatura-escuro.png" alt="Ferramenta A minha fatura" width="74%">
  <img src="imagens/telemovel-claro.png" alt="O site no telemóvel" width="24%">
</p>

## Porque o fiz

A fatura da luz tem muitos termos (potência, kVA, vazio, indexado, TAR…) e a maioria das pessoas não sabe se está a pagar demais. Quis fazer uma ferramenta simples: escreves quatro números da tua fatura e vês quanto pagas, para onde vai o dinheiro e que ofertas te saem mais baratas. Sem registo e sem publicidade.

## O que o site faz

- **A minha fatura:** lê a fatura em PDF (ou preenches à mão), mostra o total com IVA e taxas e compara com as ofertas do mercado. Quem não tem a fatura à mão pode estimar o consumo pelos aparelhos da casa.
- **Poupar em casa:** dicas escolhidas para a casa de cada pessoa e quanto se poupa com elas.
- **Comparar ofertas:** as cerca de 70 ofertas publicadas pela ERSE, da mais barata para a mais cara, para o teu consumo.
- **Preço hora a hora:** o preço do mercado ibérico (OMIE) de hoje e de amanhã.
- **Bi-horário compensa?:** compara a tarifa simples, bi-horária e tri-horária com o teu horário de consumo.

No Início há uma calculadora rápida: escreves quanto pagaste na última fatura e ela estima quanto podes poupar por ano.

## Como está organizado

```
simulador-energia/
  app.py        arranque do site: menu, tema e página escolhida
  nucleo/       as contas (Python simples, sem Streamlit)
  interface/    cores, estilo e peças visuais repetidas
  paginas/      uma página por ferramenta, mais o Início e a Ajuda
  tests/        testes automáticos
  assets/       logótipo e ilustrações
```

Separei as contas (`nucleo/`) do que se vê no ecrã (`interface/` e `paginas/`). Assim consigo testar os cálculos sem abrir o site e mudar o aspeto sem mexer nas contas.

## Alguns pormenores

- **Números verdadeiros.** Os preços vêm de fontes oficiais: tarifas e ofertas da ERSE e preços diários do OMIE. O IVA e as taxas foram conferidos com uma fatura real e o total bate ao cêntimo.
- **Testado.** Há 228 testes: os cálculos são comparados com contas feitas à mão e cada página é aberta para confirmar que não dá erro. Correm sozinhos no GitHub a cada envio de código.
- **Para quem não percebe de energia.** As palavras técnicas aparecem sublinhadas e explicam-se ao passar o rato. Os detalhes ficam guardados atrás de um «ⓘ».
- **Privacidade.** A fatura é lida em memória para preencher os campos e não fica guardada.
- **Tema claro e escuro**, pensado também para o telemóvel.
- **Cartão para partilhar:** uma imagem com a poupança e um código QR que abre o site.

## Tecnologias

Python, Streamlit, pandas, Plotly, pypdf (ler faturas), reportlab (resumo em PDF), Pillow e segno (cartão com QR) e pytest.

## Correr no teu computador

```bash
git clone https://github.com/Felipecassani/simulador-energetico.git
cd simulador-energetico
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd simulador-energia
../.venv/bin/python -m streamlit run app.py
```

Para correr os testes, dentro da pasta `simulador-energia`:

```bash
../.venv/bin/python -m pytest
```

## Como o fiz

A parte mais grossa do código foi escrita com a ajuda do Claude Code. O meu trabalho foi decidir o que o site devia fazer, verificar as contas com faturas reais e rever e corrigir partes do código e do site.

O projeto ainda não está completo: há secções por fazer e linhas de código que quero reescrever à minha maneira.

## Próximos passos

- Reescrever à minha maneira os ficheiros mais pequenos de `nucleo/`, a começar por `relampago.py` (a calculadora rápida) e `aparelhos.py` (o consumo dos aparelhos). Os dois têm testes próprios, por isso consigo mudar o código e confirmar com `pytest` que as contas continuam certas.
- Depois, passar ao resto de `nucleo/` e às páginas, um ficheiro de cada vez.
- Acabar as secções que ainda estão escondidas do menu (gás, painéis solares, produção, Europa…).

O histórico de commits mostra esta evolução.

## Autor

Luiz Cassani · [LinkedIn](https://www.linkedin.com/in/luizfelipecassani/) · [GitHub](https://github.com/Felipecassani) · cassaniluizfelipe@gmail.com
