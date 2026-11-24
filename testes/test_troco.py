"""Testes de corretude das 4 implementações (guloso/PD x Python/Java).

Rodar a partir da raiz do repositório:  python -m unittest discover -s testes -v
"""
import csv
import glob
import os
import subprocess
import sys
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "src", "python"))

sys.path.insert(0, os.path.join(RAIZ, "scripts"))
from validar_resultados import validar_cobertura_resultados

from troco import ler_instancias, troco_guloso, troco_pd  # noqa: E402

ENTRADAS = os.path.join(RAIZ, "entradas")
BUILD = os.path.join(RAIZ, "build")


def forca_bruta(moedas, V):
    """Oráculo independente: tenta todas as quantidades de cada moeda (só para V pequeno)."""
    melhor = None

    def busca(i, resto, usadas):
        nonlocal melhor
        if resto == 0:
            if melhor is None or usadas < melhor:
                melhor = usadas
            return
        if i == len(moedas):
            return
        for q in range(resto // moedas[i] + 1):
            busca(i + 1, resto - q * moedas[i], usadas + q)

    busca(0, V, 0)
    return -1 if melhor is None else melhor


def tabela_pd(moedas, limite):
    """dp[v] para todo v em [0, limite] (uma única passada)."""
    inf = limite + 1
    dp = [inf] * (limite + 1)
    dp[0] = 0
    for c in moedas:
        for v in range(c, limite + 1):
            if dp[v - c] + 1 < dp[v]:
                dp[v] = dp[v - c] + 1
    return [x if x <= limite else -1 for x in dp]


def respostas_java(arquivo, *filtros):
    os.makedirs(BUILD, exist_ok=True)
    fontes = glob.glob(os.path.join(RAIZ, "src", "java", "*.java"))
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", BUILD] + fontes, check=True)
    saida = os.path.join(BUILD, "respostas_" + os.path.basename(arquivo) + ".csv")
    subprocess.run(["java", "-cp", BUILD, "Medir", "respostas", arquivo, saida] + list(filtros),
                   check=True)
    with open(saida, encoding="utf-8") as f:
        return {(r["id"], r["algoritmo"]): int(r["resposta"]) for r in csv.DictReader(f)}


class TestPython(unittest.TestCase):

    def test_casos_conhecidos(self):
        brl = [20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50, 25, 10, 5, 1]
        self.assertEqual(troco_guloso(brl, 0), 0)
        self.assertEqual(troco_pd(brl, 0), 0)
        self.assertEqual(troco_guloso(brl, 289), 8)   # 200+50+25+10+1+1+1+1 (R$ 2,89)
        self.assertEqual(troco_pd(brl, 289), 8)
        self.assertEqual(troco_guloso([4, 3, 1], 6), 3)
        self.assertEqual(troco_pd([4, 3, 1], 6), 2)

    def test_pd_igual_forca_bruta(self):
        for inst in ler_instancias(os.path.join(ENTRADAS, "aleatorias.txt")):
            with self.subTest(id=inst["id"]):
                self.assertEqual(troco_pd(inst["moedas"], inst["V"]),
                                 forca_bruta(inst["moedas"], inst["V"]))

    def test_guloso_nunca_melhor_que_otimo(self):
        for inst in ler_instancias(os.path.join(ENTRADAS, "aleatorias.txt")):
            g = troco_guloso(inst["moedas"], inst["V"])
            o = troco_pd(inst["moedas"], inst["V"])
            if g != -1:
                self.assertNotEqual(o, -1)
                self.assertGreaterEqual(g, o)

    def test_sistemas_do_benchmark_sao_canonicos(self):
        """Kozen & Zaks (1994): se o guloso falha, o menor contraexemplo é < c_(m-1) + c_m.
        Basta comparar guloso e PD para todo V abaixo desse limite."""
        sistemas = {tuple(i["moedas"]) for arq in ("bench_V.txt", "bench_n.txt")
                    for i in ler_instancias(os.path.join(ENTRADAS, arq))}
        for moedas in sistemas:
            limite = moedas[0] + moedas[1] if len(moedas) > 1 else moedas[0]
            dp = tabela_pd(list(moedas), limite)
            for V in range(limite + 1):
                if troco_guloso(list(moedas), V) != dp[V]:
                    self.fail(f"sistema com n={len(moedas)} não é canônico em V={V}")

    def test_contraexemplos(self):
        esperado = {  # id: (guloso, pd)
            "contra_01": (3, 2), "contra_02": (3, 2), "contra_03": (7, 4),
            "contra_04": (5, 2), "contra_05": (50, 2), "contra_06": (-1, 3),
            "contra_07": (-1, -1), "contra_08": (-1, 3),
        }
        for inst in ler_instancias(os.path.join(ENTRADAS, "contraexemplos.txt")):
            with self.subTest(id=inst["id"]):
                self.assertEqual((troco_guloso(inst["moedas"], inst["V"]),
                                  troco_pd(inst["moedas"], inst["V"])), esperado[inst["id"]])


class TestJavaIgualPython(unittest.TestCase):

    def comparar(self, arquivo, *filtros):
        java = respostas_java(os.path.join(ENTRADAS, arquivo), *filtros)
        insts = ler_instancias(os.path.join(ENTRADAS, arquivo))
        comparadas = 0
        for inst in insts:
            for nome, f in (("guloso", troco_guloso), ("pd", troco_pd)):
                if (inst["id"], nome) not in java:
                    continue
                comparadas += 1
                with self.subTest(id=inst["id"], algoritmo=nome):
                    self.assertEqual(java[(inst["id"], nome)], f(inst["moedas"], inst["V"]))
        self.assertGreater(comparadas, 0)
        return java

    def test_aleatorias(self):
        self.comparar("aleatorias.txt")

    def test_contraexemplos_guloso_diverge_nas_duas_linguagens(self):
        java = self.comparar("contraexemplos.txt")
        for (id_, alg), r in java.items():
            if alg == "guloso" and id_ != "contra_07":
                self.assertNotEqual(r, java[(id_, "pd")], id_)

    def test_benchmark_quatro_iguais(self):
        for arq in ("bench_V.txt", "bench_n.txt"):
            java = self.comparar(arq, "--max-V", "200000", "--max-n", "128")
            for (id_, alg), r in java.items():
                self.assertEqual(r, java[(id_, "pd")], f"{arq} {id_}")




class TestResultadosMedidos(unittest.TestCase):
    def test_respostas_iguais_nos_csv(self):
        arquivos = glob.glob(os.path.join(RAIZ, "resultados", "tempos_*.csv"))
        instancias = [i for nome in ("bench_V.txt", "bench_n.txt")
                      for i in ler_instancias(os.path.join(ENTRADAS, nome))]
        validar_cobertura_resultados(arquivos, instancias)

    def test_rejeita_resultados_incompletos(self):
        import tempfile
        with tempfile.TemporaryDirectory() as pasta:
            arq = os.path.join(pasta, "parcial.csv")
            with open(arq, "w", encoding="utf-8", newline="") as f:
                f.write("id,linguagem,algoritmo,rep,resposta\n"
                        "exemplo,python,pd,0,2\n")
            with self.assertRaisesRegex(AssertionError, "cobertura"):
                validar_cobertura_resultados([arq], [{"id": "exemplo"}])

    def test_rejeita_repeticoes_ausentes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as pasta:
            arq = os.path.join(pasta, "parcial.csv")
            with open(arq, "w", encoding="utf-8", newline="") as f:
                f.write("id,linguagem,algoritmo,rep,resposta\n")
                for ling in ("python", "java"):
                    for alg in ("guloso", "pd"):
                        f.write(f"exemplo,{ling},{alg},0,2\n")
            with self.assertRaisesRegex(AssertionError, "repetições"):
                validar_cobertura_resultados([arq], [{"id": "exemplo"}])


class TestLimitesJava(unittest.TestCase):
    def test_limites_pd_e_algoritmo_invalido(self):
        import tempfile
        fontes = glob.glob(os.path.join(RAIZ, "src", "java", "*.java"))
        with tempfile.TemporaryDirectory() as pasta:
            fonte = os.path.join(pasta, "Limites.java")
            with open(fonte, "w", encoding="utf-8") as f:
                f.write("""
public class Limites {
    public static void main(String[] args) {
        for (int v : new int[] {-1, Integer.MAX_VALUE, Integer.MAX_VALUE - 1}) {
            try {
                Troco.pd(new int[] {1}, v);
                throw new AssertionError("PD deveria rejeitar V=" + v);
            } catch (IllegalArgumentException esperado) {}
        }
        try {
            Troco.executar("invalido", new int[] {1}, 1);
            throw new AssertionError("deveria rejeitar algoritmo desconhecido");
        } catch (IllegalArgumentException esperado) {}
        if (Troco.pd(new int[] {3, 1}, 0) != 0 ||
            Troco.pd(new int[] {4, 3, 1}, 6) != 2)
            throw new AssertionError("regressão nas entradas válidas");
    }
}
""")
            subprocess.run(["javac", "-encoding", "UTF-8", "-d", pasta] + fontes + [fonte], check=True)
            subprocess.run(["java", "-cp", pasta, "Limites"], check=True)


if __name__ == "__main__":
    unittest.main()
