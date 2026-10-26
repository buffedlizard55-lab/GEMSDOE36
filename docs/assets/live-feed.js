// Public GitHub source-freshness indicator ONLY; never a score or submission receipt.
(() => {
  "use strict";
  const ids = [24, 25, 27, 28, 30, 31, 32, 33, 36];
  const refresh = document.getElementById("refresh-source-feed");
  const status = document.getElementById("source-feed-status");
  const list = document.getElementById("source-feed-list");
  if (!refresh || !status || !list) return;

  async function updateOne(id, pinned) {
    const repo = `GEMSDOE${id}`;
    if (!/^[0-9a-f]{40}$/.test(pinned || "")) throw new Error("Missing pinned ref");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(`https://api.github.com/repos/buffedlizard55-lab/${repo}/commits/main`, {
        headers: { Accept: "application/vnd.github+json" }, signal: controller.signal, cache: "no-store"
      });
      if (!response.ok) throw new Error(`GitHub API HTTP ${response.status}`);
      const latest = await response.json();
      if (!latest || !/^[0-9a-f]{40}$/.test(latest.sha)) throw new Error("Missing public main ref");
      const timestamp = latest.commit && latest.commit.author && latest.commit.author.date;
      const date = timestamp ? new Date(timestamp) : new Date(NaN);
      if (Number.isNaN(date.getTime())) throw new Error("Missing public commit timestamp");
      return { repo, sha: latest.sha, pinned, date: date.toISOString(), changed: latest.sha !== pinned };
    } finally {
      clearTimeout(timeout);
    }
  }

  async function update() {
    refresh.disabled = true;
    status.textContent = "Checking nine public repositories against the pinned audit…";
    list.replaceChildren();
    try {
      const snapshot = await fetch("data/focus-refs.json", { cache: "no-store" });
      if (!snapshot.ok) throw new Error("Pinned snapshot unavailable");
      const refs = await snapshot.json();
      const results = await Promise.allSettled(ids.map(id => updateOne(id, refs[`GEMSDOE${id}`])));
      let checked = 0;
      let changed = 0;
      results.forEach((result, index) => {
        const li = document.createElement("li");
        if (result.status === "fulfilled") {
          checked++;
          const { repo, sha, pinned, date, changed: isChanged } = result.value;
          if (isChanged) changed++;
          const link = document.createElement("a");
          link.href = `https://github.com/buffedlizard55-lab/${repo}/commit/${sha}`;
          link.rel = "noopener noreferrer";
          link.target = "_blank";
          link.textContent = `${repo} ${sha.slice(0, 8)}`;
          const detail = document.createElement("span");
          detail.textContent = ` · ${isChanged ? "changed since" : "matches"} pinned ${pinned.slice(0, 8)} · commit ${date.slice(0, 10)} UTC`;
          li.append(link, detail);
        } else {
          li.textContent = `GEMSDOE${ids[index]} · unavailable (network, API rate limit, or missing snapshot ref).`;
        }
        list.append(li);
      });
      const time = new Date().toISOString().slice(0, 19).replace("T", " ");
      status.textContent = `${checked}/9 checked at ${time} UTC; ${changed} changed since the pinned snapshot. Changed commits do not prove new rasters or scores.`;
    } catch {
      status.textContent = "Source freshness unavailable. Use the pinned audit; no current inventory is established.";
    } finally {
      refresh.disabled = false;
    }
  }

  refresh.addEventListener("click", update);
  update();
})();
