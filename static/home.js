const assessments = JSON.parse(document.getElementById("home-config").textContent);
async function refresh() {
    try {
        const response = await fetch("/api/assignments");
        if (!response.ok) throw new Error("Could not load attempts. Refresh to retry.");
        const statuses = await response.json();
        document.querySelectorAll("li[data-assessment-id]").forEach(row => {
            const status = statuses[row.dataset.assessmentId];
            const button = row.querySelector(".button");
            const enabled = status.active || status.available;
            button.textContent = status.active ? "Resume" : !enabled ? "Complete" : status.count ? "Reattempt" : "Start";
            button.setAttribute("aria-disabled", String(!enabled));
            if (!enabled) button.removeAttribute("href");
            button.classList.toggle("button-disabled", !enabled);
        });
    } catch (error) { document.getElementById("home-status").textContent = error.message; }
}
document.querySelectorAll("li[data-assessment-id] .button").forEach(button => button.addEventListener("click", event => {
    if (button.getAttribute("aria-disabled") === "true") event.preventDefault();
}));
window.addEventListener("pageshow", refresh);
