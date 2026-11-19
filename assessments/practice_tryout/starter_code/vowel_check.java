import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Main {
    public static int vowelCheck(String word) {
        // Your code here!
        return 0;
    }

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        System.err.print("Enter word: ");
        System.err.flush();
        String word = br.readLine();
        System.out.println(vowelCheck(word));
    }
}
