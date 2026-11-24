"""Medição das implementações em Python.

Modos:
  tempo     <instancias> <saida.csv> [--reps R] [--max-V X] [--max-n Y]
  memoria   <instancias> <saida.csv> [--max-V X] [--max-n Y]
  respostas <instancias> <saida.csv>

Cronometra o lote de chamadas do algoritmo: o laço do lote e a soma das respostas entram na medida;
leitura de arquivo e escrita do CSV ficam fora.
"""
import argparse
import csv
import gc
import time
import tracemalloc

from troco import ALGORITMOS, ler_instancias

LOTE_MIN_NS = 10_000_000   # um lote precisa durar pelo menos 10 ms
LOTE_MAX = 1 << 26         # teto de chamadas por lote
AQUECIMENTO = 1            # lotes descartados antes de medir

sink = 0  # acumula as respostas de cada lote (consome o resultado de toda chamada)


def medir_lote(f, moedas, V, n_chamadas):
    global sink
    acc = 0
    inicio = time.perf_counter_ns()
    for _ in range(n_chamadas):
        acc += f(moedas, V)
    fim = time.perf_counter_ns()
    sink += acc
    return fim - inicio


def calibrar(f, moedas, V):
    n_chamadas = 1
    while True:
        t = medir_lote(f, moedas, V, n_chamadas)
        if t >= LOTE_MIN_NS or n_chamadas >= LOTE_MAX:
            return n_chamadas
        n_chamadas *= 2


def filtrar(instancias, max_V, max_n):
    return [i for i in instancias
            if (max_V is None or i["V"] <= max_V)
            and (max_n is None or i["n"] <= max_n)]


def modo_tempo(instancias, saida, reps):
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["linguagem", "algoritmo", "experimento", "caso", "id",
                    "n", "V", "lote", "rep", "ns_por_chamada", "resposta"])
        for inst in instancias:
            for nome, alg in ALGORITMOS.items():
                moedas, V = inst["moedas"], inst["V"]
                resposta = alg(moedas, V)
                gc.collect()
                gc.disable()
                lote = calibrar(alg, moedas, V)
                for _ in range(AQUECIMENTO):
                    medir_lote(alg, moedas, V, lote)
                tempos = [medir_lote(alg, moedas, V, lote) / lote
                          for _ in range(reps)]
                gc.enable()
                for r, t in enumerate(tempos):
                    w.writerow(["python", nome, inst["experimento"],
                                inst["caso"], inst["id"], inst["n"], V,
                                lote, r, f"{t:.1f}", resposta])
                f.flush()
                print(f"python {nome:6s} {inst['id']:14s} lote={lote:<7d} "
                      f"media={sum(tempos) / reps / 1e6:.4f} ms", flush=True)


def modo_memoria(instancias, saida):
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["linguagem", "algoritmo", "experimento", "caso", "id",
                    "n", "V", "bytes_pico"])
        for inst in instancias:
            for nome, alg in ALGORITMOS.items():
                gc.collect()
                tracemalloc.start()
                tracemalloc.reset_peak()
                alg(inst["moedas"], inst["V"])
                _, pico = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                w.writerow(["python", nome, inst["experimento"], inst["caso"],
                            inst["id"], inst["n"], inst["V"], pico])
                print(f"python memoria {nome:6s} {inst['id']:14s} {pico} B",
                      flush=True)


def modo_respostas(instancias, saida):
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "algoritmo", "resposta"])
        for inst in instancias:
            for nome, alg in ALGORITMOS.items():
                w.writerow([inst["id"], nome, alg(inst["moedas"], inst["V"])])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("modo", choices=["tempo", "memoria", "respostas"])
    p.add_argument("instancias")
    p.add_argument("saida")
    p.add_argument("--reps", type=int, default=20)
    p.add_argument("--max-V", type=int, default=None)
    p.add_argument("--max-n", type=int, default=None)
    a = p.parse_args()
    inst = filtrar(ler_instancias(a.instancias), a.max_V, a.max_n)
    if a.modo == "tempo":
        modo_tempo(inst, a.saida, a.reps)
    elif a.modo == "memoria":
        modo_memoria(inst, a.saida)
    else:
        modo_respostas(inst, a.saida)


if __name__ == "__main__":
    main()
