"""Gera historias.json a partir da aba Histórias.

Mesma lógica da aba Aulas: cada linha é um bloco, agrupado por id_historia
e ordenado por ordem_bloco (ou pela ordem das linhas). Tipos de bloco:
historia, personagem, cena, narracao, fala, professor, licao, referencia.
Referência com base "historias": 1º id = anterior, 2º = próxima ("-" = nenhuma).
"""
import csv, io, json, os, re, urllib.request
from comum import ajustar

TIPOS = {"historia", "personagem", "cena", "narracao", "fala", "professor", "licao", "referencia"}
BASES = {"glossario": "glossario.json", "historias": None, "aulas": "aulas.json",
         "personas": "personalidades.json", "personalidades": "personalidades.json",
         "entidades": "entidades.json", "referencias": "referencias.json", "acervo": "artigos.json"}
avisos = []


def lista(v):
    return [x.strip() for x in re.split(r"[,;\n]+", v or "") if x.strip()]


def sim(v):
    return (v or "").strip().lower() in ("sim", "s", "x", "true", "1")


def nao(v):
    return (v or "").strip().lower() in ("não", "nao", "n", "false", "0")


def numero(v):
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


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
        out.append({"texto": rotulo or url, "url": url})
    return out


with urllib.request.urlopen(os.environ["CSV_URL"]) as r:
    texto_csv = r.read().decode("utf-8")

historias, ordem = {}, []
for n, linha in enumerate(csv.DictReader(io.StringIO(texto_csv)), start=2):
    l = ajustar({(k or "").strip(): (v or "").strip() for k, v in linha.items()}, "historias")
    hid, tipo = l.get("id_historia", ""), l.get("tipo_bloco", "").lower()
    if not hid and not tipo:
        continue
    onde = f"Linha {n} ({hid}, {tipo})"
    if not hid:
        avisos.append(f"{onde}: sem id_historia, ignorada"); continue
    if tipo not in TIPOS:
        avisos.append(f"{onde}: tipo_bloco '{tipo}' não existe, ignorada"); continue
    if hid not in historias:
        historias[hid] = {"id": hid, "_publicar": True, "_linhas": []}
        ordem.append(hid)
    h = historias[hid]

    if tipo == "historia":
        h["_publicar"] = not nao(l.get("publicar"))
        h.update({
            "ordem": numero(l.get("ordem")),
            "titulo": l.get("titulo", ""),
            "resumo": l.get("resumo", ""),
            "imagem": l.get("imagem", ""),
            "imagem_alt": l.get("imagem_alt", ""),
            "legenda": l.get("legenda", ""),
            "capa": l.get("capa", ""),
            "publico": lista(l.get("publico")),
            "genero": l.get("genero", ""),
            "nivel": l.get("nivel", ""),
            "tema": l.get("tema", ""),
            "tags": lista(l.get("tags")),
            "autor": l.get("autor", ""),
            "fonte": l.get("fonte", ""),
            "link": l.get("link", ""),
            "links": ler_links(l.get("links"), onde),
            "evidenciar": sim(l.get("evidenciar")),
            "anterior": None,
            "proxima": None,
            "personagens": [],
            "blocos": [],
        })
        continue
    if nao(l.get("publicar")):
        continue
    h["_linhas"].append((l.get("ordem_bloco") or "", n, tipo, l, onde))

saida = []
for hid in ordem:
    h = historias[hid]
    if not h.pop("_publicar"):
        continue
    linhas = h.pop("_linhas")
    if "titulo" not in h:
        avisos.append(f"História {hid}: falta a linha do tipo historia, ignorada"); continue
    # ordem_bloco quando preenchida; senão, a ordem das linhas na planilha
    linhas.sort(key=lambda x: (x[0] == "", x[0], x[1]))
    for _, n, tipo, l, onde in linhas:
        if tipo == "personagem":
            nome = l.get("personagem") or l.get("titulo")
            if not nome:
                avisos.append(f"{onde}: personagem sem nome, ignorado"); continue
            h["personagens"].append({"nome": nome, "tipo": l.get("imagem", ""), "voz": l.get("voz", "") or "narrador"})
            continue
        if tipo == "referencia" and l.get("base", "").lower() == "historias":
            ids = lista(l.get("ref_id"))
            vazio = lambda i: None if i in ("", "-") else i
            h["anterior"] = vazio(ids[0]) if len(ids) > 0 else None
            h["proxima"] = vazio(ids[1]) if len(ids) > 1 else None
            if l.get("titulo"):
                h["titulo_navegacao"] = l["titulo"]
            continue
        bloco = {"tipo": tipo}
        for campo in ("titulo", "texto", "voz", "personagem", "imagem", "imagem_alt", "legenda", "fonte"):
            if l.get(campo):
                bloco[campo] = l[campo]
        if tipo in ("narracao", "fala", "licao") and "voz" not in bloco:
            bloco["voz"] = "narrador"
        if tipo == "fala" and not l.get("personagem"):
            avisos.append(f"{onde}: fala sem personagem")
        links = ler_links(l.get("links"), onde)
        if links:
            bloco["links"] = links
        if tipo == "referencia":
            base = l.get("base", "").lower()
            if base:
                bloco["base"] = base
                bloco["ids"] = lista(l.get("ref_id"))
        if sim(l.get("evidenciar")):
            bloco["evidenciar"] = True
        h["blocos"].append(bloco)
    saida.append(h)

saida.sort(key=lambda h: (h["ordem"] is None, h["ordem"] or 0, h["titulo"].lower()))

# Confere anterior/próxima e as referências ao glossário
ids_hist = {h["id"] for h in saida}
for h in saida:
    for campo in ("anterior", "proxima"):
        if h[campo] and h[campo] not in ids_hist:
            avisos.append(f"História {h['id']}: {campo} '{h[campo]}' não encontrada (ou não publicada)")
cache = {}
for h in saida:
    for b in h["blocos"]:
        arq = BASES.get(b.get("base", ""))
        if not arq:
            continue
        if arq not in cache:
            try:
                with open(arq, encoding="utf-8") as f:
                    cache[arq] = {str(i.get("id", "")) for i in json.load(f)}
            except Exception:
                cache[arq] = None
        if cache[arq]:
            for i in b["ids"]:
                if i not in cache[arq]:
                    avisos.append(f"História {h['id']}: id '{i}' não encontrado em {b['base']}")

with open("historias.json", "w", encoding="utf-8") as f:
    json.dump(saida, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
print(f"{len(saida)} história(s) gravada(s) em historias.json")
