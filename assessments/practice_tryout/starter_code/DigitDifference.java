import java.util.Scanner;

public class DigitDifference {
    public static int digitDifference(int n) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter n: ");
            System.err.flush();
            int n = Integer.parseInt(input.nextLine().trim());
            System.out.println(digitDifference(n));
        }
    }
}
