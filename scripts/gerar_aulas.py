"""Gera aulas.json a partir da aba Aulas.

Cada linha é um bloco, agrupado por aula_id. Chaves = nomes das colunas (ver comum.py).
Estrutura: [ {colunas da linha "aula", "secoes": [ {colunas da linha "secao", "blocos": [...]} ],
              "recursos": [ {colunas da linha "recurso"} ]} ]
Nos blocos e recursos só vão as colunas preenchidas.
"""
from comum import avisos, converter, gravar, ids_do_arquivo, ler_csv, nao

TIPOS = {"aula", "secao", "card", "citacao", "subtitulo", "cooperativa", "referencia", "recurso"}
CORES = {"petroleo-escuro", "petroleo", "laranja", "dourado", "verde"}
# Valor da coluna base -> arquivo deste repositório
BASES = {
    "glossario": "glossario.json", "calendario": "eventos.json", "eventos": "eventos.json",
    "acervo": "acervo.json", "referencias": "referencias.json", "personalidades": "personalidades.json",
    "entidades": "entidades.json", "politicas": "politicas.json", "dados": "dados.json",
    "historias": "historias.json", "tese": "tese.json",
}
SO_DA_LINHA = ("aula_id", "tipo_bloco", "secao")


def preenchidas(item):
    return {k: v for k, v in item.items() if v not in ("", [], None, False) and k not in SO_DA_LINHA}


aulas, ordem = {}, []
for n, l in ler_csv():
    aid, tipo = l.get("aula_id", ""), l.get("tipo_bloco", "").lower()
    if not aid and not tipo:
        continue
    onde = f"Linha {n} ({aid}, {tipo})"
    if not aid:
        avisos.append(f"{onde}: sem aula_id, ignorada"); continue
    if tipo not in TIPOS:
        avisos.append(f"{onde}: tipo_bloco '{tipo}' não existe, ignorada"); continue
    if aid not in aulas:
        aulas[aid] = {"aula_id": aid, "_pub": True, "secoes": [], "recursos": [], "_secoes": {}, "_ocultas": set()}
        ordem.append(aid)
    a = aulas[aid]
    item = converter(l, onde)
    publicar = not nao(l.get("publicar"))
    num = item.get("secao") or 0

    if tipo == "aula":
        a.update({k: v for k, v in item.items() if k not in ("tipo_bloco", "secao")})
        a["_pub"] = publicar
        continue
    if tipo == "secao":
        if not num:
            avisos.append(f"{onde}: seção sem número, ignorada"); continue
        if not publicar:
            a["_ocultas"].add(num); continue
        if item.get("cor") and item["cor"] not in CORES:
            avisos.append(f"{onde}: cor '{item['cor']}' fora da lista ({', '.join(sorted(CORES))})")
        s = {"secao": num, **{k: v for k, v in item.items() if k not in SO_DA_LINHA}, "blocos": []}
        a["_secoes"][num] = s
        a["secoes"].append(s)
        continue
    if not publicar:
        continue
    if tipo == "recurso":
        if not item.get("links"):
            avisos.append(f"{onde}: recurso sem link, ignorado"); continue
        a["recursos"].append(preenchidas(item))
        continue
    if num in a["_ocultas"]:
        continue
    if num not in a["_secoes"]:
        avisos.append(f"{onde}: seção {num} não existe (falta a linha secao antes deste bloco), ignorado"); continue
    bloco = {"tipo_bloco": tipo, **preenchidas(item)}
    if tipo == "referencia":
        if bloco.get("base", "").lower() not in BASES or not bloco.get("ref_id"):
            avisos.append(f"{onde}: referência precisa de base ({', '.join(BASES)}) e ref_id, ignorada"); continue
    a["_secoes"][num]["blocos"].append(bloco)

cache = {}
saida = []
for aid in ordem:
    a = aulas[aid]
    if not a.pop("_pub"):
        continue
    if "titulo" not in a:
        avisos.append(f"Aula {aid}: falta a linha do tipo aula")
    for s in a["secoes"]:
        for b in s["blocos"]:
            if b["tipo_bloco"] != "referencia":
                continue
            arq = BASES[b["base"].lower()]
            if arq not in cache:
                cache[arq] = ids_do_arquivo(arq)
            if cache[arq]:
                for i in b["ref_id"]:
                    if i not in cache[arq]:
                        avisos.append(f"Aula {aid}, seção {s['secao']}: id '{i}' não encontrado em {b['base']}")
    a.pop("_secoes"); a.pop("_ocultas")
    saida.append(a)

gravar("aulas.json", saida, f"{len(saida)} aula(s) gravada(s) em aulas.json")
