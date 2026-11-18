const config = JSON.parse(document.getElementById("assessment-config").textContent);
const assessment = config.assessment;
const storageKey = `attempt:${assessment.id}`;
const countKey = `attempt-count:${assessment.id}`;
const freshAttempt = new URLSearchParams(location.search).has("reattempt");
let state = JSON.parse(localStorage.getItem(storageKey) || "null");
if (!state || state.submitted || freshAttempt) {
    state = {answers: {}, startedAt: Date.now(), submitted: false, testResults: {}};
}
state.answers ||= {};
state.testResults ||= {};
state.startedAt ||= Date.now();
let activeQuestion = 0;
let editorInstances = [];
let submitting = false;

function save() { localStorage.setItem(storageKey, JSON.stringify(state)); }
function toast(message) {
    const box = document.getElementById("toast");
    box.textContent = message;
    box.classList.add("visible");
    setTimeout(() => box.classList.remove("visible"), 2500);
}
function allTests() {
    let passed = 0, total = 0;
    assessment.questions.forEach(question => {
        const results = state.testResults[question.id] || [];
        passed += results.filter(result => result.passed).length;
        total += results.length;
    });
    return {passed, total};
}
function formatScore() {
    const {passed, total} = allTests();
    const format = assessment.score_visibility.score_format || "fraction";
    if (format === "integer") return String(passed);
    if (format === "percent") return `${total ? Math.round(passed / total * 100) : 0}%`;
    return `${passed}/${total}`;
}
function updateScore() {
    const visible = !state.submitted && assessment.score_visibility.while_taking;
    const score = document.getElementById("score-display");
    score.hidden = !visible;
    score.textContent = visible ? `Score ${formatScore()}` : "";
}
function buildNavigation() {
    const nav = document.getElementById("question-nav");
    nav.replaceChildren();
    assessment.questions.forEach((question, index) => {
        const button = document.createElement("button");
        button.className = "question-nav-item";
        button.type = "button";
        button.textContent = String(index + 1);
        button.setAttribute("aria-label", `Question ${index + 1}`);
        button.addEventListener("click", () => showQuestion(index));
        nav.append(button);
    });
}
function buildQuestion(question, index) {
    const card = document.createElement("section");
    card.className = "question-card";
    const heading = document.createElement("div");
    heading.className = "question-heading";
    heading.innerHTML = `<span>Question ${index + 1}</span><h1></h1>`;
    heading.querySelector("h1").textContent = question.title;
    card.append(heading);
    const layout = document.createElement("div");
    layout.className = "question-layout";
    const hasStimulus = Boolean(question.stimulus && config.stimuliHtml[question.stimulus]);
    if (hasStimulus) {
        const stimulus = document.createElement("article");
        stimulus.className = "stimulus-pane";
        stimulus.innerHTML = config.stimuliHtml[question.stimulus];
        const handle = document.createElement("div");
        handle.className = "resize-handle";
        handle.setAttribute("role", "separator");
        handle.setAttribute("aria-label", "Resize problem and answer panes");
        const response = document.createElement("div");
        response.className = "response-pane";
        layout.append(stimulus, handle, response);
        setupSplitter(layout, handle);
        renderResponse(question, response);
    } else {
        const response = document.createElement("div");
        response.className = "response-pane response-full";
        layout.append(response);
        renderResponse(question, response);
    }
    card.append(layout);
    const footer = document.createElement("div");
    footer.className = "question-footer";
    const previous = document.createElement("button");
    previous.type = "button"; previous.textContent = "Previous"; previous.disabled = index === 0;
    previous.addEventListener("click", () => showQuestion(index - 1));
    const position = document.createElement("span"); position.textContent = `${index + 1} of ${assessment.questions.length}`;
    const next = document.createElement("button"); next.type = "button";
    next.textContent = index === assessment.questions.length - 1 ? "Finish" : "Next";
    next.addEventListener("click", () => index < assessment.questions.length - 1 ? showQuestion(index + 1) : document.getElementById("submit-assessment").click());
    footer.append(previous, position, next); card.append(footer);
    return card;
}
function setupSplitter(layout, handle) {
    handle.addEventListener("pointerdown", event => {
        event.preventDefault(); handle.setPointerCapture(event.pointerId);
        const move = moveEvent => {
            const rect = layout.getBoundingClientRect();
            const ratio = Math.max(.25, Math.min(.68, (moveEvent.clientX - rect.left) / rect.width));
            layout.style.gridTemplateColumns = `minmax(0, ${ratio}fr) 8px minmax(0, ${1 - ratio}fr)`;
        };
        const stop = () => { handle.removeEventListener("pointermove", move); handle.removeEventListener("pointerup", stop); };
        handle.addEventListener("pointermove", move); handle.addEventListener("pointerup", stop);
    });
}
function renderResponse(question, host) {
    if (question.response_type === "short_answer") return renderShortAnswer(question, host);
    if (question.response_type === "code_editor") return renderCodeEditor(question, host);
    host.textContent = `Unsupported response type: ${question.response_type}`;
}
function renderShortAnswer(question, host) {
    const fields = question.response_config.fields || [];
    fields.forEach((field, index) => {
        const id = `${question.id}:${field.id || index}`;
        const wrap = document.createElement("label");
        wrap.className = "short-answer-field";
        const title = document.createElement("div"); title.className = "field-prompt"; title.innerHTML = field.question_html || "";
        const input = document.createElement("input"); input.type = field.email ? "email" : "text";
        input.maxLength = field.character_limit || 100; input.value = state.answers[id] || "";
        if (field.numeric_only) { input.inputMode = "numeric"; input.pattern = "[0-9]*"; }
        input.addEventListener("input", () => {
            if (field.numeric_only) input.value = input.value.replace(/[^0-9]/g, "");
            state.answers[id] = input.value; save();
        });
        wrap.append(title, input);
        if (field.numeric_only && field.allowed_range) {
            const hint = document.createElement("small"); hint.textContent = `Allowed: ${field.allowed_range[0]}–${field.allowed_range[1]}`; wrap.append(hint);
        }
        if (field.email) input.addEventListener("change", () => { if (input.value && !input.validity.valid) input.reportValidity(); });
        host.append(wrap);
    });
}
function renderCodeEditor(question, host) {
    const c = question.response_config;
    const workbench = document.createElement("div"); workbench.className = "code-workbench";
    const explorer = document.createElement("aside"); explorer.className = "file-explorer";
    const explorerTitle = document.createElement("div"); explorerTitle.className = "explorer-title"; explorerTitle.textContent = "EXPLORER";
    const folder = document.createElement("div"); folder.className = "folder-title"; folder.textContent = "⌄  PROGRAM";
    const files = c.files.length ? c.files : [`main.${c.supported_languages[0] === "python" ? "py" : c.supported_languages[0]}`];
    const fileList = document.createElement("div"); fileList.className = "file-list";
    files.forEach(file => { const row = document.createElement("button"); row.type = "button"; row.className = "file-row selected"; row.textContent = `▧  ${file}`; fileList.append(row); });
    explorer.append(explorerTitle, folder, fileList);
    const workspace = document.createElement("div"); workspace.className = "editor-workspace";
    const toolbar = document.createElement("div"); toolbar.className = "editor-toolbar";
    const fileTab = document.createElement("span"); fileTab.className = "editor-tab"; fileTab.textContent = files[0];
    const select = document.createElement("select"); select.setAttribute("aria-label", "Programming language");
    c.supported_languages.forEach(language => { if (config.languages[language]) select.add(new Option(config.languages[language].label, language)); });
    const actions = document.createElement("div"); actions.className = "editor-actions";
    const run = document.createElement("button"); run.type = "button"; run.className = "run-button"; run.textContent = "Run";
    const tests = document.createElement("button"); tests.type = "button"; tests.className = "tests-button"; tests.textContent = "Run tests";
    const reset = document.createElement("button"); reset.type = "button"; reset.className = "quiet-button"; reset.textContent = "Reset";
    if (!c.runnable) run.hidden = true;
    if (!c.runnable_tests) tests.hidden = true;
    if (c.read_only) reset.hidden = true;
    actions.append(run, tests, reset, select); toolbar.append(fileTab, actions);
    const editorEl = document.createElement("div"); editorEl.className = "monaco-question-editor";
    workspace.append(toolbar, editorEl);
    if (c.output) {
        const outputPanel = document.createElement("section"); outputPanel.className = "output-panel";
        const outputHeader = document.createElement("div"); outputHeader.className = "output-header"; outputHeader.textContent = "OUTPUT";
        const stdin = document.createElement("textarea"); stdin.className = "stdin"; stdin.placeholder = "Program input (stdin)";
        stdin.hidden = !c.allow_input;
        const output = document.createElement("pre"); output.className = "output"; output.textContent = "Run your program or tests to see output.";
        outputPanel.append(outputHeader, stdin, output); workspace.append(outputPanel);
        run.addEventListener("click", async () => {
            run.disabled = true; output.textContent = "Running…";
            try {
                const response = await fetch(config.runUrl, {method: "POST", headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({language: select.value, code: getCode(), input: stdin.value})});
                const data = await response.json(); output.textContent = data.output || data.error || "Done.";
            } catch (error) { output.textContent = `Request failed: ${error.message}`; }
            finally { run.disabled = false; }
        });
        tests.addEventListener("click", async () => {
            tests.disabled = true; output.textContent = "Running tests…";
            try {
                const response = await fetch(config.testsUrl, {method: "POST", headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({question_id: question.id, language: select.value, code: getCode()})});
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || "Tests failed to run.");
                state.testResults[question.id] = data.tests; save(); updateScore();
                output.textContent = data.tests.map(test => `${test.passed ? "✓" : "✗"} ${test.name}: ${test.output}`).join("\n") || "No tests configured.";
            } catch (error) { output.textContent = `Could not run tests: ${error.message}`; }
            finally { tests.disabled = false; }
        });
        editorEl._output = output;
    }
    host.append(workbench);
    if (c.file_browser === false) explorer.hidden = true;
    workbench.append(explorer, workspace);
    let editor = null;
    function getCode() { return editor ? editor.getValue() : ""; }
    function languageChanged() {
        if (!editor) return;
        const current = editor.getModel().getLanguageId();
        state.answers[question.id] ||= {};
        state.answers[question.id][current] = editor.getValue();
        const model = monaco.editor.createModel(state.answers[question.id][select.value] ?? c.default_code[select.value] ?? "", select.value);
        editor.setModel(model); fileTab.textContent = files.find(file => file.endsWith(select.value === "python" ? ".py" : select.value === "java" ? ".java" : ".cpp")) || files[0];
        save();
    }
    select.addEventListener("change", languageChanged);
    reset.addEventListener("click", () => { if (editor) editor.setValue(c.default_code[select.value] || ""); });
    const initialize = () => {
        if (!window.require || !select.value) { editorEl.textContent = "Code editor could not load. Check your internet connection and refresh."; return; }
        window.require.config({paths: {vs: config.monacoBase + "vs"}});
        window.require(["vs/editor/editor.main"], () => {
            const language = select.value;
            const draft = (state.answers[question.id] || {})[language] ?? c.default_code[language] ?? "";
            editor = monaco.editor.create(editorEl, {value: draft, language, theme: "vs-dark", automaticLayout: true,
                fontSize: 14, minimap: {enabled: false}, wordWrap: "on", scrollBeyondLastLine: false,
                automaticClosingBrackets: "always", autoIndent: "full", quickSuggestions: c.intellisense,
                suggestOnTriggerCharacters: c.intellisense, tabCompletion: c.intellisense ? "on" : "off",
                readOnly: Boolean(c.read_only)});
            editor.onDidChangeModelContent(() => {
                state.answers[question.id] ||= {}; state.answers[question.id][select.value] = editor.getValue(); save();
            });
            editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => c.runnable_tests ? tests.click() : run.click());
            editorInstances.push(editor);
        });
    };
    initialize();
}
function showQuestion(index) {
    if (index < 0 || index >= assessment.questions.length) return;
    activeQuestion = index;
    editorInstances.forEach(editor => editor.dispose()); editorInstances = [];
    const host = document.getElementById("question-host"); host.replaceChildren(buildQuestion(assessment.questions[index], index));
    document.querySelectorAll(".question-nav-item").forEach((button, i) => button.classList.toggle("active", i === index));
    document.querySelectorAll(".question-nav-item")[index]?.scrollIntoView({block: "nearest", inline: "nearest"});
}
async function submitAssessment(automatic = false) {
    if (state.submitted || submitting) return;
    if (!automatic && !window.confirm("Submit this assessment? You cannot change your answers after submitting.")) return;
    submitting = true;
    state.submitted = true; state.submittedAt = Date.now(); state.scoreText = formatScore(); save();
    try {
        await fetch(config.submitUrl, {method: "POST", headers: {"Content-Type": "application/json"}, keepalive: true,
            body: JSON.stringify({answers: state.answers, score: {display: state.scoreText, tests: state.testResults}})});
    } catch (_) { /* The browser still retains the completed attempt locally. */ }
    document.getElementById("submit-assessment").disabled = true;
    document.getElementById("complete-title").textContent = automatic ? "Time is up" : "Assessment submitted";
    document.getElementById("complete-message").textContent = assessment.score_visibility.upon_completion ? `Your score: ${state.scoreText}` : "Your work has been saved.";
    document.getElementById("complete-dialog").hidden = false;
    updateScore();
}
function updateTimer() {
    if (!assessment.time_limit_seconds) return;
    const remaining = Math.max(0, assessment.time_limit_seconds - Math.floor((Date.now() - state.startedAt) / 1000));
    const minutes = Math.floor(remaining / 60), seconds = remaining % 60;
    document.getElementById("timer").textContent = `${minutes}:${String(seconds).padStart(2, "0")} remaining`;
    if (remaining === 0 && !state.submitted) submitAssessment(true);
}

document.getElementById("submit-assessment").hidden = !assessment.submittable_early;
document.getElementById("submit-assessment").addEventListener("click", () => submitAssessment(false));
document.getElementById("complete-home").addEventListener("click", () => { location.href = "/"; });
document.getElementById("exit-assessment").addEventListener("click", event => {
    if (state.submitted) return;
    if (assessment.auto_submit_on_leave) {
        if (!window.confirm("Leaving will submit this assessment automatically. Continue?")) event.preventDefault();
        else submitAssessment(true);
    } else if (!window.confirm("Leave this assessment? Your progress has been saved and you can resume later.")) event.preventDefault();
});
window.addEventListener("beforeunload", event => {
    if (!state.submitted && assessment.auto_submit_on_leave) {
        state.submitted = true; state.submittedAt = Date.now(); state.scoreText = formatScore(); save();
        fetch(config.submitUrl, {method: "POST", headers: {"Content-Type": "application/json"}, keepalive: true,
            body: JSON.stringify({answers: state.answers, score: {display: state.scoreText, tests: state.testResults}})});
    }
});
document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !state.submitted) document.getElementById("exit-assessment").click();
    if (event.altKey && event.key === "ArrowRight") showQuestion(activeQuestion + 1);
    if (event.altKey && event.key === "ArrowLeft") showQuestion(activeQuestion - 1);
});
buildNavigation(); showQuestion(0); save(); updateScore(); updateTimer(); setInterval(updateTimer, 1000);
