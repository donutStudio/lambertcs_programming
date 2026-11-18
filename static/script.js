// Python supplies language data and routes; JavaScript connects the browser editor.
const config = JSON.parse(document.getElementById("editor-config").textContent);
const MONACO_BASE = config.monacoBase;
const languageSelect = document.getElementById("language");
const runButton = document.getElementById("run-button");
const output = document.getElementById("output");
const savedCode = Object.fromEntries(
    Object.entries(config.languages).map(([key, language]) => [key, language.default_code])
);

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
            value: savedCode[config.initialLanguage],
            language: config.initialLanguage,

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

    runButton.disabled = false;
    document.getElementById("reset-button").disabled = false;

    document.getElementById("reset-button").addEventListener("click", function () {
        const language = languageSelect.value;
        const code = config.languages[language].default_code;
        editor.setValue(code);
        savedCode[language] = code;
    });

    for (const [language, settings] of Object.entries(config.languages)) {
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
                    suggestions: settings.suggestions.map((name) => ({
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
            language
        );

        editor.setValue(savedCode[language]);
    });

    editor.onDidChangeModelContent(function () {
        const language = languageSelect.value;
        savedCode[language] = editor.getValue();
    });

    async function runCode() {
        if (runButton.disabled) return;
        const language = languageSelect.value;
        const code = editor.getValue();

        runButton.disabled = true;
        runButton.textContent = "Running...";
        output.textContent = "Running code...";

        try {
            const response = await fetch(config.runUrl, {
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
