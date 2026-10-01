"""Gera tese.json a partir da aba Tese.

As colunas ainda não foram definidas, então este script é genérico:
cada linha vira um objeto com todas as colunas da planilha, exceto
obs_internas. Linhas com publicar = "não" ficam de fora. Se a aba estiver
vazia, grava uma lista vazia ([]), para o arquivo já existir no site.
Quando as colunas forem definidas, dá para especializar este script.
"""
import csv, io, json, os, re, urllib.request
from comum import ajustar

avisos = []


def nao(v):
    return (v or "").strip().lower() in ("não", "nao", "n", "false", "0")


with urllib.request.urlopen(os.environ["CSV_URL"]) as r:
    texto_csv = r.read().decode("utf-8")

itens, ids = [], set()
leitor = csv.DictReader(io.StringIO(texto_csv))
for n, linha in enumerate(leitor, start=2):
    l = ajustar({(k or "").strip(): (v or "").strip() for k, v in linha.items() if (k or "").strip()}, "tese")
    if not any(l.values()):
        continue
    if nao(l.get("publicar")):
        continue
    ident = l.get("id_tese") or l.get("id", "")
    if ident:
        if ident in ids:
            avisos.append(f"Linha {n}: id '{ident}' repetido")
        ids.add(ident)
        l = {"id": ident, **{k: v for k, v in l.items() if k not in ("id", "id_tese")}}
    l.pop("publicar", None)
    itens.append(l)

with open("tese.json", "w", encoding="utf-8") as f:
    json.dump(itens, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
print(f"{len(itens)} item(ns) gravado(s) em tese.json")
