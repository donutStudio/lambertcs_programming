import java.util.Scanner;

public class Main {
    public static boolean splling(String misspelling, String spelling) {
        for (int i = -1; i < misspelling.length(); i++) {
            String word;
            if (i == -1) {
                word = "e" + misspelling;
            } else {
                word = misspelling.substring(0, i + 1) + "e";
                if (i < misspelling.length() - 2) {
                    word += misspelling.substring(i + 3);
                } else if (i < misspelling.length() - 1) {
                    word += misspelling.substring(i + 2);
                }
            }
            System.out.println(word);
        }
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
        System.out.println(splling(misspelling, spelling) ? "Yes!" : "No!");
        sc.close();
    }
}