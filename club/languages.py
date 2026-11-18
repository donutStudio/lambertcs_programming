"""Language options, starter programs, and editor completions."""
LANGUAGES = {
    "python": {
        "label": "Python",
        "default_code": 'print("Hello, world!")',
        "suggestions": [
            "print", "len", "range", "enumerate", "list", "dict", "set", "sum",
            "math", "random", "collections", "itertools", "heapq", "bisect",
        ],
    },
    "java": {
        "label": "Java",
        "default_code": '''public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, world!");
    }
}''',
        "suggestions": [
            "System.out.println", "System.out.print", "String", "Math", "Arrays",
            "ArrayList", "HashMap", "HashSet", "Scanner", "Collections", "PriorityQueue",
        ],
    },
    "cpp": {
        "label": "C++",
        "default_code": '''#include <iostream>
int main() {
    std::cout << "Hello, world!" << std::endl;
    return 0;
}''',
        "suggestions": [
            "cout", "cin", "vector", "string", "map", "unordered_map", "set",
            "sort", "priority_queue", "queue", "stack", "algorithm",
        ],
    },
}
