"""E3: caso médio com 20 entradas distintas por tamanho e 20 repetições por entrada.

python scripts/estudar_caso_medio.py
python scripts/estudar_caso_medio.py --rapido  # demonstração; não substitui os dados completos
"""
import argparse
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

from gerar_entradas import gerar_bench_medio
from graficos import carregar, expoente, salvar_csv, passos_teoricos
from rodar_tudo import registrar_ambiente, rodar, PY, RAIZ

from validar_resultados import validar_cobertura_resultados
from troco import ler_instancias


def consolidar(res, entradas, figura):
    linhas = carregar(str(res), str(entradas))
    salvar_csv(str(res / 'resumo_por_entrada.csv'), linhas)
    grupos = {}
    for l in linhas:
        grupos.setdefault((l['linguagem'], l['algoritmo'], l['n']), []).append(l)
    resumo = []
    for (ling, alg, n), grupo in sorted(grupos.items()):
        medias = [l['media_ns'] for l in grupo]
        moedas = list(range(n, 0, -1))
        it = [passos_teoricos('guloso', moedas, l['V']) for l in grupo]
        f = statistics.mean(l['f_passos'] for l in grupo)
        resumo.append(dict(linguagem=ling, algoritmo=alg, n=n, entradas=len(grupo),
            repeticoes_por_entrada=grupo[0]['repeticoes'], V_medio=statistics.mean(l['V'] for l in grupo),
            media_ns=statistics.mean(medias),
            desvio_entre_entradas_ns=statistics.stdev(medias),
            desvio_temporal_medio_ns=statistics.mean(l['desvio_ns'] for l in grupo),
            iteracoes_medias=statistics.mean(it), iteracoes_esperadas=(n+1)/2,
            f_passos_medio=f, ns_por_passo=statistics.mean(medias)/f))
    salvar_csv(str(res / 'resumo_por_tamanho.csv'), resumo)
    ajustes = []
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    cores = {'python': '#0072B2', 'java': '#D55E00'}
    for j, alg in enumerate(('guloso', 'pd')):
        ax = axs[0, j]
        for ling in ('python', 'java'):
            s = [l for l in resumo if l['algoritmo'] == alg and l['linguagem'] == ling]
            xs = [l['n'] for l in s]
            ys = [l['media_ns']/1e6 for l in s]
            ax.errorbar(xs, ys, yerr=[l['desvio_entre_entradas_ns']/1e6 for l in s],
                        marker='o', color=cores[ling], label=ling, capsize=3)
            ajustes.append(dict(linguagem=ling, algoritmo=alg, pontos=len(xs),
                expoente_tempo=expoente(xs, ys)))
            axs[1, 1].plot(xs, [l['ns_por_passo']/s[-1]['ns_por_passo'] for l in s],
                           marker='o', color=cores[ling], ls='-' if alg == 'pd' else '--',
                           label=f'{ling} {alg}')
        ax.set(xscale='log', yscale='log', xlabel='n (tipos de moeda)', ylabel='tempo (ms)',
               title=f'{alg}: média entre entradas; barras = desvio entre entradas')
        ax.legend()
    s = [l for l in resumo if l['linguagem'] == 'python' and l['algoritmo'] == 'guloso']
    axs[1, 0].plot([l['n'] for l in s], [l['iteracoes_medias'] for l in s], 'o-', label='amostra')
    axs[1, 0].plot([l['n'] for l in s], [l['iteracoes_esperadas'] for l in s], ':', label='E[I] = (n+1)/2')
    axs[1, 0].set(xscale='log', yscale='log', xlabel='n', ylabel='iterações do guloso', title='Amostra aleatória e esperança teórica')
    axs[1, 0].legend()
    axs[1, 1].set(xscale='log', xlabel='n', ylabel='T / passos (normalizado)', title='Custo relativo por passo previsto')
    axs[1, 1].axhline(1, ls=':', color='0.5')
    axs[1, 1].legend(fontsize=8)
    fig.suptitle(f'E3: {resumo[0]["entradas"]} entradas por tamanho; V próximo de 10.000')
    fig.tight_layout()
    figura.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figura, dpi=180)
    plt.close(fig)
    salvar_csv(str(res/'ajustes.csv'), ajustes)
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rapido', action='store_true')
    a = p.parse_args()
    raiz = Path(RAIZ)
    res = raiz / ('saida_rapida/caso_medio' if a.rapido else 'resultados/caso_medio')
    res.mkdir(parents=True, exist_ok=True)
    entrada = raiz/'entradas/bench_medio.txt'
    # Arquivo determinístico independente dos geradores E1/E2.
    entrada.write_text('\n'.join(gerar_bench_medio())+'\n', encoding='utf-8')
    inst = ler_instancias(entrada)
    if a.rapido:
        inst = [i for i in inst if i['n'] <= 16 and i['id'].endswith(('_00', '_01'))]
        entrada = res/'bench_medio.txt'
        from gerar_entradas import linha
        entrada.write_text('\n'.join(linha(i['id'], 'E3', 'medio', i['V'], i['moedas']) for i in inst)+'\n', encoding='utf-8')
    reps = 3 if a.rapido else 20
    fontes = sorted(str(x) for x in (raiz/'src/java').glob('*.java'))
    rodar(['javac', '-encoding', 'UTF-8', '-d', 'build']+fontes)
    registrar_ambiente(str(res))
    for ling, cmd in [('java', ['java', '-cp', 'build', 'Medir']),
                      ('python', [PY, 'src/python/medir.py'])]:
        rodar(cmd+['tempo', str(entrada), str(res/f'tempos_{ling}.csv'), '--reps', str(reps)])
    arquivos = [str(res/f'tempos_{ling}.csv') for ling in ('java', 'python')]
    validar_cobertura_resultados(arquivos, inst, repeticoes=reps)
    # O modo rápido tem entradas isoladas; carregar recebe o diretório certo.
    pasta_entradas = res if a.rapido else raiz/'entradas'
    figura = res/'fig7_caso_medio.png' if a.rapido else raiz/'graficos/fig7_caso_medio.png'
    consolidar(res, pasta_entradas, figura)
    print('E3 validado: quatro implementações, cobertura completa e respostas iguais.')


if __name__ == '__main__':
    main()
