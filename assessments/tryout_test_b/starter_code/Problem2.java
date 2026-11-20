import java.util.Scanner;

public class Problem2 {
    public static boolean splling(String misspelling, String spelling) {
        // Your code here! Return true for Yes! or false for No!.
        return false;
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter first string (misspelling): ");
            System.err.flush();
            String misspelling = input.nextLine();
            System.err.print("Enter second string (correct spelling): ");
            System.err.flush();
            String spelling = input.nextLine();
            System.out.println(splling(misspelling, spelling) ? "Yes!" : "No!");
        }
    }
}
