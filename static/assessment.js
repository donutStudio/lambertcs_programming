const config = JSON.parse(document.getElementById("assessment-config").textContent);
const assessment = config.assessment;
let state = {answers: {}, score: {}};
let activeQuestion = 0, submitting = false, saveTimer, saveChain = Promise.resolve(), clockOffset = 0;
let editorInstances = [], cleanups = [];
const saveStatus = document.getElementById("save-status");
const questionSelect = document.getElementById("question-select");
window.MonacoEnvironment = {getWorkerUrl() {
    return URL.createObjectURL(new Blob([`self.MonacoEnvironment={baseUrl:${JSON.stringify(config.monacoBase)}};importScripts(${JSON.stringify(config.monacoBase + "vs/base/worker/workerMain.js")});`], {type: "text/javascript"}));
}};
let completionsRegistered = false;

async function api(url, body, options = {}) {
    const response = await fetch(url, body === undefined ? options : {...options, method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || data.output || `Request failed (${response.status})`);
    return data;
}
function acceptClock(data) { clockOffset = data.server_time * 1000 - Date.now(); }
function save() {
    if (config.standalone || state.submitted) return;
    saveStatus.textContent = "Saving…";
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => persist().catch(() => {}), 450);
}
function persist(extra = {}) {
    clearTimeout(saveTimer);
    if (config.standalone) return Promise.resolve();
    const answers = structuredClone(state.answers);
    saveChain = saveChain.catch(() => {}).then(async () => {
        try {
            const data = await api(`/api/attempt/${state.id}`, {answers, ...extra});
            acceptClock(data);
            if (JSON.stringify(answers) === JSON.stringify(state.answers)) state.score = data.attempt.score;
            state.reason = data.attempt.reason;
            if (data.attempt.submitted) { state.submitted = data.attempt.submitted; finish(); }
            saveStatus.textContent = "Saved";
            updateScore();
            return data;
        } catch (error) {
            saveStatus.textContent = "Save failed — retrying";
            throw error;
        }
    });
    return saveChain;
}
function formatScore() {
    let passed = 0, total = 0;
    assessment.questions.forEach(q => {
        total += q.response_config?.test_count || 0;
        passed += state.score[q.id]?.passed || 0;
    });
    const format = assessment.score_visibility.score_format;
    return format === "percent" ? `${total ? Math.round(passed / total * 100) : 0}%` : format === "integer" ? String(passed) : `${passed}/${total}`;
}
function updateScore() {
    const score = document.getElementById("score-display");
    score.hidden = !assessment.score_visibility.while_taking || Boolean(state.submitted);
    score.textContent = `Tests ${formatScore()}`;
    score.title = "Results for the current code from tests run on the server";
}
function buildNavigation() {
    assessment.questions.forEach((q, i) => questionSelect.add(new Option(`Question ${i + 1}/${assessment.questions.length}`, i)));
    questionSelect.addEventListener("change", () => showQuestion(Number(questionSelect.value)));
}
function splitter(handle, getValue, apply, orientation = "vertical") {
    handle.tabIndex = 0;
    handle.setAttribute("role", "separator");
    handle.setAttribute("aria-orientation", orientation);
    const adjust = event => {
        const value = getValue(event);
        apply(value);
        handle.setAttribute("aria-valuenow", String(Math.round(value * 100)));
    };
    handle.addEventListener("pointerdown", event => {
        event.preventDefault(); handle.setPointerCapture(event.pointerId);
        handle.addEventListener("pointermove", adjust);
        const stop = () => { handle.removeEventListener("pointermove", adjust); handle.removeEventListener("pointerup", stop); handle.removeEventListener("pointercancel", stop); };
        handle.addEventListener("pointerup", stop); handle.addEventListener("pointercancel", stop);
    });
    handle.addEventListener("keydown", event => {
        if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
        event.preventDefault();
        const value = Math.max(.1, Math.min(.9, Number(handle.getAttribute("aria-valuenow") || 40) / 100 + (["ArrowRight", "ArrowDown"].includes(event.key) ? .04 : -.04)));
        apply(value); handle.setAttribute("aria-valuenow", String(Math.round(value * 100)));
    });
}
function buildQuestion(question, index) {
    const card = document.createElement("section"); card.className = "question-card";
    const layout = document.createElement("div"); layout.className = "question-layout";
    const hasStimulus = Boolean(question.stimulus && config.stimuliHtml[question.stimulus]);
    if (question.response_type === "stimulus_only") {
        const stimulus = document.createElement("article"); stimulus.className = "stimulus-only-pane";
        stimulus.innerHTML = config.stimuliHtml[question.stimulus]; layout.classList.add("stimulus-only-layout"); layout.append(stimulus);
    } else {
        const response = document.createElement("div"); response.className = "response-pane";
        if (hasStimulus) {
            const stimulus = document.createElement("article"); stimulus.className = "stimulus-pane"; stimulus.innerHTML = config.stimuliHtml[question.stimulus];
            const handle = document.createElement("div"); handle.className = "resize-handle"; handle.setAttribute("aria-label", "Resize stimulus and response");
            layout.append(stimulus, handle, response);
            const apply = ratio => {
                if (matchMedia("(max-width:580px)").matches) layout.style.gridTemplateRows = `minmax(0,${ratio}fr) 6px minmax(0,${1-ratio}fr)`;
                else layout.style.gridTemplateColumns = `minmax(0,${ratio}fr) 6px minmax(0,${1-ratio}fr)`;
            };
            splitter(handle, event => {
                const rect = layout.getBoundingClientRect();
                return Math.max(.15, Math.min(.85, matchMedia("(max-width:580px)").matches ? (event.clientY - rect.top) / rect.height : (event.clientX - rect.left) / rect.width));
            }, apply);
        } else { response.classList.add("response-full"); layout.append(response); }
        if (question.response_type === "code_editor") renderCodeEditor(question, response);
        else renderShortAnswer(question, response);
    }
    card.append(layout);
    if (!config.standalone) {
        const footer = document.createElement("div"); footer.className = "question-footer";
        const previous = document.createElement("button"); previous.textContent = "Previous"; previous.disabled = index === 0;
        previous.onclick = () => showQuestion(index - 1);
        const hint = document.createElement("span"); hint.textContent = "Alt + ← / →";
        const next = document.createElement("button"); next.textContent = index === assessment.questions.length - 1 ? "Finish" : "Next";
        next.onclick = () => index < assessment.questions.length - 1 ? showQuestion(index + 1) : submitAssessment();
        footer.append(previous, hint, next); card.append(footer);
    }
    return card;
}
function renderShortAnswer(question, host) {
    host.classList.add("short-answer-pane");
    (question.response_config.fields || []).forEach((field, index) => {
        const id = `${question.id}:${field.id || index}`;
        const wrap = document.createElement("label"); wrap.className = "short-answer-field";
        const title = document.createElement("div"); title.className = "field-prompt"; title.innerHTML = field.question_html || field.question_text || "";
        const input = document.createElement("input"); input.type = field.email ? "email" : "text";
        input.maxLength = field.character_limit || 100; input.value = state.answers[id] || "";
        if (field.numeric_only) { input.inputMode = "numeric"; input.pattern = "[0-9]*"; }
        input.oninput = () => {
            if (field.numeric_only) input.value = input.value.replace(/[^0-9]/g, "");
            if (field.allowed_range && input.value) input.setCustomValidity(Number(input.value) < field.allowed_range[0] || Number(input.value) > field.allowed_range[1] ? `Enter ${field.allowed_range[0]}–${field.allowed_range[1]}.` : "");
            else input.setCustomValidity("");
            state.answers[id] = input.value; save();
        };
        input.onchange = () => input.reportValidity();
        wrap.append(title, input); host.append(wrap);
    });
}
function renderCodeEditor(question, host) {
    const c = question.response_config;
    const workbench = document.createElement("div"); workbench.className = "code-workbench";
    const explorer = document.createElement("aside"); explorer.className = "file-explorer";
    const explorerTitle = document.createElement("div"); explorerTitle.className = "explorer-title"; explorerTitle.textContent = "Explorer";
    const folder = document.createElement("div"); folder.className = "folder-title"; folder.textContent = "⌄ Program";
    const fileRow = document.createElement("button"); fileRow.className = "file-row selected";
    explorer.append(explorerTitle, folder, fileRow);
    const explorerHandle = document.createElement("div"); explorerHandle.className = "resize-handle"; explorerHandle.setAttribute("aria-label", "Resize explorer");
    const workspace = document.createElement("div"); workspace.className = "editor-workspace";
    splitter(explorerHandle, event => {
        const rect = workbench.getBoundingClientRect(); return Math.max(.08, Math.min(.4, (event.clientX - rect.left) / rect.width));
    }, ratio => workbench.style.gridTemplateColumns = `minmax(55px,${ratio}fr) 5px minmax(0,${1-ratio}fr)`);
    const toolbar = document.createElement("div"); toolbar.className = "editor-toolbar";
    const fileTab = document.createElement("span"); fileTab.className = "editor-tab";
    const select = document.createElement("select"); select.setAttribute("aria-label", "Programming language");
    c.supported_languages.forEach(language => { if (config.languages[language]) select.add(new Option(config.languages[language].label, language)); });
    const questionLanguageKey = `language:${assessment.id}:${question.id}`;
    const assessmentLanguageKey = `language:${assessment.id}:last-used`;
    const preferred = sessionStorage.getItem(questionLanguageKey) ?? sessionStorage.getItem(assessmentLanguageKey);
    if (c.supported_languages.includes(preferred)) select.value = preferred;
    // Freeze the initial choice for this question, even if it stays on the default.
    sessionStorage.setItem(questionLanguageKey, select.value);
    sessionStorage.setItem(assessmentLanguageKey, select.value);
    const actions = document.createElement("div"); actions.className = "editor-actions";
    const status = document.createElement("span"); status.className = "diagnostic-status"; status.setAttribute("role", "status");
    const run = document.createElement("button"); run.className = "run-button"; run.textContent = "▶ Run"; run.disabled = true; run.hidden = !c.runnable;
    const tests = document.createElement("button"); tests.textContent = "Run tests"; tests.hidden = !c.runnable_tests; tests.disabled = true;
    const reset = document.createElement("button"); reset.textContent = "Reset"; reset.hidden = c.read_only; reset.disabled = true;
    const toggleExplorer = document.createElement("button"); toggleExplorer.textContent = "Files"; toggleExplorer.setAttribute("aria-label", "Toggle explorer"); toggleExplorer.hidden = c.file_browser === false;
    actions.append(status, toggleExplorer, run, tests, reset, select); toolbar.append(fileTab, actions);
    const editorEl = document.createElement("div"); editorEl.className = "monaco-question-editor";
    workspace.append(toolbar, editorEl);
    const outputHandle = document.createElement("div"); outputHandle.className = "resize-handle output-resizer"; outputHandle.setAttribute("aria-label", "Resize editor and output");
    const outputPanel = document.createElement("section"); outputPanel.className = "output-panel";
    const outputHeader = document.createElement("div"); outputHeader.className = "output-header";
    const outputTitle = document.createElement("span"); outputTitle.textContent = "Terminal";
    const terminalControls = document.createElement("div"); terminalControls.className = "terminal-controls";
    const batchLabel = document.createElement("label"); const batch = document.createElement("input"); batch.type = "checkbox"; batchLabel.append(batch, "Pretyped input"); batchLabel.hidden = !c.allow_input;
    const stop = document.createElement("button"); stop.textContent = "Stop"; stop.disabled = true;
    const eof = document.createElement("button"); eof.textContent = "EOF"; eof.title = "Close standard input (Ctrl+D)"; eof.disabled = true;
    const clear = document.createElement("button"); clear.textContent = "Clear";
    terminalControls.append(batchLabel, eof, stop, clear); outputHeader.append(outputTitle, terminalControls);
    const stdin = document.createElement("textarea"); stdin.className = "stdin"; stdin.hidden = true; stdin.placeholder = "Standard input"; stdin.setAttribute("aria-label", "Pretyped standard input");
    const screen = document.createElement("div"); screen.className = "terminal-screen";
    const output = document.createElement("pre"); output.className = "output";
    const input = document.createElement("input"); input.className = "terminal-input"; input.size = 1; input.hidden = true; input.autocomplete = "off"; input.spellcheck = false; input.setAttribute("aria-label", "Terminal input — Enter to send");
    input.oninput = () => input.size = Math.max(1, input.value.length + 1);
    screen.append(output, input); outputPanel.append(outputHeader, stdin, screen); workspace.append(outputHandle, outputPanel);
    outputPanel.hidden = outputHandle.hidden = !c.output;
    splitter(outputHandle, event => {
        const rect = workspace.getBoundingClientRect(); return Math.max(.12, Math.min(.75, (rect.bottom - event.clientY) / rect.height));
    }, ratio => outputPanel.style.flexBasis = `${Math.max(.12, Math.min(.75, ratio)) * 100}%`, "horizontal");
    workbench.append(explorer, explorerHandle, workspace); host.append(workbench);
    function showExplorer(visible) { explorer.hidden = explorerHandle.hidden = !visible; workbench.classList.toggle("no-explorer", !visible); if (!visible) workbench.style.gridTemplateColumns = ""; toggleExplorer.setAttribute("aria-pressed", String(visible)); }
    showExplorer(c.file_browser !== false);
    toggleExplorer.onclick = () => showExplorer(explorer.hidden);
    fileRow.onclick = () => editor?.focus();
    batch.onchange = () => { stdin.hidden = !batch.checked; };
    clear.onclick = () => { output.textContent = ""; };
    screen.onclick = () => { if (!input.hidden && !window.getSelection().toString()) input.focus(); };
    let editor = null, disposed = false, diagnosticTimer, diagnosticAbort, terminalId, pollTimer, focusedTerminal = false;
    function filename() { return select.value === "python" ? "main.py" : select.value === "java" ? "Main.java" : "main.cpp"; }
    function refreshFilename() { fileRow.textContent = fileTab.textContent = filename(); }
    refreshFilename();
    function getCode() { return editor?.getValue() || ""; }
    function terminalDone() { run.disabled = tests.disabled = !editor; stop.disabled = eof.disabled = true; input.hidden = true; batch.disabled = select.disabled = false; }
    async function poll() {
        try {
            const data = await api(`/api/terminal/${terminalId}`);
            if (disposed) return;
            output.textContent = data.output;
            input.hidden = !c.allow_input || data.done || !data.ready;
            input.disabled = !data.ready;
            if (!input.hidden && !focusedTerminal) { input.focus(); focusedTerminal = true; }
            eof.disabled = !c.allow_input || data.done || !data.ready;
            screen.scrollTop = screen.scrollHeight;
            if (data.done) { terminalId = null; terminalDone(); }
            else pollTimer = setTimeout(poll, 150);
        } catch (error) { output.textContent += `\n${error.message}`; terminalId = null; terminalDone(); }
    }
    async function sendInput(value) {
        if (!terminalId) return;
        input.disabled = true;
        try {
            const data = await api(`/api/terminal/${terminalId}`, {input: value});
            output.textContent = data.output;
            input.value = "";
            input.size = 1;
        } catch (error) { output.textContent += `\n${error.message}`; }
        finally { input.disabled = false; input.focus(); }
    }
    input.onkeydown = event => {
        if (event.key === "Enter") { event.preventDefault(); sendInput(input.value + "\n"); }
        if (event.ctrlKey && event.key.toLowerCase() === "d") { event.preventDefault(); eof.click(); }
        if (event.ctrlKey && event.key.toLowerCase() === "c") { event.preventDefault(); stop.click(); }
    };
    eof.onclick = async () => { if (terminalId) { await api(`/api/terminal/${terminalId}`, {eof: true}).catch(error => output.textContent += `\n${error.message}`); input.hidden = true; eof.disabled = true; } };
    stop.onclick = () => terminalId && api(`/api/terminal/${terminalId}`, {stop: true}).catch(error => output.textContent += `\n${error.message}`);
    run.onclick = async () => {
        run.disabled = tests.disabled = select.disabled = batch.disabled = true; output.textContent = ""; focusedTerminal = false;
        try {
            if (batch.checked) {
                output.textContent = (await api(config.runUrl, {language: select.value, code: getCode(), input: stdin.value})).output;
                terminalDone();
            } else {
                const data = await api("/api/terminal", {language: select.value, code: getCode()});
                if (disposed) { await api(`/api/terminal/${data.id}`, {stop: true}); return; }
                terminalId = data.id; stop.disabled = false; await poll();
                if (!input.hidden) input.focus();
            }
        } catch (error) { output.textContent = error.message; terminalDone(); }
    };
    tests.onclick = async () => {
        tests.disabled = run.disabled = true; output.textContent = "Running tests…";
        try {
            await persist();
            const code = getCode();
            const data = await api(config.testsUrl, {attempt_id: state.id, question_id: question.id, language: select.value, code});
            if (code === getCode()) state.score = data.score;
            updateScore();
            output.textContent = data.tests.map(t => `${t.passed ? "✓" : "✗"} ${t.name}: ${t.output}`).join("\n") || "No tests configured.";
        } catch (error) { output.textContent = error.message; }
        finally { tests.disabled = run.disabled = false; }
    };
    async function diagnose() {
        if (!editor || disposed || !c.intellisense) return;
        diagnosticAbort?.abort(); diagnosticAbort = new AbortController();
        const model = editor.getModel(), version = model.getVersionId();
        status.textContent = "Checking…";
        try {
            const data = await api("/api/diagnostics", {language: select.value, code: model.getValue()}, {signal: diagnosticAbort.signal});
            if (disposed || model.isDisposed() || editor.getModel() !== model || model.getVersionId() !== version) return;
            const markers = data.markers.map(m => ({startLineNumber: m.line, endLineNumber: m.line, startColumn: m.column, endColumn: m.column + 1, message: m.message, severity: m.severity === "error" ? monaco.MarkerSeverity.Error : m.severity === "warning" ? monaco.MarkerSeverity.Warning : monaco.MarkerSeverity.Info}));
            monaco.editor.setModelMarkers(model, "server", markers);
            status.textContent = markers.length ? `${markers.length} diagnostic${markers.length === 1 ? "" : "s"}` : "No issues found";
            status.title = markers.map(m => `Line ${m.startLineNumber}: ${m.message}`).join("\n") || data.message || "Syntax and compiler checks; not a complete language server.";
        } catch (error) { if (error.name !== "AbortError") { status.textContent = "Checks unavailable"; status.title = error.message; } }
    }
    function scheduleDiagnostics() { clearTimeout(diagnosticTimer); diagnosticTimer = setTimeout(diagnose, 650); }
    select.onchange = () => {
        if (!editor) return;
        const old = editor.getModel();
        const model = monaco.editor.createModel(state.answers[question.id]?.[select.value] ?? c.default_code[select.value] ?? "", select.value);
        editor.setModel(model); old.dispose(); refreshFilename(); scheduleDiagnostics();
        sessionStorage.setItem(questionLanguageKey, select.value);
        sessionStorage.setItem(assessmentLanguageKey, select.value);
    };
    reset.onclick = () => editor?.setValue(c.default_code[select.value] || "");
    cleanups.push(() => {
        disposed = true; clearTimeout(diagnosticTimer); clearTimeout(pollTimer); diagnosticAbort?.abort();
        if (terminalId) fetch(`/api/terminal/${terminalId}`, {method: "POST", headers: {"Content-Type": "application/json"}, body: '{"stop":true}', keepalive: true});
    });
    if (!window.require) { editorEl.textContent = "Editor unavailable. Refresh when connected to the internet."; return; }
    window.require.config({paths: {vs: config.monacoBase + "vs"}});
    window.require(["vs/editor/editor.main"], () => {
        if (disposed) return;
        if (!completionsRegistered) {
            completionsRegistered = true;
            Object.entries(config.languages).forEach(([language, settings]) => {
                monaco.languages.registerCompletionItemProvider(language, {provideCompletionItems(model, position) {
                    const word = model.getWordUntilPosition(position);
                    const range = {startLineNumber: position.lineNumber, endLineNumber: position.lineNumber, startColumn: word.startColumn, endColumn: word.endColumn};
                    const names = new Set([...settings.suggestions, ...(model.getValue().match(/\b[A-Za-z_]\w*\b/g) || [])]);
                    return {suggestions: [...names].map(name => ({label: name, insertText: name, kind: monaco.languages.CompletionItemKind.Text, range}))};
                }});
            });
        }
        const language = select.value;
        editor = monaco.editor.create(editorEl, {value: state.answers[question.id]?.[language] ?? c.default_code[language] ?? "", language,
            theme: "vs-dark", automaticLayout: true, fontSize: 14, minimap: {enabled: false}, wordWrap: "on", scrollBeyondLastLine: false,
            autoClosingBrackets: "always", autoIndent: "full", quickSuggestions: c.intellisense, suggestOnTriggerCharacters: c.intellisense,
            tabCompletion: c.intellisense ? "on" : "off", readOnly: Boolean(c.read_only)});
        run.disabled = tests.disabled = reset.disabled = false;
        state.answers[question.id] ||= {};
        state.answers[question.id][language] = editor.getValue(); save();
        editor.onDidChangeModelContent(() => {
            state.answers[question.id] ||= {}; state.answers[question.id][select.value] = getCode();
            delete state.score[question.id]; updateScore(); save(); scheduleDiagnostics();
        });
        editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => c.runnable ? run.click() : c.runnable_tests && tests.click());
        scheduleDiagnostics(); editorInstances.push(editor);
    });
}
function disposeQuestion() {
    cleanups.forEach(cleanup => cleanup()); cleanups = [];
    editorInstances.forEach(editor => { const model = editor.getModel(); editor.dispose(); model?.dispose(); }); editorInstances = [];
}
function showQuestion(index) {
    if (index < 0 || index >= assessment.questions.length || state.submitted) return;
    activeQuestion = index; disposeQuestion();
    const host = document.getElementById("question-host");
    host.replaceChildren(buildQuestion(assessment.questions[index], index));
    if (window.katex) host.querySelectorAll(".math-expression").forEach(node => {
        katex.render(node.dataset.math, node, {displayMode: node.dataset.display === "true", throwOnError: false, trust: false});
    });
    questionSelect.value = index;
}
function finish() {
    disposeQuestion();
    document.getElementById("submit-assessment").disabled = true;
    document.getElementById("question-host").inert = true;
    document.getElementById("complete-title").textContent = state.reason === "timeout" ? "Time is up" : "Assessment submitted";
    document.getElementById("complete-message").textContent = assessment.score_visibility.upon_completion ? `Tests passed: ${formatScore()}` : "Your work has been saved.";
    document.getElementById("complete-dialog").hidden = false;
    updateScore();
}
async function submitAssessment(automatic = false, reason = "submitted") {
    if (state.submitted || submitting || config.standalone) return;
    if (!automatic) {
        const invalid = [...document.querySelectorAll(".short-answer-field input")].find(input => !input.checkValidity());
        if (invalid) { invalid.reportValidity(); return; }
        if (!confirm("Submit this assessment? Answers cannot be changed afterward.")) return;
    }
    submitting = true;
    try { await persist({submit: true, reason}); }
    catch (error) { if (!automatic) alert(`Submission failed: ${error.message}. Your answers remain open. Retry Submit.`); }
    finally { submitting = false; }
}
function updateTimer() {
    if (!state.deadline || state.submitted) return;
    const remaining = Math.max(0, Math.ceil((state.deadline * 1000 - Date.now() - clockOffset) / 1000));
    document.getElementById("timer").textContent = `${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, "0")}`;
    if (!remaining) persist().catch(() => {});
}
document.getElementById("submit-assessment").onclick = () => submitAssessment();
document.getElementById("submit-assessment").hidden = config.standalone || Boolean(assessment.time_limit_seconds && !assessment.submittable_early);
document.getElementById("complete-home").onclick = () => location.href = "/";
document.getElementById("exit-assessment").onclick = async event => {
    if (config.standalone || state.submitted) return;
    event.preventDefault();
    if (assessment.auto_submit_on_leave) {
        if (!confirm("Leaving will submit this assessment. Continue?")) return;
        await submitAssessment(true, "leave");
        if (state.submitted) location.href = "/";
    } else { try { await persist(); location.href = "/"; } catch (error) { alert(error.message); } }
};
function beaconSave() {
    if (config.standalone || state.submitted || !state.id) return;
    const body = {answers: state.answers, ...(assessment.auto_submit_on_leave ? {submit: true, reason: "leave"} : {})};
    navigator.sendBeacon(`/api/attempt/${state.id}`, new Blob([JSON.stringify(body)], {type: "application/json"}));
}
window.addEventListener("pagehide", beaconSave);
document.addEventListener("visibilitychange", () => { if (document.hidden && !assessment.auto_submit_on_leave) beaconSave(); });
document.addEventListener("keydown", event => {
    if (event.altKey && ["ArrowRight", "ArrowLeft"].includes(event.key)) { event.preventDefault(); showQuestion(activeQuestion + (event.key === "ArrowRight" ? 1 : -1)); }
});
async function initialize() {
    try {
        if (!config.standalone) {
            let passcode;
            if (assessment.requires_passcode) passcode = prompt("Assessment passcode");
            const data = await api(config.attemptUrl, {passcode}); state = data.attempt; acceptClock(data);
        }
        buildNavigation(); showQuestion(0); updateScore(); updateTimer();
        if (config.standalone) document.getElementById("question-nav").hidden = true;
        setInterval(updateTimer, 1000);
        if (!config.standalone) setInterval(async () => {
            if (state.submitted || submitting) return;
            try { await persist(); } catch (_) { /* Keep retrying while work is open. */ }
        }, 5000);
    } catch (error) {
        document.getElementById("question-host").textContent = error.message;
        document.getElementById("submit-assessment").disabled = true;
    }
}
initialize();
