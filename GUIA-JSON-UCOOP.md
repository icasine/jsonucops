# Guia dos JSON do ucoop (repositório jsonucops)

Este guia explica a outra conversa como os HTML do site ucoop.com.br devem ler os JSON gerados pelo repositório `icasine/jsonucops`. Vale para adaptar um HTML existente, para criar um novo e para páginas que usam várias bases ao mesmo tempo.

## 1. Origem e atualização

Todos os JSON vêm da planilha unificada "jsonucops _uni" (Google Sheets). Cada aba vira um arquivo. Um GitHub Action atualiza tudo 4 vezes ao dia (0h, 6h, 12h e 18h de Brasília).

Endereço de cada arquivo:

```
https://raw.githubusercontent.com/icasine/jsonucops/main/<arquivo>.json
```

| Aba | Arquivo | Coluna de id | Prefixo do id |
|---|---|---|---|
| Aulas | aulas.json | aula_id | (livre, ex.: coop-aula-01) |
| Glossário | glossario.json | id_glossario | glo- |
| Acervo | acervo.json | id_acervo | ace- |
| Entidades | entidades.json | id_entidade | ent- |
| Personalidades | personalidades.json | id_persona | per- |
| Políticas | politicas.json | id_politica | pol- |
| Dados | dados.json | id_dados | dad- |
| Referências | referencias.json | id_referencia | ref- |
| Eventos | eventos.json | id_evento | eve- |
| Histórias | historias.json | id_historia | his- |
| Tese | tese.json | id_tese (a definir) | (a definir) |

Os arquivos `artigos.json` e `legislacao.json` são do formato antigo e não são mais atualizados. Nenhum HTML novo deve usá-los.

## 2. Regra de ouro

As chaves do JSON são exatamente os nomes das colunas da planilha, sem tradução. Só a coluna `obs_internas` fica de fora. Se a planilha ganhar uma coluna nova, ela aparece sozinha no JSON com o mesmo nome. O HTML é que se adapta à planilha, nunca o contrário.

Cada arquivo é uma lista (array) de objetos. Cada objeto é uma linha da planilha. Aulas e Histórias são exceção, porque agrupam várias linhas (ver seções 5 e 6).

## 3. Tipos dos valores

O conteúdo vai como está escrito na planilha. Só o tipo de algumas colunas é ajustado:

| Colunas | Vira | Exemplo no JSON |
|---|---|---|
| tags, temas, relacionados, referencias, glossario, relacionadas, outros_ids, ref_id, buscar_tags, publico | lista de textos | `["mulher", "inclusão"]` |
| link, links | lista de objetos | `[{"texto": "Site", "url": "https://..."}]` |
| evidenciar, destaque, historico, relembrar, conferido | true ou false | `true` |
| ano, ano_fundacao, ano_fim, ano_inicio, recorrencia_ate, latitude, longitude, cooperativas, cooperados, empregos, pac, nota_prof, ordem, secao | número ou null | `1844`, `-24.27` |
| todas as outras | texto | `"Regulação"` |

Cuidados para o HTML:

1. Célula vazia vira `""` (texto), `[]` (lista), `false` (sim/não) ou `null` (número). Sempre tratar o vazio antes de exibir.
2. `link` e `links` são sempre listas. Para um link só, usar `item.link[0]?.url`. Se o texto não tiver rótulo, `texto` vem igual à url.
3. `publicar` vai como texto ("sim", "não" ou vazio). O script já tirou as linhas não publicadas, então o HTML não precisa filtrar por ela.
4. Os valores de categoria vêm por extenso, como na planilha (ex.: grupo do glossário "Regulação", "Fundamentos"; origem "Nacional", "Internacional"). Filtros e cores no HTML devem usar esses textos.
5. Textos podem ter quebras de linha (`\n`). Para exibir, trocar por `<br>` ou usar `white-space: pre-line`.
6. Em referencias, `referencia` pode ter `**negrito**` em markdown simples, que o HTML precisa converter.

## 4. Campos de cada base (uma linha por item)

glossario.json: id_glossario, titulo, abbr, grupo, texto, nota, fonte, tags, relacionados, links, referencia_ucoop, ref_imagem, imagem, evidenciar, conferido, publicar. `relacionados` traz ids ou títulos de outros termos.

acervo.json: id_acervo, titulo, titulo_orig, tipo, origem, ano, autores, temas, tags, link, link_compra, fonte, evidenciar, conferido, publicar. Quando `link` vier vazio, o HTML pode montar uma busca no Google com titulo_orig (ou titulo) e autores.

entidades.json: id_entidade, titulo, nome_oficial, categoria, tipo, grau, ramo, resumo, descricao, situacao, ano_fundacao, ano_fim, pais, uf, municipio, endereco, latitude, longitude, mapa, google_maps, tags, referencias, link, fonte, ref_imagem, imagem, evidenciar, conferido, publicar. `mapa` é a camada do mapa (ex.: "Crédito", "História"). `referencias` traz ids de outras bases.

personalidades.json: id_persona, titulo, genero, resumo, descricao, categoria, origem, pais, historico, destaque, nascimento, falecimento, tags, link, fonte, ref_imagem, imagem, conferido, publicar. nascimento e falecimento são texto (podem ter "1976?"). Para calcular a idade, extrair o ano no HTML.

politicas.json: id_politica, titulo, sigla, tema, nivel, orgao, norma_origem, localidade, texto, importancia, nota_prof, comentario, situacao, data_criacao, ano_inicio, data_revogacao, ano_fim, tags, glossario, relacionadas, outros_ids, links, ref_imagem, imagem, nota, evidenciar, conferido, publicar. data_criacao e data_revogacao estão em dd/mm/aaaa. `glossario` traz ids do glossário, `relacionadas` ids de outras políticas e `outros_ids` ids de qualquer base.

dados.json: id_dados, ano, ramo, origem, nivel, pais, estado, cidade, cooperativas, cooperados, empregos, pac, tags, ref_id, ref_tipo, link, fonte, nota, conferido, publicar. O total do Brasil vem com ramo "Geral".

referencias.json: id_referencia, referencia, tipo, ano, tags, link, nota, evidenciar, conferido, publicar.

eventos.json: id_evento, titulo, tipo, categoria, resumo, descricao, data_inicio, data_fim, recorrencia, recorrencia_ate, substitui, local, tags, link, fonte, ref_imagem, imagem, evidenciar, relembrar, conferido, publicar. Além das colunas, o script acrescenta campos calculados:

| Campo | Significado |
|---|---|
| ano, mes, dia | lidos de data_inicio ("21-dez-1844", "jun-2003", "1825") |
| precisao | "dia", "mes" ou "ano" |
| start, end, allDay | só quando há dia; formato ISO para o FullCalendar; `end` é exclusivo (dia seguinte ao fim) |
| ano_fim_num | ano lido de data_fim |
| ano_origem, edicao | só nos eventos anuais repetidos |

Eventos com recorrencia "anual" aparecem uma vez por ano, com id `id_evento-AAAA` (ex.: eve-rochdale-1844-2026). Eventos sem dia completo não têm `start` e servem para linha do tempo e "nesta data". Para o FullCalendar, usar `title: e.titulo` e passar o restante em `extendedProps`.

tese.json: ainda sem colunas definidas. Hoje é `[]`. Cada linha virá com as colunas que a aba tiver. O HTML deve aceitar a lista vazia.

## 5. aulas.json (agrupado)

```
[
  {
    "aula_id": "coop-aula-01",
    ...colunas da linha tipo_bloco = "aula" (titulo, rotulo, complemento, resumo, tags, buscar_tags, imagem, ref_imagem, evidenciar...),
    "secoes": [
      {
        "secao": 1,
        ...colunas da linha "secao" (titulo, rotulo, cor, tags, evidenciar...),
        "blocos": [ { "tipo_bloco": "card", "titulo": "...", "texto": "..." }, ... ]
      }
    ],
    "recursos": [ { "tipo_bloco": "recurso", "titulo": "...", "links": [...] } ]
  }
]
```

Tipos de bloco: card, citacao, subtitulo, cooperativa, referencia. Nos blocos e recursos só vêm as colunas preenchidas, então sempre testar se a chave existe. `cor` da seção: petroleo-escuro, petroleo, laranja, dourado, verde.

Bloco `referencia`: tem `base` e `ref_id` (lista). O HTML busca cada id no arquivo da base indicada (ver seção 7). Valores aceitos em `base`: glossario, calendario ou eventos, acervo, referencias, personalidades, entidades, politicas, dados, historias, tese.

## 6. historias.json (agrupado)

```
[
  {
    "id_historia": "his-002",
    ...colunas da linha tipo_bloco = "historia" (ordem, titulo, resumo, imagem, imagem_alt, legenda, capa, publico, genero, nivel, tema, tags, autor, fonte, links, evidenciar...),
    "anterior": null,           // id da história anterior ou null
    "proxima": "his-003",       // id da próxima ou null
    "personagens": [ { "personagem": "Lia", "imagem": "menina", "voz": "narrador" } ],
    "blocos": [ { "tipo_bloco": "narracao", "texto": "...", "voz": "narrador" }, ... ]
  }
]
```

A lista já vem ordenada por `ordem`, e os blocos de cada história já vêm na ordem de `ordem_bloco`. Tipos de bloco: cena (imagem, imagem_alt, legenda), narracao (texto, voz), fala (texto, personagem, voz), professor (titulo, texto; não narrado), licao (titulo, texto), referencia (titulo, texto; com base "glossario" e ref_id para as Palavras da história). Em personagens, `imagem` é o tipo do bonequinho (senhor, senhora, homem, mulher, menino, menina). A imagem completa da história é a `imagem` da própria história.

## 7. Páginas que usam vários JSON

Carregar tudo em paralelo e montar um índice por id, que serve para todas as ligações entre bases:

```js
const RAIZ = "https://raw.githubusercontent.com/icasine/jsonucops/main/";
const ARQUIVOS = {
  glossario: "glossario.json", eventos: "eventos.json", calendario: "eventos.json",
  acervo: "acervo.json", referencias: "referencias.json", personalidades: "personalidades.json",
  entidades: "entidades.json", politicas: "politicas.json", dados: "dados.json",
  aulas: "aulas.json", historias: "historias.json", tese: "tese.json"
};

// a chave de id de cada item é a que começa com "id_" (ou "aula_id")
const idDe = item => item[Object.keys(item).find(k => k.startsWith("id_") || k === "aula_id")];

async function carregar(bases) {
  const dados = {};
  await Promise.all(bases.map(async b => {
    try {
      const r = await fetch(RAIZ + ARQUIVOS[b] + "?v=" + Date.now().toString().slice(0, -5)); // evita cache velho
      dados[b] = r.ok ? await r.json() : [];
    } catch { dados[b] = []; }      // se uma base falhar, a página continua
  }));
  return dados;
}

function indexar(dados) {
  const porId = {};
  for (const [base, lista] of Object.entries(dados))
    for (const item of lista) {
      const id = idDe(item);
      if (id) porId[id] = { base, item };
    }
  return porId;
}

// eventos anuais: "eve-x-2026" também responde por "eve-x"
const achar = (porId, id) => porId[id] || porId[Object.keys(porId).find(k => k.replace(/-\d{4}$/, "") === id)];
```

Como os prefixos dos ids são únicos (glo-, ace-, ent-, per-, pol-, dad-, ref-, eve-, his-), um índice só para todas as bases funciona sem conflito, e o prefixo diz de qual base o id veio.

Ligações que existem entre bases:

| Onde | Campo | Aponta para |
|---|---|---|
| aulas (bloco referencia) | base + ref_id | a base indicada |
| historias (bloco referencia) | base + ref_id | glossario |
| historias | anterior, proxima | outras histórias |
| glossario | relacionados | outros termos (id ou título) |
| politicas | glossario | glossario |
| politicas | relacionadas | outras políticas |
| politicas | outros_ids | qualquer base |
| entidades | referencias | qualquer base |
| dados | ref_id + ref_tipo | a base indicada em ref_tipo |

## 8. Ao adaptar ou criar um HTML

1. Ler este guia e abrir o JSON real no endereço raw para conferir os campos.
2. Usar os nomes das colunas tal como estão. Não renomear campos no HTML.
3. Tratar vazio, `null` e listas vazias em todos os campos.
4. Tratar `link` e `links` como listas de `{texto, url}`.
5. Filtros e legendas usam os valores por extenso da planilha.
6. Mostrar `ref_imagem` como crédito ou fonte da imagem quando existir.
7. `conferido` pode servir para um selo de "conferido", mas não deve esconder itens.
8. Usar `evidenciar` (ou `destaque` em personalidades) para destaques.
9. Se a página usa várias bases, usar o carregamento da seção 7, e nunca deixar uma base que falhou derrubar a página.
10. Quando surgir uma aba nova na planilha, o padrão é o mesmo: arquivo `<aba>.json`, id na coluna `id_<algo>` e as chaves iguais às colunas.

## 9. Ponto de encaixe para o editor da planilha (teste ao vivo)

O editor da planilha (Apps Script) baixa o HTML publicado da página e troca os dados do GitHub pelos dados atuais da planilha, para testar sem mexer no HTML. Para isso funcionar em qualquer página, todo HTML segue este contrato.

### 9.1 O que o HTML precisa ter

1. Um marcador vazio logo depois de `<head>`, onde o editor injeta os dados:

```html
<head>
<!-- UCOOP_DADOS -->
```

2. Todo carregamento de JSON passa por uma única função, que primeiro procura os dados injetados e só depois busca no GitHub:

```js
async function carregarBase(base) {
  if (window.UCOOP_DADOS && window.UCOOP_DADOS[base]) return window.UCOOP_DADOS[base]; // teste no editor
  try {
    const r = await fetch(RAIZ + ARQUIVOS[base] + "?v=" + Date.now().toString().slice(0, -5));
    return r.ok ? await r.json() : [];
  } catch { return []; }
}
```

A função `carregar(bases)` da seção 7 deve chamar `carregarBase` para cada base. Nenhum outro `fetch` de JSON pode existir na página, senão aquela parte não será substituída no teste.

3. O nome da base usado no HTML é o nome do arquivo sem `.json` (glossario, eventos, acervo, entidades, personalidades, politicas, dados, referencias, aulas, historias, tese).

4. Opcional: um aviso visual de modo teste, para não confundir com a página real:

```js
if (window.UCOOP_DADOS) document.documentElement.dataset.teste = "sim";
```

### 9.2 O que o editor faz

1. Baixa o HTML publicado da página.
2. Monta um objeto só com as bases que a página usa (ou todas), cada uma no mesmo formato do JSON do GitHub.
3. Troca o marcador `<!-- UCOOP_DADOS -->` por:

```html
<script>window.UCOOP_DADOS = { "glossario": [...], "eventos": [...] };</script>
```

4. Mostra o HTML resultante na prévia.

Se uma base não for injetada, a página busca a versão do GitHub normalmente. Assim dá para testar só a aba que mudou.

### 9.3 Regras que o editor precisa repetir

Para o teste ser fiel, o editor precisa gerar os dados com as mesmas regras dos scripts do jsonucops:

1. Chaves iguais às colunas. Tirar só `obs_internas`.
2. Tipos da seção 3: listas separadas por `;`, `,` ou quebra de linha; `link`/`links` em lista de `{texto, url}` (uma linha por link, "rótulo | url"); sim/não em true/false; números com vírgula decimal e ponto de milhar ("3.947" = 3947).
3. Linhas publicadas: em glossário, entidades, políticas, dados, referências e acervo só entra `publicar` = sim. Nas outras abas só sai `publicar` = não.
4. Aulas e histórias agrupadas como nas seções 5 e 6, com blocos só com as colunas preenchidas.
5. Eventos com os campos calculados da seção 4, ao menos `ano`, `mes`, `dia`, `precisao` e `start`.

Repetir as regras no editor é o que permite ao HTML nunca precisar saber se está em teste: a página real e a prévia recebem dados idênticos no formato.

As regras de geração ficam em `scripts/comum.py` (tipos), `scripts/simples.py` (bases de uma linha por item), `scripts/gerar_eventos.py`, `scripts/gerar_aulas.py` e `scripts/gerar_historias.py`.
