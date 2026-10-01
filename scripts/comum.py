"""Ajustes comuns para a planilha unificada (jsonucops _uni).

Os nomes das colunas mudaram na planilha nova (ex.: id_glossario, titulo),
mas o site continua lendo as mesmas chaves nos JSON. Aqui cada linha da
planilha recebe também os nomes antigos, e a coluna obs_internas é descartada.
"""
import re, unicodedata

INTERNAS = {"obs_internas"}

# nome novo -> nome antigo, por planilha
COLUNAS = {
    "glossario": {"id_glossario": "id", "titulo": "termo"},
    "acervo": {"titulo": "titulo_pt", "link": "url"},
    "entidades": {"id_entidade": "id"},
    "personalidades": {"id_persona": "id", "titulo": "title"},
    "politicas": {"id_politica": "id"},
    "dados": {"id_dados": "id", "nota": "note"},
    "referencias": {"id_referencia": "id"},
    "eventos": {"id_evento": "id"},
    "aulas": {},
}

MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
         "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}


def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()


def ajustar(l, planilha):
    for k in INTERNAS:
        l.pop(k, None)
    for novo, antigo in COLUNAS.get(planilha, {}).items():
        if l.get(novo) and not l.get(antigo):
            l[antigo] = l[novo]
    return l


def data_partes(v):
    """Lê '21-dez-1844', 'jun-2003', '1825', '21/12/1844' ou '1844-12-21'.
    Devolve (ano, mes, dia), com None no que faltar; (None, None, None) se não entender."""
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
    m = re.fullmatch(r"(?:(\d{1,2})[-/ ])?([a-z]{3})[a-z]*\.?[-/ ](\d{4})", v)
    if m and m.group(2) in MESES:
        d = int(m.group(1)) if m.group(1) else None
        return int(m.group(3)), MESES[m.group(2)], d
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", v)
    if m:
        return int(m.group(2)), int(m.group(1)), None
    m = re.fullmatch(r"-?\d{3,4}", v)
    if m:
        return int(v), None, None
    return None, None, None
