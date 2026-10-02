"""Gera historias.json a partir da aba Histórias.

Mesma lógica da aba Aulas: cada linha é um bloco, agrupado por id_historia
e ordenado por ordem_bloco (ou pela ordem das linhas). Chaves = nomes das colunas.
Estrutura: [ {colunas da linha "historia", "anterior", "proxima",
              "personagens": [ {colunas da linha "personagem"} ],
              "blocos": [ {colunas preenchidas de cena, narracao, fala, professor, licao, referencia} ]} ]
A referência com base "historias" vira anterior/proxima (1º id = anterior, 2º = próxima; "-" = nenhuma).
"""
import os

from comum import avisos, converter, gravar, ids_do_arquivo, ler_csv, nao, norm

# O mesmo script gera historias.json e casos.json (aba Casos, mesmas colunas).
SAIDA = os.environ.get("SAIDA", "historias.json")
PROPRIA = os.environ.get("BASE_PROPRIA", "historias")

TIPOS = {"historia", "personagem", "cena", "narracao", "fala", "professor", "licao", "referencia"}
BASES = {"glossario": "glossario.json", "aulas": "aulas.json", "personalidades": "personalidades.json",
         "entidades": "entidades.json", "referencias": "referencias.json", "acervo": "acervo.json",
         "historias": "historias.json", "casos": "casos.json"}
SO_DA_LINHA = ("id_historia",)


def preenchidas(item):
    return {k: v for k, v in item.items() if v not in ("", [], None, False) and k not in SO_DA_LINHA}


historias, ordem = {}, []
for n, l in ler_csv():
    hid, tipo = l.get("id_historia", ""), l.get("tipo_bloco", "").lower()
    if not hid and not tipo:
        continue
    onde = f"Linha {n} ({hid}, {tipo})"
    if not hid:
        avisos.append(f"{onde}: sem id_historia, ignorada"); continue
    if tipo not in TIPOS:
        avisos.append(f"{onde}: tipo_bloco '{tipo}' não existe, ignorada"); continue
    if hid not in historias:
        historias[hid] = {"id_historia": hid, "_pub": True, "_linhas": []}
        ordem.append(hid)
    h = historias[hid]
    item = converter(l, onde)
    if tipo == "historia":
        h.update(item)
        h["_pub"] = not nao(l.get("publicar"))
        h.update(anterior=None, proxima=None, personagens=[], blocos=[])
        continue
    if nao(l.get("publicar")):
        continue
    h["_linhas"].append((l.get("ordem_bloco") or "", n, tipo, item, onde))

saida = []
for hid in ordem:
    h = historias[hid]
    linhas = h.pop("_linhas")
    if not h.pop("_pub"):
        continue
    if "titulo" not in h:
        avisos.append(f"História {hid}: falta a linha do tipo historia, ignorada"); continue
    linhas.sort(key=lambda x: (x[0] == "", x[0], x[1]))
    for _, n, tipo, item, onde in linhas:
        if tipo == "personagem":
            if not item.get("personagem"):
                avisos.append(f"{onde}: personagem sem nome, ignorado"); continue
            h["personagens"].append(preenchidas(item))
            continue
        if tipo == "referencia" and norm(item.get("base")) == PROPRIA:
            ids = [None if i == "-" else i for i in item.get("ref_id", [])]
            h["anterior"] = ids[0] if len(ids) > 0 else None
            h["proxima"] = ids[1] if len(ids) > 1 else None
            continue
        if tipo == "fala" and not item.get("personagem"):
            avisos.append(f"{onde}: fala sem personagem")
        h["blocos"].append(preenchidas(item))
    saida.append(h)

saida.sort(key=lambda h: (h.get("ordem") is None, h.get("ordem") or 0, norm(h.get("titulo"))))

ids_hist = {h["id_historia"] for h in saida}
cache = {}
for h in saida:
    for campo in ("anterior", "proxima"):
        if h[campo] and h[campo] not in ids_hist:
            avisos.append(f"História {h['id_historia']}: {campo} '{h[campo]}' não encontrada (ou não publicada)")
    for b in h["blocos"]:
        arq = BASES.get(norm(b.get("base")))
        if not arq or arq == SAIDA:
            continue
        if arq not in cache:
            cache[arq] = ids_do_arquivo(arq)
        if cache[arq]:
            for i in b.get("ref_id", []):
                if i not in cache[arq]:
                    avisos.append(f"História {h['id_historia']}: id '{i}' não encontrado em {b['base']}")

gravar(SAIDA, saida, f"{len(saida)} item(ns) gravado(s) em {SAIDA}")
