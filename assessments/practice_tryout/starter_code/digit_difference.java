import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static int digitDifference(int n) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter n: ");
        System.err.flush();
        int n = Integer.parseInt(br.readLine().trim());
        System.out.println(digitDifference(n));
    }
}
