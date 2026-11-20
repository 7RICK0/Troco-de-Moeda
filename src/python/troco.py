"""Troco de moedas: menor número de moedas para pagar o valor V.

As moedas têm quantidade ilimitada. Resposta -1 significa impossível.
"""


def troco_guloso(moedas_desc, V):
    """Algoritmo A (guloso).

    Pré-condição: moedas distintas e positivas em ordem DECRESCENTE.
    Usa sempre a maior moeda que cabe no resto. Pode não ser ótimo.
    """
    resto = V
    total = 0
    for c in moedas_desc:
        if c <= resto:
            q = resto // c
            total += q
            resto -= q * c
            if resto == 0:
                return total
    return total if resto == 0 else -1


def troco_pd(moedas, V):
    """Algoritmo B (programação dinâmica).

    dp[v] = menor número de moedas para pagar v.
    dp[0] = 0; dp[v] = min(dp[v - c] + 1) para cada moeda c <= v.
    """
    infinito = V + 1
    dp = [infinito] * (V + 1)
    dp[0] = 0
    for c in moedas:
        for v in range(c, V + 1):
            x = dp[v - c] + 1
            if x < dp[v]:
                dp[v] = x
    return dp[V] if dp[V] <= V else -1


ALGORITMOS = {"guloso": troco_guloso, "pd": troco_pd}


def ler_instancias(caminho):
    """Cada linha: id experimento caso V n c1 ... cn (moedas decrescentes)."""
    instancias = []
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            p = linha.split()
            n = int(p[4])
            moedas = [int(x) for x in p[5:5 + n]]
            instancias.append({
                "id": p[0], "experimento": p[1], "caso": p[2],
                "V": int(p[3]), "n": n, "moedas": moedas,
            })
    return instancias
