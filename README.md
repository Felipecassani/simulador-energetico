# apps-ia

Apps e sites em Python construídos com IA como assistente de programação.

| App | O quê | Estado |
|---|---|---|
| [`simulador-energia/`](simulador-energia/) | Simulador de custos de eletricidade: fatura (carregar PDF/foto ou à mão), eficiência com dicas, tarifários com OMIE e ERSE ao vivo, gráficos, bi/tri-horário fixo e indexado | 5 ferramentas validadas |

## Arrancar

1. Ligar o SSD e abrir a pasta `apps-ia` no PyCharm.
2. Escolher **Simulador (Streamlit)** no canto superior direito e carregar em ▶.
3. O browser abre em <http://localhost:8501>. Cada gravação de ficheiro atualiza a página.

Outros botões ▶:
- **Testes (pytest)** — o que ainda não foi feito aparece como *skipped*.
- **Gerar guia (PDF)** — só no computador do autor (não está no repositório) — atualiza `simulador-energia/docs/Guia_Simulador_Energetico.pdf`
  (fórmulas, boas práticas com IA e ambiente de trabalho; só para o programador).

## Pelo terminal

```bash
cd simulador-energia
~/.venvs/apps-ia/bin/python -m streamlit run app.py
~/.venvs/apps-ia/bin/python -m pytest
~/.venvs/apps-ia/bin/python docs/gerar_pdf.py
```

## Ambiente

- Python 3.14 em `~/.venvs/apps-ia`, no disco interno. O SSD é exFAT e não aguenta
  bem um ambiente Python lá dentro.
- Reinstalar do zero:
  `python3.14 -m venv ~/.venvs/apps-ia && ~/.venvs/apps-ia/bin/pip install -r requirements.txt`


## Publicar (Streamlit Community Cloud, gratuito)
Passos com a tua conta (login no GitHub):
1. Abre https://share.streamlit.io e entra com **Continue with GitHub**; autoriza o acesso aos
   repositórios privados quando o pedir.
2. **Create app** › *Deploy a public app from GitHub* (o nome é enganador: com repositório privado,
   a app fica **privada**). Preenche:
   - Repository: `Felipecassani/simulador-energetico` · Branch: `main`
   - Main file path: `simulador-energia/app.py`
   - App URL: o nome que quiseres (ex.: `simulador-energetico`)
3. **Advanced settings**: Python **3.14**; em **Secrets** cola o conteúdo de
   `simulador-energia/.streamlit/secrets.toml` (a palavra-passe). Sem isto, quem entra vê
   "acesso fechado". Se a app for privada e não quiseres palavra-passe, cola antes
   `[acesso]` e `exigir = false`.
4. **Deploy** (2–5 min na 1.ª vez). Depois, em *Share*, convida os testadores por email.
- O Cloud lê a configuração de `.streamlit/config.toml` **na raiz** (cópia da do simulador; um
  teste avisa se ficarem diferentes) e as dependências de `simulador-energia/requirements.txt`.
- Cada `git push` atualiza o site sozinho. Grátis: 1 app privada, ~1 GB de memória, adormece
  após 12 h sem visitas (acorda ao abrir). Faturas: só PDF (as fotos precisam do macOS).
