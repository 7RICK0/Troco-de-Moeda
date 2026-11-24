# Diagnóstico técnico final

Revisão de 24/11/2026, sobre a branch `revisao/criterios-professor`.

## Resultado das verificações

| Verificação | Resultado |
|---|---|
| Suíte automatizada Python/Java | 20 testes aprovados, sem testes ignorados |
| PD versus força bruta | 400 instâncias pequenas conferidas |
| Sistemas canônicos e contraexemplos | Verificados; divergências do guloso são esperadas nos contraexemplos |
| Estudo ampliado do caso médio E3 | 140 entradas: 7 tamanhos × 20 valores distintos |
| Cobertura do E3 | 4 implementações × 140 entradas × 20 repetições = 11.200 medições |
| Estatísticas | Média e desvio temporal por entrada; média e desvio entre entradas por tamanho |
| Reprodução rápida | Comando completo executado com sucesso, incluindo tempo, memória, figuras e E3 reduzido |
| Geração do relatório | Contagem de testes e apêndice E3 atualizados; 14 páginas verificadas |
| Regeneração do apêndice | Segunda execução mantém 14 páginas, sem duplicação |
| Entradas e resultados originais | 14 arquivos originais de entrada/resultados preservados byte a byte |
| Importações dos módulos Python | Sem importações não utilizadas na análise estática |
| Caches, classes compiladas e execução rápida | Mantidos fora do versionamento pelo .gitignore |

## Problemas corrigidos

- O caso médio era representado por uma única entrada sorteada por tamanho. E3 agora amostra 20 valores distintos por tamanho, usando uma RNG independente, e mede cada entrada 20 vezes.
- A nova consolidação não confunde desvio entre entradas com o ruído temporal das repetições. As médias por entrada têm pesos iguais.
- Os leitores Python e Java rejeitam moedas não positivas, repetidas ou fora de ordem, quantidade incorreta de moedas, V fora do intervalo compartilhado e IDs repetidos.
- Opções sem valor, repetições inválidas, limites negativos e seleção vazia são rejeitados pelos medidores.
- O coletor de lixo do Python tem seu estado restaurado mesmo se a medição falhar.
- O Java verifica suporte à medição de memória alocada por thread. A compilação usa UTF-8 explicitamente.
- A validação dos CSV exige todas as implementações e repetições, rejeita duplicações, tempos não finitos, lotes inválidos, metadados n/V divergentes e respostas inconsistentes.
- A rotina completa valida a execução publicada antes de gerar novas medições, valida novamente os novos resultados e inclui E3. O estudo não depende de importar o módulo de testes: a validação compartilhada está em um módulo próprio.
- README e PDF foram sincronizados com o estudo novo. Há um comando opcional para regenerar o apêndice do relatório sem duplicá-lo.
- O teste automatizado no GitHub usa Python 3.12 e JDK 21; não executa benchmarks demorados.

## Limpeza e dependências

Não foram encontrados módulos, funções ou figuras anteriores comprovadamente abandonados: algoritmos, medidores, gerador, consolidação, análise dos sistemas aleatórios e testes têm referências no fluxo ou na documentação. Funções de verificação independentes foram mantidas deliberadamente. Foram removidas importações sem uso introduzidas durante a implementação e a dependência de execução sobre o módulo de testes. Nenhum arquivo de resultado foi apagado apenas por parecer antigo: E1/E2 continuam sendo evidências do relatório.

Os arquivos novos têm uso definido: `estudar_caso_medio.py` executa E3; `validar_resultados.py` é usado pelo estudo e pelos testes; `atualizar_relatorio.py` gera o apêndice; seus requisitos ficam separados das dependências normais de execução. Os CSV de resumo e ajustes alimentam a figura e o PDF.

## Limitações práticas preservadas e declaradas

- E1/E2 são medições originais em Windows/JDK 25. Não foram integralmente reexecutadas nesta revisão; suas entradas e dados brutos foram preservados. E3 foi executado em Linux, CPython 3.12.14 e OpenJDK 21.0.13, com ambiente registrado em `resultados/caso_medio/ambiente.txt`.
- Nenhuma comparação de tempo absoluto mistura máquinas diferentes. A reprodução completa em outra máquina produzirá tempos diferentes dos publicados.
- O caso médio tem uma distribuição de entrada explícita; a amostra finita não precisa coincidir exatamente com a esperança teórica. Ajustes log-log em um intervalo finito não provam complexidade.
- Lotes Java continuam sujeitos a otimizações do JIT. Consumo do resultado e warm-up reduzem problemas, mas não demonstram ausência de todas as otimizações. Não foi alegado uso de JMH.
- A PD continua pseudopolinomial e limitada por tempo e memória. O leitor das quatro implementações usa V ≤ 2³¹ − 3; aceitar um número nesse intervalo não garante memória suficiente para a tabela.
- Memória Python é pico rastreado; memória Java é total alocado pela thread durante a chamada. São métricas diferentes, identificadas no relatório.
- A nova execução foi validada em Linux. A compatibilidade anunciada com Windows/macOS depende de Python, JDK e bibliotecas disponíveis; não houve nova execução nesses sistemas nesta revisão.

O código está validado para o escopo acadêmico e para os contratos documentados. Esta verificação não é uma garantia de ausência universal de defeitos nem determina a nota da apresentação oral.
