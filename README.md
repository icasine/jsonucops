# jsonucops

Gera, todo dia às 6h (Brasília), os arquivos JSON do site ucoop.com.br a partir das planilhas publicadas no Google Sheets. Tudo roda num único workflow: `.github/workflows/atualizar-jsons.yml`.

| Planilha | Script | Arquivo gerado | Link para o site |
|---|---|---|---|
| Glossário | `scripts/gerar_glossario.py` | `glossario.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/glossario.json |
| Calendário | `scripts/gerar_eventos.py` | `eventos.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/eventos.json |
| Acervo | `scripts/gerar_acervo.py` | `artigos.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/artigos.json |
| Referências | `scripts/gerar_referencias.py` | `referencias.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/referencias.json |
| Personas | `scripts/gerar_personalidades.py` | `personalidades.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/personalidades.json |
| Dados | `scripts/gerar_dados.py` | `dados.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/dados.json |
| Entidades | `scripts/gerar_entidades.py` | `entidades.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/entidades.json |
| Aulas | `scripts/gerar_aulas.py` | `aulas.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/aulas.json |

## Como funciona

- Os links CSV das planilhas ficam no topo do workflow (bloco `env`). Não é preciso cadastrar segredos.
- Cada planilha é processada num passo separado. Se uma falhar, as outras seguem e o JSON antigo dela continua valendo; o workflow termina em vermelho dizendo qual falhou.
- Entidades e aulas rodam por último porque conferem ids nos outros JSONs (as aulas podem citar `glossario`, `calendario`, `acervo`, `referencias`, `personas` e `entidades` na coluna `base`).
- Linhas com `publicar` diferente de "sim" ficam fora. A coluna `obs_internas` nunca vai para o JSON.
- Avisos (id repetido, link sem http, referência inexistente etc.) aparecem no resumo da execução, em Actions.

Para rodar na hora: Actions > Atualizar JSONs das planilhas > Run workflow.
