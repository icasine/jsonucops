"""Regras comuns a todas as abas da planilha unificada (jsonucops _uni).

Padrão: as chaves do JSON são exatamente os nomes das colunas da planilha.
Só a coluna obs_internas fica de fora. Alguns tipos são ajustados:
  listas   -> separadas por ; , ou quebra de linha  (tags, temas, ref_id...)
  links    -> lista de {"texto", "url"}; uma linha por link, "rótulo | url" ou só a url
  sim/não  -> true/false                            (evidenciar, destaque...)
  números  -> número                                (ano, latitude, cooperados...)
Células vazias viram "" (texto), [] (lista), false (sim/não) ou null (número).
"""
import csv, io, json, os, re, unicodedata, urllib.request

INTERNAS = {"obs_internas"}
LISTAS = {"tags", "temas", "relacionados", "referencias", "glossario", "relacionadas", "outros_ids",
          "ref_id", "buscar_tags", "publico"}
LINKS = {"link", "links"}
BOOLEANOS = {"evidenciar", "destaque", "historico", "relembrar", "conferido"}
NUMEROS = {"ano", "ano_fundacao", "ano_fim", "ano_inicio", "recorrencia_ate", "latitude", "longitude",
           "cooperativas", "cooperados", "empregos", "pac", "nota_prof", "ordem", "secao"}
MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
         "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}

avisos = []


def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()


def lista(v):
    return [x.strip() for x in re.split(r"[;,\n]+", v or "") if x.strip()]


def sim(v):
    return norm(v) in ("sim", "s", "x", "true", "1")


def nao(v):
    return norm(v) in ("nao", "n", "false", "0")


def numero(v, onde="", campo=""):
    v = (v or "").strip()
    if not v:
        return None
    t = v.replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):  # 3.947 = três mil novecentos e quarenta e sete
        t = t.replace(".", "")
    t = t.replace(",", ".")
    try:
        n = float(t)
        return int(n) if n.is_integer() and "." not in t else n
    except ValueError:
        m = re.search(r"-?\d{3,4}", v) if campo.startswith("ano") else None
        if m:
            return int(m.group(0))
        avisos.append(f"{onde}: {campo} '{v}' não é número, gravei null")
        return None


def links(v, onde=""):
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


def converter(l, onde=""):
    """Linha da planilha -> objeto do JSON, com as chaves iguais às colunas."""
    item = {}
    for k, v in l.items():
        if not k or k in INTERNAS:
            continue
        if k in LISTAS:
            item[k] = lista(v)
        elif k in LINKS:
            item[k] = links(v, onde)
        elif k in BOOLEANOS:
            item[k] = sim(v)
        elif k in NUMEROS:
            item[k] = numero(v, onde, k)
        else:
            item[k] = v
    return item


def ler_csv():
    with urllib.request.urlopen(os.environ["CSV_URL"]) as r:
        texto = r.read().decode("utf-8")
    for n, linha in enumerate(csv.DictReader(io.StringIO(texto)), start=2):
        yield n, {(k or "").strip(): (v or "").strip() for k, v in linha.items() if (k or "").strip()}


def gravar(arquivo, dados, resumo):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    for a in avisos:
        print(f"::warning::{a}")
    print(resumo)


def chave_id(item):
    """Nome da coluna de id do item (id_glossario, aula_id, id_historia...)."""
    for k in item:
        if k.startswith("id_") or k == "aula_id":
            return k
    return None


def ids_do_arquivo(arquivo):
    try:
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
    except Exception:
        return None
    ids = set()
    for item in dados:
        k = chave_id(item)
        if k and item.get(k):
            i = str(item[k])
            ids.add(i)
            ids.add(re.sub(r"-\d{4}$", "", i))  # eventos anuais: eve-x-2026 vale como eve-x
    return ids


def data_partes(v):
    """Lê '21-dez-1844', 'jun-2003', '1825', '21/12/1844' ou '1844-12-21' -> (ano, mes, dia)."""
    v = norm(v).replace(" ", "")
    if not v:
        return None, None, None
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", v)
    if m:
        a, me, d = (int(x) for x in m.groups())
        return a, me, d
    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", v)
    if m:
        d, me, a = (int(x) for x in m.groups())
        return a, me, d
    m = re.fullmatch(r"(?:(\d{1,2})[-/])?([a-z]{3})[a-z]*\.?[-/](\d{4})", v)
    if m and m.group(2) in MESES:
        return int(m.group(3)), MESES[m.group(2)], int(m.group(1)) if m.group(1) else None
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", v)
    if m:
        return int(m.group(2)), int(m.group(1)), None
    if re.fullmatch(r"-?\d{3,4}", v):
        return int(v), None, None
    return None, None, None
