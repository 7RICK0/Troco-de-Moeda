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

ESTILO = {  # preto e branco: linguagem = traço, algoritmo = marcador
    ("python", "pd"): dict(color="black", ls="-", marker="o"),
    ("java", "pd"): dict(color="black", ls="--", marker="s"),
    ("python", "guloso"): dict(color="0.5", ls="-", marker="^"),
    ("java", "guloso"): dict(color="0.5", ls="--", marker="v"),
}
NOME = {"python": "Python", "java": "Java", "pd": "PD", "guloso": "Guloso"}
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.grid": True,
                     "grid.color": "0.85", "figure.dpi": 150})


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
        ax.errorbar(xs, ys, yerr=[l["desvio_ns"] / 1e6 for l in s], ms=4, lw=1.2, capsize=2,
                    label=rotulo or f"{NOME[alg]} ({NOME[ling]})", **est)
    else:
        ax.plot(xs, ys, ms=4, lw=1.2, label=rotulo or f"{NOME[alg]} ({NOME[ling]})", **est)


def fig_teorico(linhas, pasta):
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
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
        ax.axhline(1, color="0.3", lw=0.8, ls=":")
        ax.set_ylim(0, max(2.0, ax.get_ylim()[1]))
        ax.legend(fontsize=7)
    axs[0].set_title("(a) PD variando V (n = 13)")
    axs[0].set_xlabel("V")
    axs[0].set_ylabel("[T/f] ÷ [T/f no maior tamanho]")
    axs[1].set_title("(b) Variando n (V ≈ 10^5, pior caso do guloso)")
    axs[1].set_xlabel("n (tipos de moeda)")
    fig.suptitle("Teórico × medido: a razão T(x)/f(x) tende a uma constante (linha = 1)")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig1_teorico_vs_medido.png"))
    plt.close(fig)


def fig_algoritmos(linhas, pasta):
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.8))
    for ling in ("python", "java"):
        for alg in ("pd", "guloso"):
            plot_linha(axs[0], serie(linhas, ling, alg, "E1", "medio", "V"), "V", ling, alg)
            plot_linha(axs[1], serie(linhas, ling, alg, "E2", "pior", "n"), "n", ling, alg)
    for ax in axs:
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_ylabel("tempo por chamada (ms)")
    h, rot = axs[0].get_legend_handles_labels()
    fig.legend(h, rot, loc="lower center", ncol=4, fontsize=8, frameon=False)
    axs[0].set_xlabel("V")
    axs[0].set_title("(a) Variando V (n = 13)", pad=28)
    eixo_digitos(axs[0])
    axs[1].set_xlabel("n (tipos de moeda)")
    axs[1].set_title("(b) Variando n (V ≈ 10^5, pior caso do guloso)", pad=28)
    fig.suptitle("Algoritmo × algoritmo (escala log-log)")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(os.path.join(pasta, "fig2_guloso_vs_pd.png"))
    plt.close(fig)


def fig_linguagens(linhas, pasta):
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
    for ax, exp, eixo, caso in ((axs[0], "E1", "V", "medio"), (axs[1], "E2", "n", "pior")):
        for alg in ("pd", "guloso"):
            py = {l[eixo]: l["media_ns"] for l in serie(linhas, "python", alg, exp, caso, eixo)}
            jv = {l[eixo]: l["media_ns"] for l in serie(linhas, "java", alg, exp, caso, eixo)}
            xs = sorted(set(py) & set(jv))
            if xs:
                ax.plot(xs, [py[x] / jv[x] for x in xs], label=NOME[alg],
                        **ESTILO[("python", alg)], ms=4, lw=1.2)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.legend(fontsize=7)
        ax.set_ylabel("tempo Python ÷ tempo Java")
    axs[0].set_xlabel("V")
    axs[0].set_title("(a) Variando V (n = 13)")
    axs[1].set_xlabel("n (tipos de moeda)")
    axs[1].set_title("(b) Variando n (pior caso do guloso)")
    fig.suptitle("Linguagem × linguagem: quantas vezes o Python é mais lento")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "fig3_python_vs_java.png"))
    plt.close(fig)


def fig_casos(linhas, pasta):
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
    tons = {"melhor": "0.65", "medio": "0.35", "pior": "black"}
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
        ax.legend(fontsize=6.5, ncol=2)
    axs[0].set_title("(a) Guloso: melhor, médio e pior caso")
    axs[1].set_title("(b) PD nas mesmas entradas")
    fig.suptitle("Casos forçados (V ≈ 10^5, sistema {1, ..., n})")
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
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    for ling in ("python", "java"):
        s = sorted((d for d in dados if d["linguagem"] == ling and d["algoritmo"] == "pd"),
                   key=lambda d: int(d["V"]))
        if s:
            ax.plot([int(d["V"]) for d in s], [int(d["bytes_pico"]) / 2 ** 20 for d in s],
                    label=f"PD ({NOME[ling]}) medido", **ESTILO[(ling, "pd")], ms=4, lw=1.2)
    vs = sorted({int(d["V"]) for d in dados})
    ax.plot(vs, [8 * (v + 1) / 2 ** 20 for v in vs], color="0.6", ls=":", lw=1.5,
            label="teórico 8·(V+1) B (lista de ponteiros)")
    ax.plot(vs, [4 * (v + 1) / 2 ** 20 for v in vs], color="0.6", ls="-.", lw=1.2,
            label="teórico 4·(V+1) B (int[] do Java)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("V")
    ax.set_ylabel("memória alocada (MiB)")
    ax.set_title("Memória da PD: Θ(V)  (guloso: O(1))")
    ax.legend(fontsize=7)
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
