"""Validação de cobertura, repetições, metadados e respostas de um experimento."""
import csv
import math


def validar_cobertura_resultados(arquivos, instancias, repeticoes=20):
    """Exige as quatro implementações e todas as repetições de cada entrada."""
    esperados = {(i["id"], ling, alg)
                 for i in instancias
                 for ling in ("python", "java") for alg in ("guloso", "pd")}
    encontrados = {}
    metadados = {i["id"]: i for i in instancias}
    respostas = {}
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                chave = (r["id"], r["linguagem"], r["algoritmo"])
                rep = int(r["rep"])
                inst = metadados.get(r["id"])
                if inst is not None:
                    for campo in ("n", "V"):
                        if campo in inst and int(r.get(campo, -1)) != inst[campo]:
                            raise AssertionError(f"metadados divergentes: {r['id']} {campo}")
                if "ns_por_chamada" in r:
                    t = float(r["ns_por_chamada"])
                    if not math.isfinite(t) or t <= 0 or int(r["lote"]) < 1:
                        raise AssertionError("tempo ou lote inválido")
                reps = encontrados.setdefault(chave, set())
                if rep in reps:
                    raise AssertionError(f"repetição duplicada: {chave}, {rep}")
                reps.add(rep)
                respostas.setdefault(r["id"], set()).add(int(r["resposta"]))
    if set(encontrados) != esperados:
        raise AssertionError("cobertura incompleta ou inesperada das quatro implementações")
    if any(reps != set(range(repeticoes)) for reps in encontrados.values()):
        raise AssertionError("repetições ausentes ou inesperadas")
    if any(len(valores) != 1 for valores in respostas.values()):
        raise AssertionError("respostas divergentes nas implementações")

