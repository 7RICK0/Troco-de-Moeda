"""Gera a tabela-resumo (média, desvio, razão T/f, expoente ajustado) e os gráficos.

fig1 e fig2: linhas (log-log e razão T/f); fig3: barras horizontais; fig4 e fig5: colunas; fig6: pizza.

  python scripts/graficos.py --resultados resultados --graficos graficos
"""
import argparse
import csv
import glob
import math
import os
import statistics
import sys

import matplotlib
import matplotlib.ticker
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "src", "python"))
from troco import ler_instancias  # noqa: E402

AZUL, LARANJA = "#0072B2", "#D55E00"  # paleta que funciona para daltônicos
VERDE, ROSA = "#009E73", "#CC79A7"
ESTILO = {  # cor = linguagem, traço e marcador = algoritmo
    ("python", "pd"): dict(color=AZUL, ls="-", marker="o"),
    ("java", "pd"): dict(color=LARANJA, ls="-", marker="o"),
    ("python", "guloso"): dict(color=AZUL, ls="--", marker="s"),
    ("java", "guloso"): dict(color=LARANJA, ls="--", marker="s"),
}
ALG_COR = {"pd": dict(color=VERDE, ls="-", marker="o"), "guloso": dict(color=ROSA, ls="--", marker="s")}
NOME = {"python": "Python", "java": "Java", "pd": "PD", "guloso": "Guloso"}
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                     "font.size": 11, "axes.titlesize": 12, "axes.titleweight": "bold",
                     "axes.grid": True, "grid.color": "0.88", "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 200,
                     "legend.frameon": False})


def reta_ref(ax, s, eixo, rotulo="referência: inclinação 1 (cresce na mesma proporção)"):
    """Reta de inclinação 1 em log-log, paralela e logo abaixo da série s."""
    xs = [l[eixo] for l in s]
    y0 = s[0]["media_ns"] / 1e6 * 0.3
    ax.plot(xs, [y0 * x / xs[0] for x in xs], color="0.35", ls=":", lw=1.6, label=rotulo)


def passos_teoricos(alg, moedas, V):
    """f(entrada): nº de passos do laço interno (PD) ou iterações do laço (guloso)."""
    if alg == "pd":
        return sum(V - c + 1 for c in moedas if c <= V)
    resto, it = V, 0
    for c in moedas:
        it += 1
        if c <= resto:
            resto -= (resto // c) * c
            if resto == 0:
                break
    return it


def carregar(res, entradas=None):
    insts = {i["id"]: i for arq in glob.glob(os.path.join(entradas or os.path.join(RAIZ, "entradas"), "bench_*.txt"))
             for i in ler_instancias(arq)}
    grupos = {}
    for arq in glob.glob(os.path.join(res, "tempos_*.csv")):
        with open(arq, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                chave = (r["linguagem"], r["algoritmo"], r["id"])
                g = grupos.setdefault(chave, {"lote": int(r["lote"]), "t": [], "resposta": r["resposta"]})
                g["t"].append(float(r["ns_por_chamada"]))
    linhas = []
    for (ling, alg, id_), g in grupos.items():
        inst = insts[id_]
        media = statistics.mean(g["t"])
        desvio = statistics.stdev(g["t"]) if len(g["t"]) > 1 else 0.0
        f = passos_teoricos(alg, inst["moedas"], inst["V"])
        linhas.append({
            "linguagem": ling, "algoritmo": alg, "experimento": inst["experimento"],
            "caso": inst["caso"], "id": id_, "n": inst["n"], "V": inst["V"],
            "lote": g["lote"], "repeticoes": len(g["t"]), "media_ns": media, "desvio_ns": desvio,
            "cv_pct": 100 * desvio / media, "f_passos": f, "ns_por_passo": media / f,
            "resposta": g["resposta"],
        })
    linhas.sort(key=lambda l: (l["experimento"], l["caso"], l["linguagem"], l["algoritmo"], l["n"], l["V"]))
    return linhas


def serie(linhas, ling, alg, exp, caso, eixo):
    sel = sorted((l for l in linhas if l["linguagem"] == ling and l["algoritmo"] == alg
                  and l["experimento"] == exp and l["caso"] == caso), key=lambda l: l[eixo])
    return sel


def expoente(xs, ys):
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    mx, my = statistics.mean(lx), statistics.mean(ly)
    num = sum((a - mx) * (b - my) for a, b in zip(lx, ly))
    den = sum((a - mx) ** 2 for a in lx)
    return num / den if den else float("nan")


def salvar_csv(caminho, linhas):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        for l in linhas:
            w.writerow({k: (f"{v:.4g}" if isinstance(v, float) else v) for k, v in l.items()})


def ajustes(linhas):
    saida = []
    combos = sorted({(l["linguagem"], l["algoritmo"], l["experimento"], l["caso"]) for l in linhas})
    for ling, alg, exp, caso in combos:
        eixo = "V" if exp == "E1" else "n"
        s = serie(linhas, ling, alg, exp, caso, eixo)
        if len(s) < 3:
            continue
        saida.append({"linguagem": ling, "algoritmo": alg, "experimento": exp, "caso": caso,
                      "variavel": eixo, "pontos": len(s),
                      "expoente_tempo": expoente([l[eixo] for l in s], [l["media_ns"] for l in s]),
                      "expoente_razao_T_f": expoente([l[eixo] for l in s], [l["ns_por_passo"] for l in s])})
    return saida


def eixo_digitos(ax):
    sec = ax.secondary_xaxis("top", functions=(lambda v: np.log10(np.clip(v, 1e-9, None)),
                                               lambda d: 10.0 ** d))
    sec.xaxis.set_major_locator(matplotlib.ticker.FixedLocator([3, 4, 5, 6, 7]))
    sec.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    sec.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    sec.set_xlabel("log10(V) (o tamanho da entrada cresce com log V)")


def plot_linha(ax, s, eixo, ling, alg, rotulo=None, campo="media_ns", **extra):
    if not s:
        return
    xs = [l[eixo] for l in s]
    ys = [l[campo] / 1e6 if campo == "media_ns" else l[campo] for l in s]
    est = dict(ESTILO[(ling, alg)])
    est.update(extra)
    if campo == "media_ns":
        ax.errorbar(xs, ys, yerr=[l["desvio_ns"] / 1e6 for l in s], ms=6, lw=2, capsize=3,
                    label=rotulo or f"{NOME[alg]} ({NOME[ling]})", **est)
    else:
        ax.plot(xs, ys, ms=6, lw=2, label=rotulo or f"{NOME[alg]} ({NOME[ling]})", **est)


def fig_teorico(linhas, pasta):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, exp, eixo, caso, algs in ((axs[0], "E1", "V", "medio", ["pd"]),
                                      (axs[1], "E2", "n", "pior", ["pd", "guloso"])):
        for ling in ("python", "java"):
            for alg in algs:
                s = serie(linhas, ling, alg, exp, caso, eixo)
                if not s:
                    continue
                ref = s[-1]["ns_por_passo"]
                for l in s:
                    l["_norm"] = l["ns_por_passo"] / ref
                plot_linha(ax, s, eixo, ling, alg, campo="_norm")
        ax.set_xscale("log")
        ax.axhline(1, color="0.35", lw=1.2, ls=":")
        ax.set_ylim(0, max(2.0, ax.get_ylim()[1]))
        ax.legend(fontsize=9)
    axs[0].set_title("(a) PD variando V (n = 13)")
    axs[0].set_xlabel("V (valor a pagar)")
    axs[0].set_ylabel("tempo ÷ passos previstos, relativo ao último ponto")
    axs[1].set_title("(b) Variando n (V ≈ $10^5$, pior caso do guloso)")
    axs[1].set_xlabel("n (tipos de moeda)")
    fig.suptitle("Teórico × medido: a estabilização da razão é compatível com o crescimento previsto")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig1_teorico_vs_medido.png"))
    plt.close(fig)


def fig_algoritmos(linhas, pasta):
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.2))
    for ling in ("python", "java"):
        for alg in ("pd", "guloso"):
            plot_linha(axs[0], serie(linhas, ling, alg, "E1", "medio", "V"), "V", ling, alg)
            plot_linha(axs[1], serie(linhas, ling, alg, "E2", "pior", "n"), "n", ling, alg)
    reta_ref(axs[0], serie(linhas, "java", "pd", "E1", "medio", "V"), "V")
    reta_ref(axs[1], serie(linhas, "java", "pd", "E2", "pior", "n"), "n")
    for ax in axs:
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_ylabel("tempo por chamada (ms)")
    h, rot = axs[0].get_legend_handles_labels()
    fig.legend(h, rot, loc="lower center", ncol=5, fontsize=10)
    axs[0].set_xlabel("V (valor a pagar)")
    axs[0].set_title("(a) Variando V (n = 13)", pad=34)
    eixo_digitos(axs[0])
    axs[1].set_xlabel("n (tipos de moeda)")
    axs[1].set_title("(b) Variando n (V ≈ $10^5$, pior caso do guloso)", pad=34)
    fig.suptitle("A PD cresce junto com V; o guloso quase não muda (escala log-log)", fontsize=13)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(pasta, "fig2_guloso_vs_pd.png"))
    plt.close(fig)


def _tempo_txt(ns):
    for lim, div, un in ((1e3, 1, "ns"), (1e6, 1e3, "µs"), (1e9, 1e6, "ms")):
        if ns < lim:
            return f"{ns / div:.1f} {un}".replace(".", ",")
    return f"{ns / 1e9:.2f} s".replace(".", ",")


def _razoes(linhas, alg, exp, caso, eixo):
    py = {l[eixo]: l["media_ns"] for l in serie(linhas, "python", alg, exp, caso, eixo)}
    jv = {l[eixo]: l["media_ns"] for l in serie(linhas, "java", alg, exp, caso, eixo)}
    return [py[x] / jv[x] for x in sorted(set(py) & set(jv))]


def fig_linguagens(linhas, pasta):
    """Barras horizontais: quantas vezes o Python é mais lento (mediana entre E1 e E2)."""
    grupos = []
    for rot, alg in (("Programação dinâmica", "pd"), ("Guloso", "guloso")):
        r = _razoes(linhas, alg, "E1", "medio", "V") + _razoes(linhas, alg, "E2", "pior", "n")
        if r:
            grupos.append((rot, r, ALG_COR[alg]["color"]))
    if not grupos:
        return
    fig, ax = plt.subplots(figsize=(10, 3.4))
    ys = list(range(len(grupos)))[::-1]
    topo = max(max(r) for _, r, _ in grupos)
    for y, (rot, r, cor) in zip(ys, grupos):
        med = statistics.median(r)
        ax.barh(y, med, color=cor, height=0.6)
        ax.text(med + topo * 0.02, y, f"cerca de {med:.0f}× mais lento", va="center", fontsize=12, fontweight="bold")
        ax.text(med + topo * 0.02, y - 0.22, f"(variou de {min(r):.0f}× a {max(r):.0f}× entre os tamanhos medidos)",
                va="center", fontsize=9, color="0.35")
    ax.set_yticks(ys)
    ax.set_yticklabels([g[0] for g in grupos], fontsize=11)
    ax.set_xlim(0, topo * 1.5)
    n_tam = len(grupos[0][1])
    ax.set_xlabel(f"quantas vezes o Python demorou mais que o Java (mediana entre os {n_tam} tamanhos de entrada medidos)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Nestas medições, o Python foi mais lento que o Java")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig3_python_vs_java.png"))
    plt.close(fig)


def fig_casos(linhas, pasta):
    """Colunas agrupadas: melhor, médio e pior caso com o maior n de E2."""
    nmax = max((l["n"] for l in linhas if l["experimento"] == "E2"), default=None)
    if nmax is None:
        return
    rot_caso = {"melhor": "melhor", "medio": "médio", "pior": "pior"}
    cores = {"melhor": VERDE, "medio": "#E69F00", "pior": "#CC3311"}
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, alg in ((axs[0], "guloso"), (axs[1], "pd")):
        for i, ling in enumerate(("python", "java")):
            for j, caso in enumerate(("melhor", "medio", "pior")):
                l = next(x for x in serie(linhas, ling, alg, "E2", caso, "n") if x["n"] == nmax)
                x = i + (j - 1) * 0.27
                v = l["media_ns"] / 1e6
                ax.bar(x, v, width=0.25, color=cores[caso], label=rot_caso[caso] if i == 0 else None)
                ax.text(x, v * 1.15, _tempo_txt(l["media_ns"]), ha="center", fontsize=8)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Python", "Java"])
        ax.set_yscale("log")
        ax.set_ylabel("tempo por chamada (ms, escala log)")
        ax.grid(axis="x", visible=False)
        ax.legend(title="caso", fontsize=9)
    axs[0].set_title(f"(a) Guloso com n = {nmax}: o pior caso é bem mais lento")
    axs[1].set_title("(b) PD: tempos próximos nas entradas selecionadas")
    fig.suptitle("Casos forçados (moedas {1, ..., n}, V ≈ $10^5$)")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig4_casos.png"))
    plt.close(fig)


def fig_memoria(res, pasta):
    """Colunas da memória medida da PD, com a teoria marcada em cada V."""
    dados = []
    for arq in glob.glob(os.path.join(res, "memoria_*.csv")):
        with open(arq, encoding="utf-8") as f:
            dados += list(csv.DictReader(f))
    if not dados:
        return []
    vs = sorted({int(d["V"]) for d in dados})
    med = {(d["linguagem"], int(d["V"])): int(d["bytes_pico"]) / 2 ** 20 for d in dados if d["algoritmo"] == "pd"}
    fig, ax = plt.subplots(figsize=(11, 4.8))
    xs = range(len(vs))
    ax.bar([x - 0.2 for x in xs], [med[("python", v)] for v in vs], width=0.38, color=AZUL, label="PD Python (medido)")
    ax.bar([x + 0.2 for x in xs], [med[("java", v)] for v in vs], width=0.38, color=LARANJA, label="PD Java (medido)")
    ax.plot([x - 0.2 for x in xs], [8 * (v + 1) / 2 ** 20 for v in vs], "k_", ms=16, mew=2.2,
            label="teórico Python 8·(V+1) bytes")
    ax.plot([x + 0.2 for x in xs], [4 * (v + 1) / 2 ** 20 for v in vs], "_", color="0.4", ms=16, mew=2.2,
            label="teórico Java 4·(V+1) bytes")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{v:,}".replace(",", ".") for v in vs], rotation=30, ha="right", fontsize=9)
    ax.set_yscale("log")
    ax.set_xlabel("V (valor a pagar)")
    ax.set_ylabel("memória alocada (MiB, escala log)")
    ax.grid(axis="x", visible=False)
    ax.legend(fontsize=9)
    ax.set_title("Memória da PD cresce junto com V e bate com a teoria Θ(V); o guloso usa memória constante")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig5_memoria.png"))
    plt.close(fig)
    return dados


def fig_sistemas(res, pasta):
    """Pizza: em quantos sistemas aleatórios de 3 moedas o guloso nunca erra."""
    arq = os.path.join(res, "sistemas_aleatorios.csv")
    if not os.path.exists(arq):
        return
    with open(arq, encoding="utf-8") as f:
        sis = list(csv.DictReader(f))
    s3 = sis[0]
    ok = float(s3["pct_sistemas_canonicos"])
    pc = lambda x: f"{x:.1f} %".replace(".", ",")  # noqa: E731
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.pie([ok, 100 - ok], colors=[VERDE, "#CC3311"], startangle=90, counterclock=False,
           labels=["guloso nunca erra\n" + pc(ok), "guloso erra em algum valor\n" + pc(100 - ok)],
           textprops=dict(fontsize=12), wedgeprops=dict(edgecolor="white", linewidth=2))
    ax.set_title(f"{s3['sistemas']} sistemas sorteados com {s3['n']} moedas (V de 1 a 1.000)", fontsize=13)
    outros = ", ".join(f"{s['n']} moedas: {pc(float(s['pct_sistemas_canonicos']))}" for s in sis[1:])
    fig.text(0.5, 0.03, f"Com mais moedas fica ainda pior. O guloso nunca erra em {outros}.",
             ha="center", fontsize=10, color="0.3")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(os.path.join(pasta, "fig6_sistemas_pizza.png"))
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--resultados", default="resultados")
    p.add_argument("--graficos", default="graficos")
    a = p.parse_args()
    res = os.path.join(RAIZ, a.resultados)
    gra = os.path.join(RAIZ, a.graficos)
    os.makedirs(gra, exist_ok=True)
    linhas = carregar(res)
    salvar_csv(os.path.join(res, "resumo.csv"), linhas)
    salvar_csv(os.path.join(res, "ajustes.csv"), ajustes(linhas))
    fig_teorico(linhas, gra)
    for l in linhas:
        l.pop("_norm", None)
    fig_algoritmos(linhas, gra)
    fig_linguagens(linhas, gra)
    fig_casos(linhas, gra)
    fig_memoria(res, gra)
    fig_sistemas(res, gra)
    print(f"resumo.csv, ajustes.csv e figuras gravados em {a.resultados}/ e {a.graficos}/")


if __name__ == "__main__":
    main()
