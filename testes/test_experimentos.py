"""Verificações independentes da amostragem, contratos de entrada e consolidação."""
import glob
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from collections import Counter

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ/'scripts'), str(RAIZ/'src/python')]
from gerar_entradas import gerar_bench_medio, TAMANHOS_MEDIO
from troco import ler_instancias
from graficos import carregar
from validar_resultados import validar_cobertura_resultados


class TestAmostragem(unittest.TestCase):
    def test_amostras_distintas_reprodutiveis(self):
        linhas = gerar_bench_medio()
        self.assertEqual(linhas, gerar_bench_medio())
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta)/'bench_medio.txt'
            p.write_text('\n'.join(linhas), encoding='utf-8')
            inst = ler_instancias(p)
        self.assertEqual(Counter(i['n'] for i in inst), {n:20 for n in TAMANHOS_MEDIO})
        for n in TAMANHOS_MEDIO:
            valores = [i['V'] for i in inst if i['n'] == n]
            self.assertEqual(len(set(valores)), 20)
            self.assertTrue(all(8000 <= v <= 12000 for v in valores))

    def test_esperanca_guloso_em_todos_os_restos(self):
        from graficos import passos_teoricos
        for n in (4, 8, 32, 256):
            media = sum(passos_teoricos('guloso', list(range(n,0,-1)), 100*n+r)
                        for r in range(n))/n
            self.assertEqual(media, (n+1)/2)

    def test_resultados_e3_completos(self):
        pasta = RAIZ/'resultados/caso_medio'
        arquivos = list(pasta.glob('tempos_*.csv'))
        if not arquivos:
            self.skipTest('E3 ainda não executado; a rotina valida a cobertura ao terminar')
        validar_cobertura_resultados(arquivos, ler_instancias(RAIZ/'entradas/bench_medio.txt'))


class TestEntrada(unittest.TestCase):
    def test_entradas_malformadas_rejeitadas(self):
        ruins = ['x E1 medio 4 2 3', 'x E1 medio 4 1 0',
                 'x E1 medio 4 2 1 3', 'x E1 medio 4 2 1 1',
                 'x E1 medio -1 1 1', 'x E1 medio 2147483647 1 1',
                 'x E1 medio 4 1 1\nx E1 medio 5 1 1']
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta)/'entrada.txt'
            for texto in ruins:
                with self.subTest(texto=texto):
                    p.write_text(texto, encoding='utf-8')
                    with self.assertRaises(ValueError): ler_instancias(p)
                    # A mesma entrada inválida deve ser rejeitada pelo leitor Java.
                    proc = subprocess.run(['java','-cp',str(RAIZ/'build'),'Medir',
                        'respostas',str(p),str(Path(pasta)/'res.csv')], capture_output=True)
                    self.assertNotEqual(proc.returncode, 0)

    @classmethod
    def setUpClass(cls):
        subprocess.run(['javac','-encoding','UTF-8','-d',str(RAIZ/'build')]+
                       glob.glob(str(RAIZ/'src/java/*.java')),check=True)


class TestConsolidacao(unittest.TestCase):
    def test_media_e_desvio_conhecidos(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta)
            (p/'bench_exemplo.txt').write_text('x E3 medio 6 3 4 3 1\n',encoding='utf-8')
            (p/'tempos_exemplo.csv').write_text(
                'linguagem,algoritmo,id,lote,ns_por_chamada,resposta\n'
                'python,pd,x,1,10,2\npython,pd,x,1,20,2\npython,pd,x,1,30,2\n',encoding='utf-8')
            l = carregar(p,p)[0]
            self.assertEqual(l['media_ns'],20)
            self.assertEqual(l['desvio_ns'],10)
            self.assertEqual(l['repeticoes'],3)

    def test_cobertura_rejeita_duplicacao_e_tempo_nan(self):
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta)/'dados.csv'
            header='id,linguagem,algoritmo,rep,resposta,ns_por_chamada,lote\n'
            for linhas in ['x,python,pd,0,2,10,1\nx,python,pd,0,2,10,1\n',
                           'x,python,pd,0,2,nan,1\n']:
                p.write_text(header+linhas,encoding='utf-8')
                with self.assertRaises(AssertionError):
                    validar_cobertura_resultados([p],[{'id':'x'}])


class TestMedidores(unittest.TestCase):
    def test_parametros_invalidos_nas_duas_linguagens(self):
        import glob
        subprocess.run(['javac','-encoding','UTF-8','-d',str(RAIZ/'build')]+
                       glob.glob(str(RAIZ/'src/java/*.java')), check=True)
        entrada = str(RAIZ/'entradas/contraexemplos.txt')
        with tempfile.TemporaryDirectory() as pasta:
            for flags in (['--reps','0'], ['--max-V','-1'], ['--reps']):
                for cmd in ([sys.executable, str(RAIZ/'src/python/medir.py')],
                            ['java','-cp',str(RAIZ/'build'),'Medir']):
                    with self.subTest(cmd=cmd, flags=flags):
                        p=subprocess.run(cmd+['tempo',entrada,str(Path(pasta)/'saida.csv')]+flags,
                                         capture_output=True)
                        self.assertNotEqual(p.returncode,0)

    def test_gc_restaurado_apos_falha(self):
        import gc
        import medir
        from unittest.mock import patch
        entrada=[dict(id='x',experimento='teste',caso='medio',n=1,V=1,moedas=[1])]
        antes=gc.isenabled()
        with tempfile.TemporaryDirectory() as pasta:
            with patch.object(medir,'calibrar',side_effect=RuntimeError('falha de teste')):
                with self.assertRaises(RuntimeError):
                    medir.modo_tempo(entrada,str(Path(pasta)/'saida.csv'),1)
        self.assertEqual(gc.isenabled(),antes)


if __name__ == '__main__': unittest.main()
