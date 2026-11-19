import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static boolean candleSplit(int n) {
        // Your code here! Return true for YES or false for NO.
        return false;
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter n: ");
        System.err.flush();
        int n = Integer.parseInt(br.readLine().trim());
        System.out.println(candleSplit(n) ? "YES" : "NO");
    }
}
