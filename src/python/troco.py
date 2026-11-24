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
    if V < 0:
        raise ValueError("V deve ser não negativo")
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
    ids = set()
    with open(caminho, encoding="utf-8") as f:
        for numero, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            p = linha.split()
            try:
                if len(p) < 5:
                    raise ValueError("cabeçalho incompleto")
                V, n = int(p[3]), int(p[4])
                moedas = [int(x) for x in p[5:]]
                if V < 0 or V > 2 ** 31 - 3 or n < 1 or len(moedas) != n:
                    raise ValueError("V, n ou quantidade de moedas inválidos")
                if any(c <= 0 for c in moedas) or moedas != sorted(set(moedas), reverse=True):
                    raise ValueError("moedas devem ser positivas, distintas e decrescentes")
                if p[0] in ids:
                    raise ValueError("identificador duplicado")
            except ValueError as e:
                raise ValueError(f"{caminho}:{numero}: {e}") from e
            ids.add(p[0])
            instancias.append({"id": p[0], "experimento": p[1], "caso": p[2],
                               "V": V, "n": n, "moedas": moedas})
    return instancias
