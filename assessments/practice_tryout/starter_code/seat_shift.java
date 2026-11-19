import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static String seatShift(int shift, int[] seats) {
        // Your code here!
        return "";
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter shift: ");
        System.err.flush();
        int shift = Integer.parseInt(br.readLine().trim());
        System.err.print("Enter seats separated by spaces: ");
        System.err.flush();
        int[] seats = Arrays.stream(br.readLine().trim().split("\\s+")).mapToInt(Integer::parseInt).toArray();
        System.out.println(seatShift(shift, seats));
    }
}
