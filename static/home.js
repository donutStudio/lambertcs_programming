const assessments = JSON.parse(document.getElementById("home-config").textContent);
const byId = Object.fromEntries(assessments.map(item => [item.id, item]));

document.querySelectorAll(".assessment-list li[data-assessment-id]").forEach(row => {
    const item = byId[row.dataset.assessmentId];
    const button = row.querySelector(".button");
    const status = row.querySelector(".attempt-status");
    const stateKey = `attempt:${item.id}`;
    const countKey = `attempt-count:${item.id}`;
    const state = JSON.parse(localStorage.getItem(stateKey) || "null");
    const count = Number(localStorage.getItem(countKey) || 0);
    const remaining = item.number_of_attempts === 0 || count < item.number_of_attempts;
    if (state && !state.submitted) {
        status.textContent = "In progress";
        button.textContent = "Resume";
        button.dataset.mode = "resume";
    } else if (state && state.submitted) {
        status.textContent = `Submitted${state.scoreText ? ` · ${state.scoreText}` : ""}`;
        button.textContent = remaining ? "Reattempt" : "Complete";
        button.dataset.mode = "reattempt";
        button.classList.toggle("button-disabled", !remaining);
        if (!remaining) button.removeAttribute("href");
    }
    button.addEventListener("click", event => {
        if (!remaining && button.dataset.mode !== "resume") { event.preventDefault(); return; }
        event.preventDefault();
        if (item.passcode) {
            const entered = window.prompt(`Enter the passcode for ${item.title}`);
            if (entered === null || entered !== item.passcode) {
                if (entered !== null) window.alert("That passcode is not correct.");
                return;
            }
        }
        const mode = button.dataset.mode || "start";
        if (mode !== "resume") localStorage.setItem(countKey, String(count + 1));
        const url = new URL(button.href, window.location.href);
        if (mode === "reattempt") url.searchParams.set("reattempt", "1");
        window.location.href = url.href;
    });
});
