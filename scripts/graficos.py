"""Gera a tabela-resumo (média, desvio, razão T/f, expoente ajustado) e os gráficos.

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


def carregar(res):
    insts = {i["id"]: i for arq in glob.glob(os.path.join(RAIZ, "entradas", "bench_*.txt"))
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
    sec.set_xlabel("dígitos de V (o tamanho da entrada cresce com log V)")


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
    fig.suptitle("Teórico × medido: quando a razão fica perto de 1, a teoria está certa")
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


def fig_linguagens(linhas, pasta):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, exp, eixo, caso in ((axs[0], "E1", "V", "medio"), (axs[1], "E2", "n", "pior")):
        for alg in ("pd", "guloso"):
            py = {l[eixo]: l["media_ns"] for l in serie(linhas, "python", alg, exp, caso, eixo)}
            jv = {l[eixo]: l["media_ns"] for l in serie(linhas, "java", alg, exp, caso, eixo)}
            xs = sorted(set(py) & set(jv))
            if xs:
                ax.plot(xs, [py[x] / jv[x] for x in xs], label=NOME[alg],
                        **ALG_COR[alg], ms=6, lw=2)
        ax.axhline(1, color="0.35", lw=1.2, ls=":")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.legend(fontsize=10)
        ax.set_ylabel("tempo do Python ÷ tempo do Java (vezes)")
    axs[0].set_xlabel("V (valor a pagar)")
    axs[0].set_title("(a) Variando V (n = 13)")
    axs[1].set_xlabel("n (tipos de moeda)")
    axs[1].set_title("(b) Variando n (pior caso do guloso)")
    fig.suptitle("Quantas vezes o Python é mais lento que o Java (acima de 1 = Python perde)")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig3_python_vs_java.png"))
    plt.close(fig)


def fig_casos(linhas, pasta):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    tons = {"melhor": VERDE, "medio": "#E69F00", "pior": "#CC3311"}
    marc = {"melhor": "^", "medio": "o", "pior": "v"}
    for ax, alg in ((axs[0], "guloso"), (axs[1], "pd")):
        for ling, ls in (("python", "-"), ("java", "--")):
            for caso in ("melhor", "medio", "pior"):
                s = serie(linhas, ling, alg, "E2", caso, "n")
                plot_linha(ax, s, "n", ling, alg, rotulo=f"{caso} ({NOME[ling]})",
                           color=tons[caso], marker=marc[caso], ls=ls)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("n (tipos de moeda)")
        ax.set_ylabel("tempo por chamada (ms)")
        ax.legend(fontsize=8.5, ncol=2)
    axs[0].set_title("(a) Guloso: melhor, médio e pior caso")
    axs[1].set_title("(b) PD nas mesmas entradas: os três casos coincidem")
    fig.suptitle("Casos forçados (V ≈ $10^5$, moedas {1, ..., n}). Linha cheia = Python, tracejada = Java")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig4_casos.png"))
    plt.close(fig)


def fig_memoria(res, pasta):
    dados = []
    for arq in glob.glob(os.path.join(res, "memoria_*.csv")):
        with open(arq, encoding="utf-8") as f:
            dados += list(csv.DictReader(f))
    if not dados:
        return []
    fig, ax = plt.subplots(figsize=(8, 5))
    for ling in ("python", "java"):
        s = sorted((d for d in dados if d["linguagem"] == ling and d["algoritmo"] == "pd"),
                   key=lambda d: int(d["V"]))
        if s:
            ax.plot([int(d["V"]) for d in s], [int(d["bytes_pico"]) / 2 ** 20 for d in s],
                    label=f"PD ({NOME[ling]}) medido", **ESTILO[(ling, "pd")], ms=6, lw=2)
    vs = sorted({int(d["V"]) for d in dados})
    ax.plot(vs, [8 * (v + 1) / 2 ** 20 for v in vs], color="0.45", ls=":", lw=1.8,
            label="teórico 8·(V+1) bytes (lista de ponteiros)")
    ax.plot(vs, [4 * (v + 1) / 2 ** 20 for v in vs], color="0.45", ls="-.", lw=1.5,
            label="teórico 4·(V+1) bytes (int[] do Java)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("V (valor a pagar)")
    ax.set_ylabel("memória alocada (MiB)")
    ax.set_title("Memória da PD cresce junto com V: Θ(V) (o guloso usa memória constante)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig5_memoria.png"))
    plt.close(fig)
    return dados


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
    print(f"resumo.csv, ajustes.csv e figuras gravados em {a.resultados}/ e {a.graficos}/")


if __name__ == "__main__":
    main()
