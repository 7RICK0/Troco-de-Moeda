"""Reproduz tudo: entradas, compilação, testes, medições, análise e gráficos.

  python scripts/rodar_tudo.py            # completo (cerca de 30 min)
  python scripts/rodar_tudo.py --rapido   # versão reduzida (cerca de 1 min), saída em saida_rapida/
"""
import argparse
import ctypes
import glob
import os
import platform
import subprocess
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PY = sys.executable


def rodar(cmd):
    print("\n>>", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=RAIZ, check=True)


def saida_cmd(cmd):
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def cpu_e_ram():
    if platform.system() == "Windows":
        cpu = saida_cmd(["powershell", "-NoProfile", "-Command",
                         "(Get-CimInstance Win32_Processor).Name"])

        class Mem(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = Mem()
        m.dwLength = ctypes.sizeof(Mem)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        ram = m.ullTotalPhys
        energia = saida_cmd(["powercfg", "/getactivescheme"])
    else:
        cpu = platform.processor() or saida_cmd(["sh", "-c", "grep -m1 'model name' /proc/cpuinfo"])
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        energia = "n/d"
    return cpu.strip(), ram / 2 ** 30, energia


def registrar_ambiente(pasta):
    cpu, ram, energia = cpu_e_ram()
    linhas = [
        f"CPU: {cpu}",
        f"RAM: {ram:.1f} GiB",
        f"Sistema operacional: {platform.platform()}",
        f"Plano de energia: {energia}",
        f"Python: {platform.python_implementation()} {platform.python_version()} (sem flags)",
        f"Java (execução): {saida_cmd(['java', '-version']).splitlines()[0]}",
        f"Java (compilador): {saida_cmd(['javac', '-version'])} (flags: nenhuma; JIT HotSpot padrão)",
    ]
    with open(os.path.join(pasta, "ambiente.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("\n".join(linhas))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rapido", action="store_true")
    a = p.parse_args()

    if a.rapido:
        res, gra = "saida_rapida/resultados", "saida_rapida/graficos"
        extra = ["--reps", "3", "--max-V", "100000", "--max-n", "64"]
        mem_extra = ["--max-V", "100000"]
    else:
        res, gra = "resultados", "graficos"
        extra = ["--reps", "20"]
        mem_extra = []
    os.makedirs(os.path.join(RAIZ, res), exist_ok=True)
    os.makedirs(os.path.join(RAIZ, gra), exist_ok=True)

    rodar([PY, "scripts/gerar_entradas.py"])
    rodar(["javac", "-d", "build"] + sorted(glob.glob(os.path.join("src", "java", "*.java"))))
    rodar([PY, "-m", "unittest", "discover", "-s", "testes", "-v"])
    registrar_ambiente(os.path.join(RAIZ, res))

    for exp in ("V", "n"):
        entrada = f"entradas/bench_{exp}.txt"
        rodar(["java", "-cp", "build", "Medir", "tempo", entrada, f"{res}/tempos_java_{exp}.csv"] + extra)
        rodar([PY, "src/python/medir.py", "tempo", entrada, f"{res}/tempos_python_{exp}.csv"] + extra)
    rodar(["java", "-cp", "build", "Medir", "memoria", "entradas/bench_V.txt", f"{res}/memoria_java.csv"] + mem_extra)
    rodar([PY, "src/python/medir.py", "memoria", "entradas/bench_V.txt", f"{res}/memoria_python.csv"] + mem_extra)

    rodar([PY, "scripts/analisar_sistemas.py", "--saida", f"{res}/sistemas_aleatorios.csv"])
    rodar([PY, "scripts/graficos.py", "--resultados", res, "--graficos", gra])
    if not a.rapido:
        rodar([PY, "-m", "unittest", "testes.test_troco.TestResultadosMedidos", "-v"])
    print(f"\nPronto. Resultados em {res}/ e gráficos em {gra}/")


if __name__ == "__main__":
    main()
