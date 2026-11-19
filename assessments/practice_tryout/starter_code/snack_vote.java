import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static String snackVote(String votes) {
        // Your code here!
        return "";
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter votes: ");
        System.err.flush();
        String votes = br.readLine();
        System.out.println(snackVote(votes));
    }
}
