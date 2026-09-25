import csv, io, json, os, re, unicodedata, urllib.request

GRUPOS = {"base", "org", "estrut", "econ", "ramos", "hist", "reg"}
avisos = []

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")

with urllib.request.urlopen(os.environ["CSV_URL"]) as r:
    texto_csv = r.read().decode("utf-8")

itens, ids = [], set()
for n, linha in enumerate(csv.DictReader(io.StringIO(texto_csv)), start=2):
    l = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
    if l.get("publicar", "").lower() != "sim" or not l.get("termo"):
        continue

    ident = l.get("id") or slug(l["termo"])
    if not l.get("id"):
        avisos.append(f"Linha {n} ({l['termo']}): sem id, usei '{ident}'")
    if ident in ids:
        avisos.append(f"Linha {n} ({l['termo']}): id '{ident}' repetido, linha ignorada")
        continue

    grupo = l.get("grupo", "").lower()
    if grupo not in GRUPOS:
        avisos.append(f"Linha {n} ({l['termo']}): grupo '{grupo}' não existe, linha ignorada")
        continue

    if not l.get("texto"):
        avisos.append(f"Linha {n} ({l['termo']}): sem texto")

    item = {"id": ident, "termo": l["termo"], "grupo": grupo, "texto": l.get("texto", "")}
    for campo in ("abbr", "links", "relacionados", "nota", "tags", "evidenciar", "imagem"):
        if l.get(campo):
            item[campo] = l[campo]

    for link in item.get("links", "").splitlines():
        url = link.rsplit("|", 1)[-1].strip()
        if link.strip() and not url.lower().startswith(("http://", "https://")):
            avisos.append(f"Linha {n} ({l['termo']}): link sem http, será ignorado no site: {link.strip()}")

    ids.add(ident)
    itens.append(item)

# Confere se os termos relacionados existem no glossário
conhecidos = {norm(i["id"]) for i in itens} | {norm(i["termo"]) for i in itens}
for i in itens:
    for rel in re.split(r"[,;\n]+", i.get("relacionados", "")):
        if rel.strip() and norm(rel) not in conhecidos:
            avisos.append(f"{i['termo']}: relacionado '{rel.strip()}' não encontrado no glossário")

with open("glossario.json", "w", encoding="utf-8") as f:
    json.dump(itens, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
print(f"{len(itens)} termos gravados em glossario.json")
