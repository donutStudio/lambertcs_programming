const config = JSON.parse(document.getElementById("home-config").textContent);
const credentialsForm = document.getElementById("credentials-form");
let statuses = {};
function credentials() {
    return Object.fromEntries([...credentialsForm.elements].filter(input => input.name).map(input => [input.name, input.value.trim()]));
}
function renderStatuses() {
    document.querySelectorAll("li[data-assessment-id]").forEach(row => {
        const status = statuses[row.dataset.assessmentId];
        if (!status) return;
        const button = row.querySelector(".button");
        const required = JSON.parse(row.dataset.required || "[]");
        const missing = !status.active && required.some(key => {
            const input = credentialsForm.elements.namedItem(key);
            return !input.value.trim() || !input.checkValidity();
        });
        const enabled = (status.active || status.available) && !missing;
        button.textContent = status.active ? "Resume" : !status.available ? "Complete" : status.count ? "Reattempt" : "Start";
        button.title = missing ? "Complete the required student details: " + required.join(", ").replaceAll("_", " ") : "";
        button.setAttribute("aria-disabled", String(!enabled));
        if (enabled) button.href = button.dataset.url;
        else button.removeAttribute("href");
        button.classList.toggle("button-disabled", !enabled);
        row.querySelector(".assessment-score").textContent = status.score === null ? "" : `Score: ${status.score}`;
    });
}
if (credentialsForm) {
    try {
        const saved = JSON.parse(sessionStorage.getItem("assessment-credentials") || "{}");
        [...credentialsForm.elements].forEach(input => { if (input.name) input.value = saved[input.name] || ""; });
    } catch (_) {}
    credentialsForm.addEventListener("submit", event => event.preventDefault());
    credentialsForm.addEventListener("input", () => {
        sessionStorage.setItem("assessment-credentials", JSON.stringify(credentials()));
        renderStatuses();
    });
}
async function refresh() {
    try {
        const response = await fetch(config.assignmentsUrl, {cache: "no-store"});
        if (!response.ok) throw new Error("Could not load attempts. Refresh to retry.");
        statuses = await response.json();
        renderStatuses();
        document.getElementById("home-status").textContent = "";
    } catch (error) { document.getElementById("home-status").textContent = error.message; }
}
document.querySelectorAll("li[data-assessment-id] .button").forEach(button => button.addEventListener("click", event => {
    if (button.getAttribute("aria-disabled") === "true") event.preventDefault();
}));
window.addEventListener("pageshow", refresh);
if (credentialsForm) setInterval(refresh, 3000);
