import java.util.Scanner;

public class CandleSplit {
    public static boolean candleSplit(int n) {
        // Your code here! Return true for YES or false for NO.
        return false;
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter n: ");
            System.err.flush();
            int n = Integer.parseInt(input.nextLine().trim());
            System.out.println(candleSplit(n) ? "YES" : "NO");
        }
    }
}
