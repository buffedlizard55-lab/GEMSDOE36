// Public source-freshness indicator ONLY. Never treat commit updates as score receipts.
(() => {
  "use strict";
  const ids = [24, 25, 27, 28, 30, 31, 32, 33, 36];
  const refresh = document.getElementById("refresh-source-feed");
  const status = document.getElementById("source-feed-status");
  const list = document.getElementById("source-feed-list");
  if (!refresh || !status || !list) return;

  async function updateOne(id) {
    const repo = `GEMSDOE${id}`;
    const url = `https://api.github.com/repos/buffedlizard55-lab/${repo}/commits?per_page=1`;
    const response = await fetch(url, { headers: { Accept: "application/vnd.github+json" } });
    if (!response.ok) throw new Error(`GitHub API HTTP ${response.status}`);
    const commits = await response.json();
    const latest = commits[0];
    if (!latest || !/^[0-9a-f]{40}$/.test(latest.sha)) throw new Error("No public commit");
    const timestamp = latest.commit && latest.commit.author && latest.commit.author.date;
    const date = timestamp ? new Date(timestamp) : new Date(NaN);
    if (Number.isNaN(date.getTime())) throw new Error("No commit timestamp");
    return { repo, sha: latest.sha, date: date.toISOString() };
  }

  async function update() {
    refresh.disabled = true;
    status.textContent = "Checking nine public repositories…";
    list.replaceChildren();
    try {
      const results = await Promise.allSettled(ids.map(updateOne));
      let healthy = 0;
      results.forEach((result, index) => {
        const li = document.createElement("li");
        if (result.status === "fulfilled") {
          healthy++;
          const { repo, sha, date } = result.value;
          const link = document.createElement("a");
          link.href = `https://github.com/buffedlizard55-lab/${repo}/commit/${sha}`;
          link.rel = "noopener noreferrer";
          link.target = "_blank";
          link.textContent = `${repo} ${sha.slice(0, 8)}`;
          const time = document.createElement("time");
          time.dateTime = date;
          time.textContent = ` · last public commit ${date.slice(0, 10)} UTC`;
          li.append(link, time);
        } else {
          li.textContent = `GEMSDOE${ids[index]} · unavailable (GitHub API rate limit, network, or private repository). See pinned source in audit.`;
        }
        list.append(li);
      });
      status.textContent = `${healthy}/9 public sources checked at ${new Date().toISOString().slice(0, 19)} UTC. Commit timestamps are NOT leaderboard scores or organizer receipts.`;
    } catch {
      status.textContent = "Source activity could not be checked. Use the pinned audit and official leaderboard links.";
    } finally {
      refresh.disabled = false;
    }
  }

  refresh.addEventListener("click", update);
  update();
})();
