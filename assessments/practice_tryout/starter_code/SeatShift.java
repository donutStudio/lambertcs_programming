import java.util.Scanner;

public class SeatShift {
    public static String seatShift(int shift, int[] seats) {
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
            System.err.print("Enter shift: ");
            System.err.flush();
            int shift = Integer.parseInt(input.nextLine().trim());
            System.err.print("Enter seats separated by spaces: ");
            System.err.flush();
            int[] seats = readNumbers(input);
            System.out.println(seatShift(shift, seats));
        }
    }
}
