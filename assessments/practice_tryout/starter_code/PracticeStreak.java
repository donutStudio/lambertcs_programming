import java.util.Scanner;

public class PracticeStreak {
    public static int practiceStreak(int[] days) {
        // Your code here!
        return 0;
    }

    // Read one line of space-separated integers.
    private static int[] readNumbers(Scanner input) {
        String line = input.nextLine().trim();
        if (line.isEmpty()) {
            return new int[0];
        }
        String[] values = line.split("\\s+");
        int[] numbers = new int[values.length];
        for (int i = 0; i < values.length; i++) {
            numbers[i] = Integer.parseInt(values[i]);
        }
        return numbers;
    }

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            System.err.print("Enter days separated by spaces: ");
            System.err.flush();
            int[] days = readNumbers(input);
            System.out.println(practiceStreak(days));
        }
    }
}
