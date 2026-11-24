/**
 * Troco de moedas: menor número de moedas para pagar o valor V.
 * As moedas têm quantidade ilimitada. Resposta -1 significa impossível.
 */
public final class Troco {

    private Troco() {}

    /**
     * Algoritmo A (guloso).
     * Pré-condição: moedas distintas e positivas em ordem DECRESCENTE.
     */
    public static int guloso(int[] moedasDesc, int V) {
        int resto = V;
        int total = 0;
        for (int c : moedasDesc) {
            if (c <= resto) {
                int q = resto / c;
                total += q;
                resto -= q * c;
                if (resto == 0) {
                    return total;
                }
            }
        }
        return resto == 0 ? total : -1;
    }

    /**
     * Algoritmo B (programação dinâmica).
     * dp[v] = menor número de moedas para pagar v.
     */
    public static int pd(int[] moedas, int V) {
        // Reserva margem para o sentinela e para dp[v - c] + 1.
        // A alocação da tabela também depende da memória disponível.
        if (V < 0 || V > Integer.MAX_VALUE - 2) {
            throw new IllegalArgumentException("V fora do intervalo suportado pela PD");
        }
        int infinito = V + 1;
        int[] dp = new int[V + 1];
        java.util.Arrays.fill(dp, infinito);
        dp[0] = 0;
        for (int c : moedas) {
            for (int v = c; v <= V; v++) {
                int x = dp[v - c] + 1;
                if (x < dp[v]) {
                    dp[v] = x;
                }
            }
        }
        return dp[V] <= V ? dp[V] : -1;
    }

    public static int executar(String algoritmo, int[] moedas, int V) {
        return switch (algoritmo) {
            case "guloso" -> guloso(moedas, V);
            case "pd" -> pd(moedas, V);
            default -> throw new IllegalArgumentException("algoritmo desconhecido: " + algoritmo);
        };
    }
}
