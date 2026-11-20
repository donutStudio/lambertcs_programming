import java.util.Scanner;

public class ReadingGoal {
    public static int readingGoal(int goal, int[] pages) {
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
            System.err.print("Enter goal: ");
            System.err.flush();
            int goal = Integer.parseInt(input.nextLine().trim());
            System.err.print("Enter pages separated by spaces: ");
            System.err.flush();
            int[] pages = readNumbers(input);
            System.out.println(readingGoal(goal, pages));
        }
    }
}
