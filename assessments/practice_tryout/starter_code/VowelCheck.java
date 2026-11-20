import java.util.Scanner;

public class VowelCheck {
    public static int vowelCheck(String word) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter word: ");
            System.err.flush();
            String word = input.nextLine();
            System.out.println(vowelCheck(word));
        }
    }
}
