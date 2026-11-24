"""Atualiza a contagem de testes e o apêndice E3 do PDF publicado, sem duplicá-lo.

Dependências opcionais: pip install -r requirements-relatorio.txt
Uso: python scripts/atualizar_relatorio.py
O corpo E1/E2 do PDF é preservado; suas medições pertencem ao ambiente original.
"""
import csv
from pathlib import Path
import unittest
from xml.sax.saxutils import escape

import pymupdf as fitz
import reportlab
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

RAIZ = Path(__file__).resolve().parents[1]
TITULO = '12. Caso médio ampliado (E3)'


def main():
    res = RAIZ/'resultados/caso_medio'
    with (res/'resumo_por_tamanho.csv').open(encoding='utf-8') as f:
        dados = list(csv.DictReader(f))
    with (res/'ajustes.csv').open(encoding='utf-8') as f:
        ajustes = list(csv.DictReader(f))
    ntestes = unittest.defaultTestLoader.discover(str(RAIZ/'testes')).countTestCases()
    destino = RAIZ/'relatorio/relatorio_troco_de_moedas_v1.pdf'
    d = fitz.open(destino)
    for i, pg in enumerate(d):
        if TITULO in pg.get_text():
            d.delete_pages(i, len(d)-1)
            break
    pg = d[4]
    linhas = sorted([( ''.join(s['text'] for s in l['spans']), fitz.Rect(l['bbox']))
                     for b in pg.get_text('dict')['blocks'] for l in b.get('lines',[])],
                    key=lambda x:(x[1].y0,x[1].x0))
    inicio = next(i for i,(t,_) in enumerate(linhas) if t.startswith('9. Corretude:'))
    fim = next(i for i in range(inicio+1,len(linhas)) if linhas[i][0].startswith('10. Teórico'))
    rect = fitz.Rect(linhas[inicio][1])
    for _, box in linhas[inicio+1:fim]: rect |= box
    rect.x1=539
    pg.add_redact_annot(rect,fill=(1,1,1)); pg.apply_redactions(images=0,graphics=0)
    texto = (f'9. Corretude: {ntestes} testes automatizados em testes/: força bruta, equivalência Java/Python, '
             'canonicidade, limites, entradas e parâmetros inválidos, amostragem, consolidação e integridade dos CSV. '
             'E3 amplia o caso médio com 20 entradas por tamanho (seção 12).')
    assert pg.insert_textbox(rect,texto,fontname='helv',fontsize=9,lineheight=1.1)>=0
    # Fonte incluída com ReportLab: evita dependência de Arial instalada no sistema.
    fontes=Path(reportlab.__file__).parent/'fonts'
    pdfmetrics.registerFont(TTFont('RelVera',str(fontes/'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('RelVeraBold',str(fontes/'VeraBd.ttf')))
    pdfmetrics.registerFontFamily('RelVera',normal='RelVera',bold='RelVeraBold')
    body=ParagraphStyle('body',fontName='RelVera',fontSize=9.4,leading=13,spaceAfter=8)
    head=ParagraphStyle('head',parent=body,fontName='RelVeraBold',fontSize=13,leading=16,spaceAfter=12)
    small=ParagraphStyle('small',parent=body,fontSize=8,leading=11,spaceAfter=6)
    def par(t,style=body):return Paragraph(t,style)
    def tabela(rows,widths):
        tb=Table([[par(str(c),small) for c in row] for row in rows],colWidths=widths,hAlign='LEFT')
        tb.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.4,colors.grey),
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('TOPPADDING',(0,0),(-1,-1),5)]))
        return tb
    idx={(x['linguagem'],x['algoritmo'],int(x['n'])):x for x in dados}
    ns=sorted({int(x['n']) for x in dados})
    rows=[['n','Guloso Python (µs)','Guloso Java (µs)','PD Python (ms)','PD Java (ms)']]
    for n in ns:
        row=[n]
        for ling,alg,div in [('python','guloso',1e3),('java','guloso',1e3),('python','pd',1e6),('java','pd',1e6)]:
            x=idx[(ling,alg,n)]
            row.append(f"{float(x['media_ns'])/div:.3f} ± {float(x['desvio_entre_entradas_ns'])/div:.3f}")
        rows.append(row)
    story=[par(TITULO,head),par('12.1 Metodologia e ambiente',head),
      par('E3 complementa E1/E2 com uma amostra de entradas, em vez de repetir apenas um valor por tamanho. São 7 tamanhos geométricos (n de 4 a 256), 20 valores V distintos por tamanho e 20 repetições por entrada: 140 entradas e 11.200 medições nas quatro implementações.'),
      par('Para cada n, as moedas são {1, ..., n}; V é sorteado sem reposição em um intervalo de 10·n inteiros próximo de 10.000, alinhado a múltiplos de n. A semente independente é 2027. A população tem restos uniformes; a amostra finita pode se afastar de E[I] = (n+1)/2. Os dois algoritmos e as duas linguagens recebem exatamente as mesmas entradas.'),
      par('A média por tamanho é a média das 20 médias por entrada, com o mesmo peso para cada entrada. O desvio entre entradas e o desvio temporal médio das repetições são registrados separadamente. As barras da Figura 7 representam o desvio entre entradas, e não um intervalo de confiança.'),
      par('Os tempos de E3 não são misturados aos de E1/E2: foram obtidos em outro ambiente. O ambiente original da seção 8 continua válido para as Tabelas 4 a 8 e Figuras 2 a 6.'),
      par(escape((res/'ambiente.txt').read_text()).replace('\n','<br/>'),small),
      par('12.2 Resultados do caso médio',head),
      par('Tabela 10 - Média ± desvio entre as 20 entradas de cada tamanho.',small),tabela(rows,[35,112.5,112.5,112.5,112.5]),Spacer(1,10),
      par('Arquivos: entradas/bench_medio.txt; resultados/caso_medio/tempos_*.csv; resumo_por_entrada.csv; resumo_por_tamanho.csv e ajustes.csv. A validação exige as quatro implementações, todas as repetições, metadados coerentes e respostas iguais. Os testes independentes verificam também a esperança de iterações sobre todos os restos.',small),PageBreak(),
      par('12.3 Interpretação e limites',head),Image(str(RAIZ/'graficos/fig7_caso_medio.png'),width=485,height=323.33),
      par('Figura 7 - Tempos médios, dispersão entre entradas, iterações observadas e razão entre tempo e passos previstos. Todas as séries desta figura pertencem ao ambiente E3.',small)]
    itrows=[['n','Iterações médias observadas','Esperança teórica (n+1)/2']]
    for n in ns:
        x=idx[('python','guloso',n)];itrows.append([n,f"{float(x['iteracoes_medias']):.2f}",f"{float(x['iteracoes_esperadas']):.2f}"])
    story += [tabela(itrows,[45,220,220]),Spacer(1,8),
      par('Expoentes ajustados T ≈ a·n^b: '+ '; '.join(f"{x['algoritmo']} {x['linguagem']}: b = {float(x['expoente_tempo']):.2f}" for x in ajustes)+'.',small),
      par('A variação do número de iterações entre entradas é parte do comportamento do guloso; a PD percorre uma tabela com custo próximo de n·V nas condições usadas. Desvios do expoente 1 podem refletir amostragem, custos fixos e o intervalo finito de n; o ajuste experimental não constitui prova de complexidade.',small),
      par('Conclusão: o guloso é indicado quando a canonicidade está garantida; a PD fornece o ótimo para denominações arbitrárias com quantidade ilimitada e V moderado. O estudo amplia a evidência experimental, sem alterar as classes assintóticas. Persistem limites de memória, ruído de execução e possíveis otimizações do JIT nos lotes Java; não foi alegada validação por JMH.',small)]
    temporario=RAIZ/'build/apendice_e3.pdf'
    temporario.parent.mkdir(exist_ok=True)
    SimpleDocTemplate(str(temporario),pagesize=(595.28,841.89),leftMargin=55,rightMargin=55,topMargin=45,bottomMargin=45).build(story)
    ap=fitz.open(temporario)
    assert len(ap)==2, f'Apêndice com {len(ap)} páginas: revisar layout'
    d.insert_pdf(ap)
    saida=destino.with_suffix('.tmp.pdf'); d.save(saida,garbage=4,deflate=True);d.close();ap.close();saida.replace(destino)
    print(f'Relatório atualizado: {ntestes} testes; apêndice E3 com 2 páginas.')


if __name__=='__main__':main()
