import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static int academicComeback(int[] grades) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter grades separated by spaces: ");
        System.err.flush();
        String[] parts = br.readLine().trim().split("\s+");
        int[] grades = new int[parts.length];
        for (int i = 0; i < parts.length; i++) {
            grades[i] = Integer.parseInt(parts[i]);
        }
        System.out.println(academicComeback(grades));
    }
}