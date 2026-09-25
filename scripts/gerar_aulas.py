import csv, io, json, os, re, unicodedata, urllib.request

TIPOS = {"aula", "secao", "card", "citacao", "subtitulo", "cooperativa", "referencia", "recurso"}
CORES = {"petroleo-escuro", "petroleo", "laranja", "dourado", "verde"}
# Bases que um bloco "referencia" pode citar. Os arquivos ficam neste mesmo
# repositório (jsonucops) e são gerados antes das aulas no workflow.
BASES = {
    "glossario": "glossario.json",
    "calendario": "eventos.json",
    "acervo": "artigos.json",
    "referencias": "referencias.json",
    "personas": "personalidades.json",
    "entidades": "entidades.json",
    "legislacao": "legislacao.json",
}
avisos = []

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()

def lista(v):
    return [x.strip() for x in re.split(r"[,;\n]+", v or "") if x.strip()]

def sim(v):
    return (v or "").strip().lower() in ("sim", "s", "x", "true", "1")

def ler_links(v, onde):
    out = []
    for linha in (v or "").splitlines():
        linha = linha.strip()
        if not linha:
            continue
        rotulo, _, url = linha.rpartition("|")
        url, rotulo = url.strip(), rotulo.strip()
        if not url.lower().startswith(("http://", "https://")):
            avisos.append(f"{onde}: link sem http ignorado: {linha}")
            continue
        out.append({"texto": rotulo, "url": url})
    return out

with urllib.request.urlopen(os.environ["CSV_URL"]) as r:
    texto_csv = r.read().decode("utf-8")

aulas, ordem = {}, []
for n, linha in enumerate(csv.DictReader(io.StringIO(texto_csv)), start=2):
    l = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
    aid, tipo = l.get("aula_id", ""), l.get("tipo_bloco", "").lower()
    if not aid and not tipo:
        continue
    onde = f"Linha {n} ({aid}, {tipo})"
    if not aid:
        avisos.append(f"{onde}: sem aula_id, ignorada"); continue
    if tipo not in TIPOS:
        avisos.append(f"{onde}: tipo_bloco '{tipo}' não existe, ignorada"); continue

    if aid not in aulas:
        aulas[aid] = {"id": aid, "publicar": True, "secoes": [], "recursos": [], "_secoes": {}, "_ocultas": set()}
        ordem.append(aid)
    a = aulas[aid]
    publicar = l.get("publicar", "sim").lower() != "não" and l.get("publicar", "sim").lower() != "nao"
    try:
        num = int(float(l.get("secao") or 0))
    except ValueError:
        num = 0

    if tipo == "aula":
        a.update({"titulo": l.get("titulo", ""), "rotulo": l.get("rotulo", ""), "complemento": l.get("complemento", ""),
                  "resumo": l.get("resumo", ""), "tags": lista(l.get("tags")), "buscar_tags": lista(l.get("buscar_tags")),
                  "imagem": l.get("imagem", ""), "evidenciar": sim(l.get("evidenciar")), "publicar": publicar})
        continue

    if tipo == "secao":
        if not num:
            avisos.append(f"{onde}: seção sem número, ignorada"); continue
        if not publicar:
            a["_ocultas"].add(num); continue
        cor = l.get("cor", "").lower()
        if cor and cor not in CORES:
            avisos.append(f"{onde}: cor '{cor}' não existe, usei petroleo")
            cor = "petroleo"
        s = {"numero": num, "titulo": l.get("titulo", ""), "rotulo": l.get("rotulo", ""), "cor": cor or "petroleo",
             "tags": lista(l.get("tags")), "evidenciar": sim(l.get("evidenciar")), "blocos": []}
        a["_secoes"][num] = s
        a["secoes"].append(s)
        continue

    if not publicar:
        continue

    if tipo == "recurso":
        links = ler_links(l.get("links"), onde)
        if not links:
            avisos.append(f"{onde}: recurso sem link, ignorado"); continue
        a["recursos"].append({"titulo": l.get("titulo", "") or links[0]["texto"] or links[0]["url"],
                              "rotulo": l.get("rotulo", ""), "url": links[0]["url"], "tags": lista(l.get("tags"))})
        continue

    if num in a["_ocultas"]:
        continue
    if num not in a["_secoes"]:
        avisos.append(f"{onde}: seção {num} não existe (falta a linha secao antes deste bloco), ignorado"); continue

    bloco = {"tipo": tipo}
    for campo in ("titulo", "texto", "fonte", "imagem"):
        if l.get(campo):
            bloco[campo] = l[campo]
    links = ler_links(l.get("links"), onde)
    if links:
        bloco["links"] = links
    if l.get("tags"):
        bloco["tags"] = lista(l["tags"])
    if sim(l.get("evidenciar")):
        bloco["evidenciar"] = True
    if tipo == "referencia":
        base = l.get("base", "").lower()
        ids = lista(l.get("ref_id"))
        if base not in BASES or not ids:
            avisos.append(f"{onde}: referência precisa de base (" + ", ".join(BASES) + ") e ref_id, ignorada"); continue
        bloco["base"], bloco["ids"] = base, ids
    a["_secoes"][num]["blocos"].append(bloco)

# Confere se os ids das referências existem nos outros JSON
existentes = {}
for base, arquivo in BASES.items():
    try:
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
        ids = set()
        for item in dados:
            i = str(item.get("id", ""))
            if i:
                ids.add(i)
                ids.add(re.sub(r"-\d{4}$", "", i))  # eventos anuais: lei-5764-2026 vale como lei-5764
        if ids:  # o acervo ainda não tem coluna id; sem ids não há o que conferir
            existentes[base] = ids
    except Exception:
        avisos.append(f"Não consegui ler o JSON de {base} para conferir as referências")

saida = []
for aid in ordem:
    a = aulas[aid]
    if not a.get("publicar", True):
        continue
    if "titulo" not in a:
        avisos.append(f"Aula {aid}: falta a linha do tipo aula")
    for s in a["secoes"]:
        for b in s["blocos"]:
            if b["tipo"] == "referencia" and b["base"] in existentes:
                for i in b["ids"]:
                    if i not in existentes[b["base"]]:
                        avisos.append(f"Aula {aid}, seção {s['numero']}: id '{i}' não encontrado em {b['base']}")
    for k in ("_secoes", "_ocultas", "publicar"):
        a.pop(k, None)
    saida.append(a)

with open("aulas.json", "w", encoding="utf-8") as f:
    json.dump(saida, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
print(f"{len(saida)} aula(s) gravada(s) em aulas.json")
