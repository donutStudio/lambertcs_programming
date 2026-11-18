// Browser storage no longer owns attempts. This helper only clears legacy caches.
// Server records and attempt limits are deliberately unaffected.
if (location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
    throw new Error("This development helper only runs on localhost.");
}
for (const key of Object.keys(localStorage)) {
    if (key.startsWith("attempt:") || key.startsWith("attempt-count:")) localStorage.removeItem(key);
}
console.info("Cleared legacy browser caches. Attempts and submissions remain on the server.");
