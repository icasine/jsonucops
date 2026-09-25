import csv, io, json, os, re, unicodedata, urllib.request

avisos = []

TEMAS = {"marco-legal", "credito-financiamento", "regulacao-setorial", "fomento", "comemorativa",
         "compras-publicas", "trabalho", "tributacao", "economia-solidaria", "educacao-formacao",
         "assistencia-tecnica", "institucional"}
NIVEIS = {"internacional", "federal", "estadual", "municipal"}
SITUACOES = {"vigente", "revogada", "superada", "extinta", "encerrada", "vetada", "sem execução"}
IMPORTANCIAS = {"alta", "média", "baixa"}


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
    m = re.search(r"\d{4}", v)
    if not m:
        avisos.append(f"{onde}: {campo} '{v}' não é um ano, ignorado")
        return None
    return int(m.group(0))


def data_iso(v, onde, campo):
    """Aceita dd/mm/aaaa (ou só aaaa) e devolve aaaa-mm-dd para ordenar no site."""
    if not v:
        return ""
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", v)
    if m:
        d, mes, a = (int(x) for x in m.groups())
        if 1 <= d <= 31 and 1 <= mes <= 12:
            return f"{a:04d}-{mes:02d}-{d:02d}"
    if re.fullmatch(r"\d{4}", v):
        return v
    avisos.append(f"{onde}: {campo} '{v}' fora do formato dd/mm/aaaa")
    return ""


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

    onde = f"Linha {n} ({l.get('id') or titulo})"
    if not titulo:
        avisos.append(f"{onde}: sem titulo, ignorada")
        continue

    ident = l.get("id") or slug(l.get("norma_origem") or titulo)
    if not l.get("id"):
        avisos.append(f"{onde}: sem id, usei '{ident}'")
    if ident in ids:
        avisos.append(f"{onde}: id '{ident}' repetido, linha ignorada")
        continue

    tema = norm(l.get("tema"))
    if tema and tema not in TEMAS:
        avisos.append(f"{onde}: tema '{tema}' fora da lista usual")
    nivel = norm(l.get("nivel"))
    if nivel and nivel not in NIVEIS:
        avisos.append(f"{onde}: nivel '{nivel}' fora da lista usual")
    situacao = l.get("situacao", "").lower()
    if situacao and situacao not in SITUACOES:
        avisos.append(f"{onde}: situacao '{situacao}' fora da lista usual")
    importancia = l.get("importancia", "").lower()
    if importancia and importancia not in IMPORTANCIAS:
        avisos.append(f"{onde}: importancia '{importancia}' fora da lista usual")

    data_criacao = l.get("data_criacao", "")
    data_revogacao = l.get("data_revogacao", "")
    iso_criacao = data_iso(data_criacao, onde, "data_criacao")
    iso_revogacao = data_iso(data_revogacao, onde, "data_revogacao")

    ano_inicio = ano(l.get("ano_inicio"), onde, "ano_inicio") or ano(data_criacao, onde, "data_criacao")
    ano_fim = ano(l.get("ano_fim"), onde, "ano_fim") or ano(data_revogacao, onde, "data_revogacao")
    if ano_inicio and ano_fim and ano_fim < ano_inicio:
        avisos.append(f"{onde}: ano_fim ({ano_fim}) anterior ao ano_inicio ({ano_inicio})")
    if situacao == "vigente" and ano_fim:
        avisos.append(f"{onde}: marcada como vigente mas tem ano_fim ({ano_fim})")

    nota_prof = None
    if l.get("nota_prof"):
        try:
            nota_prof = float(l["nota_prof"].replace(",", "."))
            nota_prof = int(nota_prof) if nota_prof.is_integer() else nota_prof
            if not 0 <= nota_prof <= 10:
                avisos.append(f"{onde}: nota_prof {nota_prof} fora de 0 a 10")
        except ValueError:
            avisos.append(f"{onde}: nota_prof '{l['nota_prof']}' não é número, ignorada")
            nota_prof = None

    imagem = l.get("imagem", "")
    if imagem and not imagem.lower().startswith(("http://", "https://")):
        avisos.append(f"{onde}: imagem sem http, ignorada")
        imagem = ""

    links = ler_links(l.get("links"), onde)

    item = {
        "id": ident,
        "titulo": titulo,
        "sigla": l.get("sigla", ""),
        "norma_origem": l.get("norma_origem", ""),
        "tema": tema,
        "orgao": l.get("orgao", ""),
        "nivel": nivel,
        "localidade": l.get("localidade", ""),
        "data_criacao": data_criacao,
        "data_criacao_iso": iso_criacao,
        "ano_inicio": ano_inicio,
        "data_revogacao": data_revogacao,
        "data_revogacao_iso": iso_revogacao,
        "ano_fim": ano_fim,
        "situacao": situacao,
        "texto": l.get("texto", ""),
        "importancia": importancia,
        "nota_prof": nota_prof,
        "comentario": l.get("comentario", ""),
        "link": links[0]["url"] if links else "",
        "links": links,
        "imagem": imagem,
        "tags": lista(l.get("tags")),
        "glossario": lista(l.get("glossario")),
        "relacionadas": lista(l.get("relacionadas")),
        "outros_ids": lista(l.get("outros_ids")),
        "nota": l.get("nota", ""),
        "evidenciar": sim(l.get("evidenciar")),
    }

    if not item["texto"]:
        avisos.append(f"{onde}: sem texto")

    ids.add(ident)
    itens.append(item)

# Confere as ligações: "relacionadas" aponta para esta mesma planilha,
# "glossario" para glossario.json e "outros_ids" para qualquer outra base.
def ids_de(arquivo):
    try:
        with open(arquivo, encoding="utf-8") as f:
            return {str(i.get("id", "")) for i in json.load(f) if i.get("id")}
    except Exception:
        avisos.append(f"Não consegui ler {arquivo} para conferir as ligações")
        return None

glossario = ids_de("glossario.json")
outros = set(ids)
for arquivo in ("glossario.json", "eventos.json", "referencias.json", "personalidades.json", "entidades.json", "dados.json"):
    outros |= ids_de(arquivo) or set()

for i in itens:
    for ref in i["relacionadas"]:
        if ref not in ids:
            avisos.append(f"{i['id']}: relacionada '{ref}' não encontrada na legislação")
    if glossario is not None:
        for ref in i["glossario"]:
            if ref not in glossario and ref not in ids:
                avisos.append(f"{i['id']}: termo '{ref}' não encontrado no glossário")
    for ref in i["outros_ids"]:
        if ref not in outros:
            avisos.append(f"{i['id']}: outro_id '{ref}' não encontrado em nenhuma base")

itens.sort(key=lambda i: (i["ano_inicio"] or 9999, i["data_criacao_iso"] or "", norm(i["titulo"])))

with open("legislacao.json", "w", encoding="utf-8") as f:
    json.dump(itens, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
vigentes = sum(1 for i in itens if i["situacao"] == "vigente")
print(f"{len(itens)} norma(s) gravada(s) em legislacao.json ({vigentes} vigente(s))")
