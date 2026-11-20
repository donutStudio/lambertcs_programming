import java.util.Scanner;

public class SnackVote {
    public static String snackVote(String votes) {
        // Your code here!
        return "";
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter votes: ");
            System.err.flush();
            String votes = input.nextLine();
            System.out.println(snackVote(votes));
        }
    }
}
