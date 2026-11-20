"""Com que frequência o guloso erra? Sorteia sistemas de moedas (sempre com a moeda 1)
e compara guloso e PD para todo V de 1 a 1000.  Semente fixa.
"""
import argparse
import csv
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "python"))
from troco import troco_guloso  # noqa: E402

SEMENTE = 2026
V_MAX = 1000
SISTEMAS_POR_N = 500
MAIOR_MOEDA = 100


def tabela_otima(moedas, limite):
    dp = [0] + [limite + 1] * limite
    for c in moedas:
        for v in range(c, limite + 1):
            if dp[v - c] + 1 < dp[v]:
                dp[v] = dp[v - c] + 1
    return dp


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--saida", required=True)
    a = p.parse_args()
    rng = random.Random(SEMENTE)
    linhas = []
    for n in (3, 4, 5, 6):
        canonicos = 0
        erros = excesso = 0
        pior_razao = 1.0
        for _ in range(SISTEMAS_POR_N):
            moedas = sorted([1] + rng.sample(range(2, MAIOR_MOEDA + 1), n - 1), reverse=True)
            otimo = tabela_otima(moedas, V_MAX)
            erros_sistema = 0
            for V in range(1, V_MAX + 1):
                g = troco_guloso(moedas, V)
                if g != otimo[V]:
                    erros_sistema += 1
                    excesso += g - otimo[V]
                    pior_razao = max(pior_razao, g / otimo[V])
            erros += erros_sistema
            canonicos += erros_sistema == 0
        total = SISTEMAS_POR_N * V_MAX
        linhas.append({
            "n": n,
            "sistemas": SISTEMAS_POR_N,
            "pct_sistemas_canonicos": round(100 * canonicos / SISTEMAS_POR_N, 1),
            "pct_valores_com_erro": round(100 * erros / total, 1),
            "moedas_a_mais_quando_erra": round(excesso / erros, 2) if erros else 0,
            "pior_razao_guloso_otimo": round(pior_razao, 2),
        })
    with open(a.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    for l in linhas:
        print(l)


if __name__ == "__main__":
    main()
