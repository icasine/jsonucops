"""Gera eventos.json a partir da aba Eventos.

Chaves = nomes das colunas (ver comum.py). Campos calculados acrescentados,
para o calendário e a linha do tempo:
  ano, mes, dia      lidos de data_inicio ("21-dez-1844", "jun-2003", "1825"...)
  precisao           "dia", "mes" ou "ano"
  start, end, allDay datas ISO (só quando a data_inicio tem dia); end exclusivo
  ano_fim_num        ano lido de data_fim
Eventos com recorrencia = anual são repetidos ano a ano até recorrencia_ate
(ou 2 anos à frente), com id_evento-AAAA, ano_origem e edicao.
"""
from datetime import date, timedelta
from comum import avisos, converter, data_partes, gravar, ler_csv, nao

ANO_ATUAL = date.today().year
ANOS_A_FRENTE = 2

linhas = []
for n, l in ler_csv():
    if not l.get("titulo") or nao(l.get("publicar")) or (l.get("publicar", "") == "" and "publicar" in l):
        continue
    linhas.append((n, l))
substituidos = {l["substitui"] for _, l in linhas if l.get("substitui")}

saida = []
for n, l in linhas:
    onde = f"Linha {n} ({l.get('id_evento')})"
    ev = converter(l, onde)
    ano, mes, dia = data_partes(l.get("data_inicio"))
    if not ano:
        avisos.append(f"{onde}: data_inicio '{l.get('data_inicio')}' não reconhecida, ignorada")
        continue
    fa, fm, fd = data_partes(l.get("data_fim"))
    if l.get("data_fim") and not fa:
        avisos.append(f"{onde}: data_fim '{l.get('data_fim')}' não reconhecida")
    ev.update(ano=ano, mes=mes, dia=dia, ano_fim_num=fa)

    if not (mes and dia):
        ev["precisao"] = "mes" if mes else "ano"
        saida.append(ev)
        continue
    try:
        inicio = date(ano, mes, dia)
    except ValueError:
        avisos.append(f"{onde}: data inválida {dia}/{mes}/{ano}")
        continue
    fim = None
    if fa and fm and fd:
        try:
            fim = date(fa, fm, fd)
        except ValueError:
            avisos.append(f"{onde}: data_fim inválida")
    ev["precisao"] = "dia"

    def datar(e, ini, fi):
        e["allDay"] = True
        e["start"] = ini.isoformat()
        if fi:
            e["end"] = (fi + timedelta(days=1)).isoformat()  # fim exclusivo no FullCalendar
        return e

    if l.get("recorrencia", "").lower() != "anual":
        saida.append(datar(ev, inicio, fim))
        continue
    ate = ev.get("recorrencia_ate") or ANO_ATUAL + ANOS_A_FRENTE
    duracao = (fim - inicio) if fim else None
    for a in range(ano, ate + 1):
        ident = f"{l['id_evento']}-{a}"
        if ident in substituidos:
            continue
        try:
            ini = inicio.replace(year=a)
        except ValueError:
            continue  # 29 de fevereiro em ano não bissexto
        e = dict(ev, id_evento=ident, ano_origem=ano, edicao=a - ano)
        saida.append(datar(e, ini, ini + duracao if duracao is not None else None))


def ordem(e):
    return e.get("start") or f"{e['ano']:04d}-{(e['mes'] or 1):02d}"


saida.sort(key=ordem)
gravar("eventos.json", saida, f"{len(saida)} itens gravados em eventos.json")
