# jsonucops

Gera, 4 vezes por dia, às 0h, 6h, 12h e 18h (Brasília), os arquivos JSON do site ucoop.com.br a partir das planilhas publicadas no Google Sheets. Tudo roda num único workflow: `.github/workflows/atualizar-jsons.yml`.

| Planilha | Script | Arquivo gerado | Link para o site |
|---|---|---|---|
| Glossário | `scripts/gerar_glossario.py` | `glossario.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/glossario.json |
| Eventos | `scripts/gerar_eventos.py` | `eventos.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/eventos.json |
| Acervo | `scripts/gerar_acervo.py` | `acervo.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/acervo.json |
| Referências | `scripts/gerar_referencias.py` | `referencias.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/referencias.json |
| Personalidades | `scripts/gerar_personalidades.py` | `personalidades.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/personalidades.json |
| Dados | `scripts/gerar_dados.py` | `dados.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/dados.json |
| Políticas | `scripts/gerar_politicas.py` | `politicas.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/politicas.json |
| Entidades | `scripts/gerar_entidades.py` | `entidades.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/entidades.json |
| Aulas | `scripts/gerar_aulas.py` | `aulas.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/aulas.json |
| Tese (colunas a definir) | `scripts/gerar_tese.py` | `tese.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/tese.json |
| Histórias | `scripts/gerar_historias.py` | `historias.json` | https://raw.githubusercontent.com/icasine/jsonucops/main/historias.json |

## Padrão dos JSON

- As chaves de cada item são exatamente os nomes das colunas da planilha. Só a coluna `obs_internas` fica de fora.
- Listas (`tags`, `temas`, `ref_id`, `relacionados`, `referencias`, `glossario`, `relacionadas`, `outros_ids`, `buscar_tags`, `publico`) viram listas; separe por `;`, `,` ou quebra de linha.
- `link` e `links` viram lista de `{"texto", "url"}` (uma linha por link, `rótulo | url` ou só a url).
- `evidenciar`, `destaque`, `historico`, `relembrar` e `conferido` viram true/false. Anos, coordenadas e quantidades viram número.
- Eventos ganham campos calculados (`ano`, `mes`, `dia`, `precisao`, `start`, `end`, `allDay`, `ano_fim_num`); os anuais são repetidos com `id_evento-AAAA`.
- Aulas e histórias são agrupadas (seções/blocos, personagens/blocos); nos blocos só vão as colunas preenchidas.
- As regras comuns estão em `scripts/comum.py`; as abas de um item por linha usam `scripts/simples.py`.
- `artigos.json` e `legislacao.json` são do formato antigo e não são mais atualizados.

## Como funciona

- Os links CSV das abas ficam no topo do workflow (bloco `env`). Não é preciso cadastrar segredos.
- Cada aba é processada num passo separado. Se uma falhar, as outras seguem e o JSON antigo dela continua valendo; o workflow termina em vermelho dizendo qual falhou.
- Aulas e histórias conferem os ids citados na coluna `base` + `ref_id` (glossario, calendario/eventos, acervo, referencias, personalidades, entidades, politicas, dados, historias, tese).
- Glossário, entidades, políticas, dados, referências e acervo só levam as linhas com `publicar` = sim; nas outras abas só fica fora `publicar` = não.
- Avisos (id repetido, link sem http, referência inexistente etc.) aparecem no resumo da execução, em Actions.

Para rodar na hora: Actions > Atualizar JSONs das planilhas > Run workflow.

Todas as abas vêm da planilha unificada.
