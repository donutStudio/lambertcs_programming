
const MONACO_BASE =
    "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/";

const languageSelect = document.getElementById("language");
const runButton = document.getElementById("run-button");
const output = document.getElementById("output");

const defaultCode = {
    python: 
`print("Hello, world!")`,

    java:
`public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, world!");
    }
}`,

    cpp:
`#include <iostream>
int main() {
    std::cout << "Hello, world!" << std::endl;
    return 0;
}`
};

// stores language saved code
const savedCode = { ...defaultCode };

const monacoLanguages = {
    python: "python",
    java: "java",
    cpp: "cpp"
};

window.MonacoEnvironment = {
    getWorkerUrl: function () {
        const workerCode = `
            self.MonacoEnvironment = {
                baseUrl: "${MONACO_BASE}"
            };
            importScripts(
                "${MONACO_BASE}vs/base/worker/workerMain.js"
            );
        `;

        return URL.createObjectURL(
            new Blob([workerCode], {
                type: "text/javascript"
            })
        );
    }
};

require.config({
    paths: {
        vs: MONACO_BASE + "vs"
    }
});

require(["vs/editor/editor.main"], function () {

    const editor = monaco.editor.create(
        document.getElementById("editor"),
        {
            value: savedCode.python,
            language: "python",

            theme: "vs-dark",
            automaticLayout: true,

            fontSize: 14,
            minimap: { enabled: false },

            wordWrap: "on",
            scrollBeyondLastLine: false,

            automaticClosingBrackets: "always",
            autoIndent: "full",

            quickSuggestions: true,
            suggestOnTriggerCharacters: true,
            tabCompletion: "on"
        }
    );

    document.getElementById("reset-button").addEventListener("click", function () {
        const language = languageSelect.value;
        const code = defaultCode[language];
        editor.setValue(code);
        savedCode[language] = code;
    });

    // no full language server so just like hardcoded suggestions and shit
    const suggestions = {
        python: [
            "print", "len", "range", "enumerate",
            "list", "dict", "set", "sum",
            "math", "random", "collections",
            "itertools", "heapq", "bisect"
        ],

        java: [
            "System.out.println", "System.out.print",
            "String", "Math", "Arrays",
            "ArrayList", "HashMap", "HashSet",
            "Scanner", "Collections", "PriorityQueue"
        ],

        cpp: [
            "cout", "cin", "vector", "string",
            "map", "unordered_map", "set",
            "sort", "priority_queue", "queue",
            "stack", "algorithm"
        ]
    };

    for (const [language, words] of Object.entries(suggestions)) {
        monaco.languages.registerCompletionItemProvider(language, {
            provideCompletionItems: function (model, position) {
                const word = model.getWordUntilPosition(position);

                const range = {
                    startLineNumber: position.lineNumber,
                    endLineNumber: position.lineNumber,
                    startColumn: word.startColumn,
                    endColumn: word.endColumn
                };

                return {
                    suggestions: words.map((name) => ({
                        label: name,
                        kind: monaco.languages.CompletionItemKind.Text,
                        insertText: name,
                        range: range
                    }))
                };
            }
        });
    }

    // change language button and saving code per language
    languageSelect.addEventListener("change", function () {
        const language = languageSelect.value;

        monaco.editor.setModelLanguage(
            editor.getModel(),
            monacoLanguages[language]
        );

        editor.setValue(savedCode[language]);
    });

    editor.onDidChangeModelContent(function () {
        const language = languageSelect.value;
        savedCode[language] = editor.getValue();
    });

    async function runCode() {
        const language = languageSelect.value;
        const code = editor.getValue();

        runButton.disabled = true;
        runButton.textContent = "Running...";
        output.textContent = "Running code...";

        try {
            const response = await fetch("/run", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    language: language,
                    code: code
                })
            });

            const data = await response.json();

            output.textContent = data.output ?? "Program finished!";

        } catch (error) {
            output.textContent = error.message;
        } finally {
            runButton.disabled = false;
            runButton.textContent = "Run";
        }
    }

    runButton.addEventListener("click", runCode);

    // add a keybind to run code
    editor.addCommand(
        monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
        runCode
    );

});
