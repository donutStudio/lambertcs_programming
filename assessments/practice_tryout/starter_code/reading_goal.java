import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static int readingGoal(int goal, int[] pages) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter goal: ");
        System.err.flush();
        int goal = Integer.parseInt(br.readLine().trim());
        System.err.print("Enter pages separated by spaces: ");
        System.err.flush();
        int[] pages = Arrays.stream(br.readLine().trim().split("\\s+")).mapToInt(Integer::parseInt).toArray();
        System.out.println(readingGoal(goal, pages));
    }
}
