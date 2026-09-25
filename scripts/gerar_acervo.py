import csv, io, json, os, urllib.parse, urllib.request

ORIGENS = {"nacional": "N", "internacional": "I", "n": "N", "i": "I"}
avisos = []

def sim(v):
    return (v or "").strip().lower() in ("sim", "s", "x", "true", "1")

with urllib.request.urlopen(os.environ["CSV_URL"]) as r:
    texto_csv = r.read().decode("utf-8")

itens = []
for n, linha in enumerate(csv.DictReader(io.StringIO(texto_csv)), start=2):
    l = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
    if not l.get("titulo_pt"):
        continue
    if l.get("publicar", "sim").lower() != "sim":
        continue

    titulo = l["titulo_pt"]
    try:
        ano = int(float(l.get("ano", "")))
    except ValueError:
        ano = 0
        avisos.append(f"Linha {n} ({titulo[:50]}): ano vazio ou inválido")

    origem = ORIGENS.get(l.get("origem", "").lower())
    if not origem:
        avisos.append(f"Linha {n} ({titulo[:50]}): origem '{l.get('origem')}' não reconhecida, usei Internacional")
        origem = "I"

    tipo = l.get("tipo") or "Artigo científico"
    temas = [t.strip() for t in l.get("temas", "").replace(",", ";").split(";") if t.strip()]
    autores, fonte = l.get("autores", ""), l.get("fonte", "")

    fonte_ano = ", ".join(x for x in (fonte, str(ano) if ano else "") if x)
    meta = " · ".join(x for x in (autores, fonte_ano) if x)

    url = l.get("url", "")
    if url and not url.lower().startswith(("http://", "https://")):
        avisos.append(f"Linha {n} ({titulo[:50]}): url sem http, troquei pela busca no Google")
        url = ""
    if not url:
        busca = f'"{l.get("titulo_orig") or titulo}" {autores}'.strip()
        url = "https://www.google.com/search?q=" + urllib.parse.quote(busca)

    item = {"tipo": tipo, "origem": origem, "ano": ano, "temas": temas,
            "titulo_pt": titulo, "titulo_orig": l.get("titulo_orig", ""),
            "meta": meta, "url": url}

    compra = l.get("link_compra", "")
    if compra:
        if compra.lower().startswith(("http://", "https://")):
            item["link_compra"] = compra
        else:
            avisos.append(f"Linha {n} ({titulo[:50]}): link_compra sem http, ignorado")
    if sim(l.get("evidenciar")):
        item["evidenciar"] = True

    itens.append(item)

itens.sort(key=lambda i: (-i["ano"], i["titulo_pt"].lower()))

with open("artigos.json", "w", encoding="utf-8") as f:
    json.dump(itens, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
print(f"{len(itens)} publicações gravadas em artigos.json ({sum(1 for i in itens if i.get('evidenciar'))} em destaque)")
