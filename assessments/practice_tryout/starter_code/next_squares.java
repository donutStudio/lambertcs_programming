import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static int nextSquares(int k, int n) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter k and n separated by a space: ");
        System.err.flush();
        String[] parts = br.readLine().trim().split("\\s+");
        int k = Integer.parseInt(parts[0]);
        int n = Integer.parseInt(parts[1]);
        System.out.println(nextSquares(k, n));
    }
}
