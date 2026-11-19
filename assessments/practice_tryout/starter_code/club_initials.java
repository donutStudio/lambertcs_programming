import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static String clubInitials(String name) {
        // Your code here!
        return "";
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter name: ");
        System.err.flush();
        String name = br.readLine();
        System.out.println(clubInitials(name));
    }
}
