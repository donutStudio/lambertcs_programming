import java.util.Scanner;

public class ClubInitials {
    public static String clubInitials(String name) {
        // Your code here!
        return "";
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter name: ");
            System.err.flush();
            String name = input.nextLine();
            System.out.println(clubInitials(name));
        }
    }
}
