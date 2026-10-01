"""Gera o JSON das abas em que cada linha é um item.

Cada script gerar_<aba>.py só chama gerar("<aba>").
Abas: glossario, acervo, entidades, personalidades, politicas, dados, referencias, tese.
O arquivo gravado tem o nome da aba (glossario.json, acervo.json...).
As chaves são os nomes das colunas (ver comum.py).
"""
from comum import avisos, converter, gravar, ler_csv, nao, norm, sim


# Abas em que só entra a linha marcada publicar = sim.
# Nas outras, entra tudo, menos publicar = não.
SO_COM_SIM = {"glossario", "entidades", "politicas", "dados", "referencias", "acervo"}
# Coluna principal: linha sem ela é ignorada
TITULO = {"referencias": "referencia", "dados": "ano"}
ORDEM = {
    "glossario": lambda i: norm(i.get("titulo")),
    "acervo": lambda i: (-(i.get("ano") or 0), norm(i.get("titulo"))),
    "entidades": lambda i: norm(i.get("titulo")),
    "personalidades": lambda i: norm(i.get("titulo")),
    "politicas": lambda i: (i.get("ano_inicio") or 9999, norm(i.get("titulo"))),
    "dados": lambda i: (i.get("ano") or 0, norm(i.get("ramo"))),
    "referencias": lambda i: norm((i.get("referencia") or "").replace("*", "")),
}


def gerar(aba):
    itens, ids = [], set()
    for n, l in ler_csv():
        if not any(l.values()):
            continue
        pub = l.get("publicar", "")
        if (aba in SO_COM_SIM and "publicar" in l and not sim(pub)) or nao(pub):
            continue
        item = converter(l, f"Linha {n}")
        titulo = TITULO.get(aba, "titulo")
        k_id = next((k for k in item if k.startswith("id_")), None)
        onde = f"Linha {n} ({(item.get(k_id) if k_id else '') or str(item.get(titulo, ''))[:50]})"
        if titulo in l and not l.get(titulo):
            avisos.append(f"{onde}: sem {titulo}, ignorada")
            continue
        if k_id:
            if not item[k_id]:
                avisos.append(f"{onde}: sem {k_id}")
            elif item[k_id] in ids:
                avisos.append(f"{onde}: {k_id} '{item[k_id]}' repetido, linha ignorada")
                continue
            ids.add(item[k_id])
        for campo in ("imagem",):
            if item.get(campo) and not item[campo].lower().startswith(("http://", "https://")):
                avisos.append(f"{onde}: {campo} sem http")
        itens.append(item)

    if aba in ORDEM:
        itens.sort(key=ORDEM[aba])

    # Confere as ligações entre bases
    if aba == "glossario":
        conhecidos = {norm(i.get("id_glossario")) for i in itens} | {norm(i.get("titulo")) for i in itens}
        for i in itens:
            for rel in i.get("relacionados", []):
                if norm(rel) not in conhecidos:
                    avisos.append(f"{i.get('id_glossario')}: relacionado '{rel}' não encontrado no glossário")
    if aba == "politicas":
        for i in itens:
            for rel in i.get("relacionadas", []):
                if rel not in ids:
                    avisos.append(f"{i.get('id_politica')}: relacionada '{rel}' não encontrada nas políticas")

    gravar(f"{aba}.json", itens, f"{len(itens)} item(ns) gravado(s) em {aba}.json")
