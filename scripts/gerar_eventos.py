import csv, io, json, os, urllib.request
from datetime import date, datetime, timedelta

ANO_ATUAL = date.today().year
ANOS_A_FRENTE = 2
avisos = []

def ler_planilha():
    with urllib.request.urlopen(os.environ["CSV_URL"]) as r:
        texto = r.read().decode("utf-8")
    for n, linha in enumerate(csv.DictReader(io.StringIO(texto)), start=2):
        l = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
        l["_linha"] = n
        yield l

def inteiro(v):
    try:
        return int(float(v))
    except ValueError:
        return None

def hora(v):
    return v[:5] if v else ""

def ler_data(v):
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(v, formato).date()
        except ValueError:
            pass
    return None

def base(l, ident):
    return {
        "id": ident,
        "title": l["titulo"],
        "extendedProps": {
            "tipo": l.get("tipo", ""),
            "categoria": l.get("categoria", ""),
            "tags": [t.strip() for t in l.get("tags", "").split(",") if t.strip()],
            "local": l.get("local", ""),
            "resumo": l.get("resumo", ""),
            "descricao": l.get("descricao", ""),
            "link": l.get("link", ""),
            "imagem": l.get("imagem", "") or l.get("foto", ""),
            "fonte": l.get("fonte", ""),
            "relembrar": l.get("relembrar", "").lower() == "sim",
            "evidenciar": any(l.get(c, "").strip().lower() in ("sim", "s", "true", "1", "x") for c in ("evidenciar", "destaque", "destacar")),
        },
    }

def com_data(ev, l, inicio, fim):
    h_ini, h_fim = hora(l.get("hora_inicio", "")), hora(l.get("hora_fim", ""))
    ev["allDay"] = not h_ini
    ev["start"] = inicio.isoformat() + (f"T{h_ini}" if h_ini else "")
    if fim is None and h_fim:
        fim = inicio
    if fim:
        if h_ini:
            ev["end"] = f"{fim.isoformat()}T{h_fim or h_ini}"
        else:
            ev["end"] = (fim + timedelta(days=1)).isoformat()  # fim exclusivo no FullCalendar
    return ev

linhas = [l for l in ler_planilha()
          if l.get("publicar", "").lower() == "sim" and l.get("titulo")]
substituidos = {l["substitui"] for l in linhas if l.get("substitui")}
saida = []

for l in linhas:
    ano, mes, dia = inteiro(l.get("ano", "")), inteiro(l.get("mes", "")), inteiro(l.get("dia", ""))

    if not ano:
        avisos.append(f'Linha {l["_linha"]} ({l.get("id")}): sem ano, ignorada')
        continue

    # Datas incompletas: vão para o JSON sem "start", para o painel de memória e a linha do tempo
    if not (mes and dia):
        ev = base(l, l["id"])
        ev["extendedProps"].update(precisao="mes" if mes else "ano", ano=ano, mes=mes)
        saida.append(ev)
        continue

    try:
        inicio = date(ano, mes, dia)
    except ValueError:
        avisos.append(f'Linha {l["_linha"]} ({l.get("id")}): data inválida {dia}/{mes}/{ano}')
        continue

    fim = ler_data(l["data_fim"]) if l.get("data_fim") else None

    if l.get("recorrencia", "").lower() != "anual":
        ev = com_data(base(l, l["id"]), l, inicio, fim)
        ev["extendedProps"]["precisao"] = "dia"
        saida.append(ev)
        continue

    ate = inteiro(l.get("recorrencia_ate", "")) or ANO_ATUAL + ANOS_A_FRENTE
    duracao = (fim - inicio) if fim else None
    for a in range(ano, ate + 1):
        ident = f'{l["id"]}-{a}'
        if ident in substituidos:
            continue
        try:
            ini = inicio.replace(year=a)
        except ValueError:
            continue  # 29 de fevereiro em ano não bissexto
        ev = com_data(base(l, ident), l, ini, ini + duracao if duracao is not None else None)
        ev["extendedProps"].update(precisao="dia", ano_origem=ano, edicao=a - ano)
        saida.append(ev)

def ordem(e):
    if "start" in e:
        return e["start"]
    p = e["extendedProps"]
    return f'{p["ano"]:04d}-{(p["mes"] or 1):02d}'

saida.sort(key=ordem)

with open("eventos.json", "w", encoding="utf-8") as f:
    json.dump(saida, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
print(f"{len(saida)} itens gravados em eventos.json")
