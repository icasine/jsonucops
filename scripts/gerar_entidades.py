import csv, io, json, os, re, unicodedata, urllib.request

avisos = []

# Arquivos deste repositório usados para conferir a coluna "referencias"
OUTRAS_BASES = ("referencias.json", "personalidades.json", "glossario.json")


def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")


def lista(v):
    return [x.strip() for x in re.split(r"[,;\n]+", v or "") if x.strip()]


def sim(v):
    return (v or "").strip().lower() in ("sim", "s", "x", "true", "1")


def ano(v, onde, campo):
    if not v:
        return None
    m = re.search(r"-?\d{3,4}", v)
    if not m:
        avisos.append(f"{onde}: {campo} '{v}' não é um ano, ignorado")
        return None
    return int(m.group(0))


def coord(v, onde, campo, limite):
    """Aceita -24,284 ou -24.284 (vírgula ou ponto como decimal)."""
    if not v:
        return None
    try:
        n = float(v.replace(" ", "").replace(",", "."))
    except ValueError:
        avisos.append(f"{onde}: {campo} '{v}' inválida, ignorada")
        return None
    if not -limite <= n <= limite:
        avisos.append(f"{onde}: {campo} {n} fora do intervalo, ignorada")
        return None
    return n


def ler_links(v, onde):
    """Uma linha por link. Aceita 'rótulo | url' ou só a url."""
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

itens, ids = [], set()
for n, linha in enumerate(csv.DictReader(io.StringIO(texto_csv)), start=2):
    l = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
    titulo = l.get("titulo", "")
    if not titulo and not l.get("id"):
        continue
    if not sim(l.get("publicar")):
        continue

    onde = f"Linha {n} ({titulo or l.get('id')})"
    if not titulo:
        avisos.append(f"{onde}: sem titulo, ignorada")
        continue

    ident = l.get("id") or "ent-" + slug(titulo)
    if not l.get("id"):
        avisos.append(f"{onde}: sem id, usei '{ident}'")
    if ident in ids:
        avisos.append(f"{onde}: id '{ident}' repetido, linha ignorada")
        continue

    lat = coord(l.get("latitude"), onde, "latitude", 90)
    lng = coord(l.get("longitude"), onde, "longitude", 180)
    if (lat is None) != (lng is None):
        avisos.append(f"{onde}: só uma das coordenadas preenchida, ficou fora do mapa")
        lat = lng = None

    ano_fundacao = ano(l.get("ano_fundacao"), onde, "ano_fundacao")
    ano_fim = ano(l.get("ano_fim"), onde, "ano_fim")
    if ano_fundacao and ano_fim and ano_fim < ano_fundacao:
        avisos.append(f"{onde}: ano_fim ({ano_fim}) anterior ao ano_fundacao ({ano_fundacao})")

    imagem = l.get("imagem", "")
    if imagem and not imagem.lower().startswith(("http://", "https://")):
        avisos.append(f"{onde}: imagem sem http, ignorada")
        imagem = ""

    links = ler_links(l.get("link"), onde)

    item = {
        "id": ident,
        "titulo": titulo,
        "nome_oficial": l.get("nome_oficial", ""),
        "categoria": l.get("categoria", ""),
        "tipo": l.get("tipo", ""),
        "grau": l.get("grau", ""),
        "ramo": l.get("ramo", ""),
        "tags": lista(l.get("tags")),
        "ano_fundacao": ano_fundacao,
        "ano_fim": ano_fim,
        "situacao": l.get("situacao", ""),
        "pais": l.get("pais", ""),
        "uf": l.get("uf", ""),
        "municipio": l.get("municipio", ""),
        "endereco": l.get("endereco", ""),
        "latitude": lat,
        "longitude": lng,
        "resumo": l.get("resumo", ""),
        "descricao": l.get("descricao", ""),
        "link": links[0]["url"] if links else "",
        "links": links,
        "imagem": imagem,
        "fonte": l.get("fonte", ""),
        "referencias": lista(l.get("referencias")),
        "mapa": l.get("mapa", ""),
        "evidenciar": sim(l.get("evidenciar")),
    }

    if not item["resumo"]:
        avisos.append(f"{onde}: sem resumo")

    ids.add(ident)
    itens.append(item)

# Confere se as referências cruzadas existem (nas entidades ou nas outras bases)
conhecidos = set(ids)
for arquivo in OUTRAS_BASES:
    try:
        with open(arquivo, encoding="utf-8") as f:
            conhecidos |= {str(i.get("id", "")) for i in json.load(f) if i.get("id")}
    except Exception:
        pass
for i in itens:
    for ref in i["referencias"]:
        if ref not in conhecidos:
            avisos.append(f"{i['id']}: referência '{ref}' não encontrada")

itens.sort(key=lambda i: norm(i["titulo"]))

with open("entidades.json", "w", encoding="utf-8") as f:
    json.dump(itens, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
sem_mapa = sum(1 for i in itens if i["latitude"] is None)
print(f"{len(itens)} entidade(s) gravada(s) em entidades.json ({sem_mapa} sem coordenadas)")
