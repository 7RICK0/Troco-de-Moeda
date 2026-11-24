"""Gera todas as entradas com semente fixa (as 4 implementações leem estes arquivos).

Formato de cada linha: id experimento caso V n c1 ... cn  (moedas em ordem decrescente)
"""
import argparse
import os
import random

SEMENTE = 2026
PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "entradas")

# Real brasileiro em centavos (moedas + cédulas), inclui 1 centavo para todo V ser pagável
SISTEMA_BRL = [20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50, 25, 10, 5, 1]

# E1: varia V em escala geométrica (passo raiz de 10), n = 13 fixo
TAMANHOS_V = [round(10 ** (3 + 0.5 * j)) for j in range(9)]  # 10^3 ... 10^7

# E2: varia n dobrando, V perto de 10^5, sistema {1, 2, ..., n}
TAMANHOS_N = [2 ** k for k in range(2, 11)]  # 4 ... 1024
V_BASE = 100_000
TAMANHOS_MEDIO = [2 ** k for k in range(2, 9)]
AMOSTRAS_MEDIO = 20
V_MEDIO = 10_000

# Sistemas não canônicos: o guloso erra (resultado esperado conhecido)
CONTRAEXEMPLOS = [
    ("contra_01", "diferente", [4, 3, 1], 6),
    ("contra_02", "diferente", [25, 20, 10, 5], 40),
    ("contra_03", "diferente", [25, 10, 1], 40),
    ("contra_04", "diferente", [10, 7, 1], 14),
    ("contra_05", "diferente", [51, 50, 1], 100),
    ("contra_06", "diferente", [5, 3], 9),
    ("contra_07", "impossivel", [5, 3], 7),
    ("contra_08", "diferente", [20, 9, 6], 24),
]


def linha(id_, experimento, caso, V, moedas):
    moedas = sorted(moedas, reverse=True)
    return f"{id_} {experimento} {caso} {V} {len(moedas)} " + " ".join(map(str, moedas))


def gerar_bench_V(rng):
    linhas = ["# E1: varia V, sistema BRL (n=13), caso medio = V + centavos aleatorios"]
    for j, Vk in enumerate(TAMANHOS_V):
        V = Vk + rng.randint(1, 99)
        linhas.append(linha(f"V_medio_{j:02d}", "E1", "medio", V, SISTEMA_BRL))
    return linhas


def gerar_bench_n(rng):
    linhas = ["# E2: varia n, sistema {1..n}, V perto de 10^5",
              "# melhor: V multiplo de n (1 iteracao do guloso); pior: V mod n = 1 (n iteracoes)"]
    for j, n in enumerate(TAMANHOS_N):
        moedas = list(range(1, n + 1))
        base = V_BASE - V_BASE % n
        casos = [("melhor", base), ("medio", base + rng.randint(0, n - 1)), ("pior", base + 1)]
        for caso, V in casos:
            linhas.append(linha(f"n_{caso}_{j:02d}", "E2", caso, V, moedas))
    return linhas


def gerar_contraexemplos():
    linhas = ["# Sistemas nao canonicos: guloso e PD devem divergir (ou ambos impossivel)"]
    for id_, caso, moedas, V in CONTRAEXEMPLOS:
        linhas.append(linha(id_, "contra", caso, V, moedas))
    return linhas


def gerar_aleatorias(rng, quantidade=400):
    linhas = ["# Instancias pequenas aleatorias (com e sem moeda 1) para testes de corretude"]
    for k in range(quantidade):
        n = rng.randint(1, 5)
        moedas = rng.sample(range(1, 31), n)
        V = rng.randint(0, 60)
        linhas.append(linha(f"aleat_{k:03d}", "aleat", "aleatorio", V, moedas))
    return linhas


def gerar_bench_medio():
    """20 valores distintos por n, amostrados sem reposição; restos uniformes na população."""
    rng = random.Random(SEMENTE + 1)
    linhas = ["# E3: caso medio, 7 tamanhos, 20 entradas distintas por tamanho, semente 2027",
              "# V perto de 10000; intervalo com 10*n valores, alinhado a multiplos de n"]
    for n in TAMANHOS_MEDIO:
        inicio = (V_MEDIO // n - 5) * n
        for j, V in enumerate(rng.sample(range(inicio, inicio + 10 * n), AMOSTRAS_MEDIO)):
            linhas.append(linha(f"medio_{n:04d}_{j:02d}", "E3", "medio", V, list(range(1, n + 1))))
    return linhas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--saida", default=PASTA)
    pasta = p.parse_args().saida
    rng = random.Random(SEMENTE)
    os.makedirs(pasta, exist_ok=True)
    arquivos = {
        "bench_V.txt": gerar_bench_V(rng),
        "bench_n.txt": gerar_bench_n(rng),
        "contraexemplos.txt": gerar_contraexemplos(),
        "aleatorias.txt": gerar_aleatorias(rng),
        "bench_medio.txt": gerar_bench_medio(),
    }
    for nome, linhas in arquivos.items():
        with open(os.path.join(pasta, nome), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(linhas) + "\n")
        print(f"entradas/{nome}: {len(linhas) - sum(l.startswith('#') for l in linhas)} instancias")


if __name__ == "__main__":
    main()
