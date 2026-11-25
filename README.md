# Troco de moedas: guloso × programação dinâmica

**CESAR School** · Ciência da Computação · **Teoria da Computação** · Prof. Daniel Bezerra · Turma B · Grupo 7

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![Java](https://img.shields.io/badge/Java-21%2B-ED8B00?style=flat&logo=openjdk&logoColor=white)
![matplotlib](https://img.shields.io/badge/matplotlib-11557c?style=flat)
![numpy](https://img.shields.io/badge/numpy-013243?style=flat&logo=numpy&logoColor=white)

## O que é este projeto

Pagar um valor V usando o **menor número possível de moedas**. Comparamos duas soluções, cada uma em **Python** e em **Java** (4 implementações), com as mesmas entradas e contra o que a teoria prevê:

- **Algoritmo A, guloso:** pega sempre a maior moeda que cabe no que falta. É muito rápido, mas **às vezes erra**: com moedas {1, 3, 4} e V = 6, usa 4 + 1 + 1 (3 moedas) em vez de 3 + 3 (2). Com as moedas do real, acerta sempre.
- **Algoritmo B, programação dinâmica (PD):** calcula o melhor troco para 1, 2, 3, … até V, reaproveitando as respostas anteriores. **Sempre acerta**, mas o tempo cresce com o valor de V.

## Principais links

<table>
  <tr>
    <td align="center" width="50%">
      <a href="relatorio/relatorio_troco_de_moedas_v1.pdf"><img src="relatorio/miniatura_capa.png" alt="Relatório em PDF" width="260"></a>
      <br><b>Relatório (PDF)</b>
      <br>Análise completa, todos os gráficos, ambiente, contribuições e declaração de uso de IA.
    </td>
    <td align="center" width="50%">
      <a href="slides/troco_de_moedas_slides.pdf"><img src="slides/miniatura_slides.png" alt="Slides da apresentação" width="260"></a>
      <br><b>Slides (PDF)</b>
      <br>Apresentação: problema, algoritmos, complexidade, experimentos, resultados e P × NP.
    </td>
  </tr>
</table>

## Requisitos atendidos

| Requisito | Onde está |
|---|---|
| 4 implementações (2 algoritmos × 2 linguagens) | [src/python/troco.py](src/python/troco.py), [src/java/Troco.java](src/java/Troco.java) |
| Geração de entradas com semente fixa | [scripts/gerar_entradas.py](scripts/gerar_entradas.py) → [entradas/](entradas/) |
| Medição de tempo e memória | [src/python/medir.py](src/python/medir.py), [src/java/Medir.java](src/java/Medir.java) |
| Testes de corretude | [testes/](testes/) |
| Gráficos e tabelas | [scripts/graficos.py](scripts/graficos.py) → [graficos/](graficos/) |
| Resultados brutos | [resultados/](resultados/) |
| Relatório (7 itens, ambiente, contribuições, uso de IA) | [relatorio/](relatorio/) |
| Reprodução completa | [scripts/rodar_tudo.py](scripts/rodar_tudo.py) |

## Respostas aos requisitos

1. **Problema e algoritmos:** guloso (maior moeda primeiro, com divisão inteira) e PD (`dp[v] = min(dp[v−c] + 1)`). Relatório, seção 1.1.
2. **Classificação:** guloso O(n) e Ω(1) no laço (Θ(n) no pior caso, Θ(1) no melhor), O(n log n) com a ordenação. PD O(n·V), Θ(n·V) com as moedas ≤ V/2, e espaço Θ(V). Seção 1.2.
3. **Casos:** guloso melhor = V múltiplo da maior moeda (1 iteração); pior = n iterações; médio (n+1)/2 iterações no sistema {1,…,n}. A PD faz o mesmo trabalho para C e V fixos. Seção 1.3.
4. **Aplicabilidade:** guloso em sistemas em que ele acerta (real, euro, dólar), com qualquer V; PD em sistemas arbitrários com V moderado. Seção 1.4.
5. **Simulação:** E1 varia V de 10³ a 10⁷; E2 varia n de 4 a 1024 nos 3 casos; E3 mede o caso médio com 20 entradas por tamanho. Seções 2.1 e 2.7.
6. **Gráficos:** teórico × medido, algoritmo × algoritmo, linguagem × linguagem, casos, memória e caso médio. Seção 2.
7. **P × NP:** a decisão "dá para pagar V com ≤ k moedas?" está em NP e é NP-completa (Lueker, 1975). A PD é **pseudopolinomial** (polinomial no valor de V, exponencial no número de dígitos), então não prova que o problema está em P. **Problema vizinho:** no caso geral o troco é NP-difícil no sentido fraco; num sistema canônico fixo, como o real, está em P (guloso O(n)). O guloso não tem garantia de aproximação: em {1, k, k+1} com V = 2k usa k moedas contra 2. Seção 1.5.

## Resultados principais

Tempo médio por chamada no E1 (moedas do real em centavos, n = 13, 20 repetições):

| V | Guloso Python | Guloso Java | PD Python | PD Java |
| ---: | ---: | ---: | ---: | ---: |
| 1.016 | 590,3 ns | 8,2 ns | 453,20 µs | 3,25 µs |
| 3.203 | 659,7 ns | 8,1 ns | 1,85 ms | 11,02 µs |
| 10.065 | 583,2 ns | 7,9 ns | 7,67 ms | 37,60 µs |
| 31.689 | 1,27 µs | 17,8 ns | 27,80 ms | 158,40 µs |
| 100.083 | 619,1 ns | 11,6 ns | 87,52 ms | 554,20 µs |
| 316.242 | 883,2 ns | 18,3 ns | 318,40 ms | 1,86 ms |
| 1.000.029 | 591,3 ns | 9,0 ns | 961,40 ms | 6,43 ms |
| 3.162.355 | 681,9 ns | 13,5 ns | 2,87 s | 19,89 ms |
| 10.000.080 | 629,9 ns | 11,3 ns | 9,84 s | 78,55 ms |

- PD: expoente log-log 1,07 (Python) e 1,10 (Java), perto do 1 previsto por Θ(n·V).
- Guloso: tempo constante em V (expoente 0,00 / 0,05).
- Na PD o Python foi de 125 a 204 vezes mais lento que o Java. A constante muda; o expoente, não.

**Limitações:** os tempos absolutos dependem da máquina (E1/E2 na seção 3 do relatório, E3 na seção 2.7); a PD em Python vai até V = 10⁷ por tempo e memória; o guloso só foi medido em sistemas em que ele acerta; os tempos do guloso Java são médias de chamadas em lote, sujeitas a otimizações do JIT.

## Como reproduzir

Pré-requisitos: **Python 3.10+** e **JDK 21+** no terminal (Windows, Linux ou macOS).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python scripts/rodar_tudo.py --rapido      # demonstração reduzida (cerca de 1 min), saída em saida_rapida/
python scripts/rodar_tudo.py               # completo: E1/E2 + E3 (a duração depende da máquina)
python -m unittest discover -s testes -v   # só os testes (compila o Java sozinho)
```

Para o modo completo, feche programas pesados, porque o tempo medido depende disso.

### Rodar cada parte separadamente

```bash
python scripts/gerar_entradas.py                       # recria entradas/ (semente 2026)
javac -encoding UTF-8 -d build src/java/*.java         # compila o Java
java -cp build Medir tempo entradas/bench_V.txt saida_java.csv --reps 20
python src/python/medir.py tempo entradas/bench_V.txt saida_python.csv --reps 20
python scripts/graficos.py --resultados resultados --graficos graficos
python scripts/estudar_caso_medio.py                   # E3 (caso médio ampliado)
```

Modos do medidor (iguais em Python e Java): `tempo`, `memoria` e `respostas`. As opções `--max-V` e `--max-n` limitam o tamanho das instâncias.

### Formato dos arquivos de entrada

Uma instância por linha; linhas que começam com `#` são comentários:

```
id experimento caso V n c1 c2 ... cn
V_medio_00 E1 medio 1016 13 20000 10000 5000 2000 1000 500 200 100 50 25 10 5 1
```

As moedas vêm em ordem **decrescente**, positivas e distintas, e V fica entre 0 e 2³¹ − 3. A resposta é o número de moedas, ou `-1` se não há solução.

## Arquitetura do projeto

O caminho dos dados: `gerar_entradas` cria as entradas → as 4 implementações medem → os CSV vão para `resultados/` → `graficos` gera tabelas e figuras → relatório e slides usam esses números.

```
.
├── src/                          os algoritmos e os medidores
│   ├── python/
│   │   ├── troco.py              guloso e PD em Python; leitura dos arquivos de entrada
│   │   └── medir.py              mede tempo (em lotes, 20 repetições) e memória (tracemalloc) em Python
│   └── java/
│       ├── Troco.java            guloso e PD em Java
│       └── Medir.java            mede tempo (em lotes, com aquecimento do JIT) e memória em Java
│
├── scripts/                      tudo o que gera, roda e analisa
│   ├── rodar_tudo.py            
│   ├── gerar_entradas.py         
│   ├── graficos.py               
│   ├── analisar_sistemas.py     
│   ├── estudar_caso_medio.py     
│   └── validar_resultados.py     
│
├── testes/                       testes automáticos
│   ├── test_troco.py             
│   └── test_experimentos.py      
│
├── entradas/                     as instâncias lidas pelas 4 implementações
│   ├── bench_V.txt               
│   ├── bench_n.txt              
│   ├── bench_medio.txt           
│   ├── contraexemplos.txt        sistemas em que o guloso erra
│   └── aleatorias.txt            instâncias pequenas para os testes de corretude
│
├── resultados/                   os dados medidos (CSV)
│   ├── tempos_*.csv              
│   ├── memoria_*.csv             
│   ├── resumo.csv, ajustes.csv   médias, desvios e expoentes calculados
│   ├── sistemas_aleatorios.csv   com que frequência o guloso erra
│   ├── ambiente.txt              máquina, sistema e versões usadas em E1/E2
│   └── caso_medio/               dados e ambiente do E3
│
├── graficos/                     
├── relatorio/                   
├── slides/                      
├── .github/workflows/testes.yml  roda os testes a cada push
└── requirements.txt              
```

## Extras do projeto

| Extra | Por quê |
|---|---|
| Medição de memória e comparação com Θ(V) | Bônus |
| Caso médio ampliado (E3): 20 entradas por tamanho | Mede a média de verdade, em vez de um único sorteio |
| Análise de sistemas aleatórios | Mostra com que frequência o guloso erra (item 4) |
| Verificação de canonicidade (Kozen e Zaks) e testes automáticos no GitHub | Garante que as 4 implementações dão a mesma resposta |
| Modo `--rapido` | Qualquer pessoa confere a reprodução em cerca de 1 minuto |

## Contribuições

| Integrante | Papel | O que fez |
|---|---|---|
| Erick Acioli Belo | Coordenação técnica e integração | Coordenou o projeto e atuou junto às duas duplas; fez a implementação em Java; integrou as entregas no repositório; conferiu testes e resultados; consolidou e revisou código, relatório, gráficos, README e apresentação. |
| Luis Guilherme Alves | Dupla 1: desenvolvimento e análise | Implementou os algoritmos em Python; participou da verificação de equivalência com Java e da análise de complexidade; contribuiu para as explicações técnicas do relatório e para a apresentação. |
| José Braz | Dupla 1: desenvolvimento e análise | Revisou os algoritmos; analisou os casos de execução e a discussão sobre P e NP; relacionou os resultados experimentais ao comportamento teórico; participou do relatório e da apresentação. |
| João Luiz | Dupla 2: experimentos e validação | Participou da preparação das entradas, da execução dos testes e das medições de tempo e memória; conferiu as respostas entre as linguagens; documentou o ambiente e a reprodução. |
| Júlio Cesar | Dupla 2: experimentos e validação | Participou da execução dos casos de teste e da conferência dos dados; organizou tabelas e gráficos; preparou os slides sobre os testes e os resultados. |

A declaração de uso de IA está na seção 5 do [relatório](relatorio/relatorio_troco_de_moedas_v1.pdf).
