import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Medição das implementações em Java.
 *
 * Modos:
 *   tempo     <instancias> <saida.csv> [--reps R] [--max-V X] [--max-n Y]
 *   memoria   <instancias> <saida.csv> [--max-V X] [--max-n Y]
 *   respostas <instancias> <saida.csv>
 *
 * Só a chamada do algoritmo é cronometrada (leitura e escrita ficam fora).
 */
public final class Medir {

    static final long LOTE_MIN_NS = 10_000_000L; // lote de pelo menos 10 ms
    static final int LOTE_MAX = 1 << 26;
    static final int AQUECIMENTO = 5;            // lotes descartados (JIT)
    static final String[] ALGORITMOS = {"guloso", "pd"};

    static volatile long sink; // impede o JIT de descartar as chamadas

    record Instancia(String id, String experimento, String caso, int V, int n, int[] moedas) {}

    static List<Instancia> ler(String caminho, long maxV, long maxN) throws IOException {
        List<Instancia> lista = new ArrayList<>();
        try (BufferedReader br = Files.newBufferedReader(Paths.get(caminho), StandardCharsets.UTF_8)) {
            String linha;
            while ((linha = br.readLine()) != null) {
                linha = linha.trim();
                if (linha.isEmpty() || linha.startsWith("#")) {
                    continue;
                }
                String[] p = linha.split("\\s+");
                int V = Integer.parseInt(p[3]);
                int n = Integer.parseInt(p[4]);
                if (V > maxV || n > maxN) {
                    continue;
                }
                int[] moedas = new int[n];
                for (int i = 0; i < n; i++) {
                    moedas[i] = Integer.parseInt(p[5 + i]);
                }
                lista.add(new Instancia(p[0], p[1], p[2], V, n, moedas));
            }
        }
        return lista;
    }

    static long medirLote(String alg, int[] moedas, int V, int chamadas) {
        long acc = 0;
        long inicio;
        long fim;
        if ("guloso".equals(alg)) {
            inicio = System.nanoTime();
            for (int i = 0; i < chamadas; i++) {
                acc += Troco.guloso(moedas, V);
            }
            fim = System.nanoTime();
        } else {
            inicio = System.nanoTime();
            for (int i = 0; i < chamadas; i++) {
                acc += Troco.pd(moedas, V);
            }
            fim = System.nanoTime();
        }
        sink += acc;
        return fim - inicio;
    }

    static int calibrar(String alg, int[] moedas, int V) {
        int chamadas = 1;
        while (true) {
            long t = medirLote(alg, moedas, V, chamadas);
            if (t >= LOTE_MIN_NS || chamadas >= LOTE_MAX) {
                return chamadas;
            }
            chamadas *= 2;
        }
    }

    static void modoTempo(List<Instancia> lista, String saida, int reps) throws IOException {
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(Paths.get(saida), StandardCharsets.UTF_8))) {
            w.println("linguagem,algoritmo,experimento,caso,id,n,V,lote,rep,ns_por_chamada,resposta");
            for (Instancia in : lista) {
                for (String alg : ALGORITMOS) {
                    int resposta = Troco.executar(alg, in.moedas(), in.V());
                    int lote = calibrar(alg, in.moedas(), in.V());
                    for (int k = 0; k < AQUECIMENTO; k++) {
                        medirLote(alg, in.moedas(), in.V(), lote);
                    }
                    double soma = 0;
                    double[] tempos = new double[reps];
                    for (int r = 0; r < reps; r++) {
                        tempos[r] = (double) medirLote(alg, in.moedas(), in.V(), lote) / lote;
                        soma += tempos[r];
                    }
                    for (int r = 0; r < reps; r++) {
                        w.printf(Locale.ROOT, "java,%s,%s,%s,%s,%d,%d,%d,%d,%.1f,%d%n",
                                alg, in.experimento(), in.caso(), in.id(), in.n(), in.V(),
                                lote, r, tempos[r], resposta);
                    }
                    w.flush();
                    System.out.printf(Locale.ROOT, "java   %-6s %-14s lote=%-7d media=%.4f ms%n",
                            alg, in.id(), lote, soma / reps / 1e6);
                }
            }
        }
    }

    static void modoMemoria(List<Instancia> lista, String saida) throws IOException {
        com.sun.management.ThreadMXBean bean =
                (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();
        long tid = Thread.currentThread().threadId();
        sink += Troco.guloso(new int[] {1}, 1) + Troco.pd(new int[] {1}, 1); // carrega as classes antes de medir
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(Paths.get(saida), StandardCharsets.UTF_8))) {
            w.println("linguagem,algoritmo,experimento,caso,id,n,V,bytes_pico");
            for (Instancia in : lista) {
                for (String alg : ALGORITMOS) {
                    long antes = bean.getThreadAllocatedBytes(tid);
                    sink += Troco.executar(alg, in.moedas(), in.V());
                    long depois = bean.getThreadAllocatedBytes(tid);
                    w.printf(Locale.ROOT, "java,%s,%s,%s,%s,%d,%d,%d%n",
                            alg, in.experimento(), in.caso(), in.id(), in.n(), in.V(), depois - antes);
                    System.out.printf(Locale.ROOT, "java   memoria %-6s %-14s %d B%n",
                            alg, in.id(), depois - antes);
                }
            }
        }
    }

    static void modoRespostas(List<Instancia> lista, String saida) throws IOException {
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(Paths.get(saida), StandardCharsets.UTF_8))) {
            w.println("id,algoritmo,resposta");
            for (Instancia in : lista) {
                for (String alg : ALGORITMOS) {
                    w.printf(Locale.ROOT, "%s,%s,%d%n", in.id(), alg, Troco.executar(alg, in.moedas(), in.V()));
                }
            }
        }
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 3) {
            System.err.println("uso: java Medir <tempo|memoria|respostas> <instancias> <saida.csv> [--reps R] [--max-V X] [--max-n Y]");
            System.exit(2);
        }
        int reps = 20;
        long maxV = Long.MAX_VALUE;
        long maxN = Long.MAX_VALUE;
        for (int i = 3; i + 1 < args.length; i += 2) {
            switch (args[i]) {
                case "--reps" -> reps = Integer.parseInt(args[i + 1]);
                case "--max-V" -> maxV = Long.parseLong(args[i + 1]);
                case "--max-n" -> maxN = Long.parseLong(args[i + 1]);
                default -> throw new IllegalArgumentException("opção desconhecida: " + args[i]);
            }
        }
        List<Instancia> lista = ler(args[1], maxV, maxN);
        switch (args[0]) {
            case "tempo" -> modoTempo(lista, args[2], reps);
            case "memoria" -> modoMemoria(lista, args[2]);
            case "respostas" -> modoRespostas(lista, args[2]);
            default -> throw new IllegalArgumentException("modo desconhecido: " + args[0]);
        }
    }
}
