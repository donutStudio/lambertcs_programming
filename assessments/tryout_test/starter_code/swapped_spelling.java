import java.util.Scanner;

public class Main {
    public static boolean swappedSpelling(String misspelling, String spelling) {
        // Your code here! Return true for Yes! or false for No!.
        return false;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.err.print("Enter first string (misspelling): ");
        System.err.flush();
        String misspelling = sc.nextLine();
        System.err.print("Enter second string (correct spelling): ");
        System.err.flush();
        String spelling = sc.nextLine();
        System.out.println(swappedSpelling(misspelling, spelling) ? "Yes!" : "No!");
    }
}
