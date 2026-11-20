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
        return "guloso".equals(algoritmo) ? guloso(moedas, V) : pd(moedas, V);
    }
}
