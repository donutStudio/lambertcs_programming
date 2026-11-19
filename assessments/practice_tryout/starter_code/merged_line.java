import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static String mergedLine(int[] first, int[] second) {
        // Your code here!
        return "";
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter first separated by spaces: ");
        System.err.flush();
        int[] first = Arrays.stream(br.readLine().trim().split("\\s+")).mapToInt(Integer::parseInt).toArray();
        System.err.print("Enter second separated by spaces: ");
        System.err.flush();
        int[] second = Arrays.stream(br.readLine().trim().split("\\s+")).mapToInt(Integer::parseInt).toArray();
        System.out.println(mergedLine(first, second));
    }
}
