const releaseApi = "https://api.github.com/repos/QuanMinhNguyen199/Windows-AI-Support-Agent/releases?per_page=100";
const stableDownload = "https://github.com/QuanMinhNguyen199/Windows-AI-Support-Agent/releases/latest/download/WinAssist-Setup.exe";

async function updateRelease() {
  const download = document.getElementById("download");
  const title = document.getElementById("release-title");
  const date = document.getElementById("release-date");
  const count = document.getElementById("download-count");
  try {
    const response = await fetch(releaseApi, { headers: { Accept: "application/vnd.github+json" } });
    if (!response.ok) throw new Error("release unavailable");
    const releases = await response.json();
    const release = releases.find((item) => !item.draft && !item.prerelease);
    if (!release) throw new Error("release unavailable");
    const hasInstaller = release.assets.some((asset) => asset.name === "WinAssist-Setup.exe");
    const totalDownloads = releases.reduce((total, item) => {
      const installer = item.assets.find((asset) => asset.name === "WinAssist-Setup.exe");
      return total + (installer?.download_count || 0);
    }, 0);
    if (hasInstaller) {
      download.querySelector("span").textContent = `Tải WinAssist ${release.tag_name}`;
      download.href = stableDownload;
    }
    title.textContent = release.name || `WinAssist ${release.tag_name}`;
    if (release.published_at) {
      const published = new Intl.DateTimeFormat("vi-VN", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      }).format(new Date(release.published_at));
      date.textContent = `Phát hành ngày ${published}`;
    }
    if (totalDownloads > 0) {
      count.lastChild.textContent = ` ${new Intl.NumberFormat("vi-VN").format(totalDownloads)} lượt tải WinAssist`;
    }
  } catch (_error) {
    title.textContent = "WinAssist 0.11.3.1";
    date.textContent = "Phát hành ngày 08/08/2026";
  }
}

updateRelease();
