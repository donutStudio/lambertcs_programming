import java.util.Scanner;

public class Problem1 {
    public static long oddOnesOut(int n) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter a number: ");
            System.err.flush();
            System.out.println(oddOnesOut(Integer.parseInt(input.nextLine().trim())));
        }
    }
}