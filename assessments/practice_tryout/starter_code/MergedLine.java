import java.util.Scanner;

public class MergedLine {
    public static String mergedLine(int[] first, int[] second) {
        // Your code here!
        return "";
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
            System.err.print("Enter first separated by spaces: ");
            System.err.flush();
            int[] first = readNumbers(input);
            System.err.print("Enter second separated by spaces: ");
            System.err.flush();
            int[] second = readNumbers(input);
            System.out.println(mergedLine(first, second));
        }
    }
}
