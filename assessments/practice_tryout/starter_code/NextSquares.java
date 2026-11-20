import java.util.Scanner;

public class NextSquares {
    public static int nextSquares(int k, int n) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter k and n separated by a space: ");
            System.err.flush();
            int k = input.nextInt();
            int n = input.nextInt();
            System.out.println(nextSquares(k, n));
        }
    }
}
