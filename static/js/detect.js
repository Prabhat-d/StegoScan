// ============================================
// DETECT — LSB steganography detection & report rendering
// ============================================

// ── DETECT ──
async function runDetect() {
  const file = document.getElementById("detect-file").files[0];
  hideErr("detect-err");
  document.getElementById("detect-result").classList.remove("visible");

  if (!file)
    return showErr("detect-err", "Please select an image to analyse.");

  const btn = document.getElementById("detect-btn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML =
      '<div class="spinner"></div><span>Analyzing...</span>';
  }

  const form = new FormData();
  form.append("image", file);

  try {
    const res = await fetch("/detect", { method: "POST", body: form });
    const data = await res.json();
    if (data.error) {
      showErr("detect-err", data.error);
      return;
    }

    const warningBox = document.getElementById("detect-warning");

    if (data.warning) {
      warningBox.style.display = "block";
      warningBox.textContent = "⚠ " + data.warning;
    } else {
      warningBox.style.display = "none";
    }

    document.getElementById("detect-result").classList.add("visible");

    // ── VERDICT BANNER ──
    const banner = document.getElementById("verdict-banner");
    const icon = document.getElementById("verdict-icon");
    const title = document.getElementById("verdict-title");
    const sub = document.getElementById("verdict-sub");

    if (data.score >= 60) {
      banner.style.cssText +=
        "background:rgba(239,68,68,0.08);border-color:rgba(239,68,68,0.3);color:var(--red);";
      icon.textContent = "🚨";
      title.textContent = "Strong Indicators of Hidden Data";
      sub.textContent =
        "Multiple statistical patterns suggest possible hidden data. High confidence of steganographic modification.";
    } else if (data.score >= 35) {
      banner.style.cssText +=
        "background:rgba(245,158,11,0.08);border-color:rgba(245,158,11,0.3);color:var(--amber);";
      icon.textContent = "⚠️";
      title.textContent = "Possible Hidden Data";
      sub.textContent =
        "Some statistical indicators suggest possible modification. Not conclusive.";
    } else {
      banner.style.cssText +=
        "background:rgba(0,229,160,0.08);border-color:rgba(0,229,160,0.3);color:var(--green);";
      icon.textContent = "✅";
      title.textContent = "Image Appears Clean";
      sub.textContent =
        "No significant LSB statistical anomalies were detected.";
    }

    // ── RISK SCORE CIRCLE ──
    const ring = document.getElementById("score-ring");
    const scoreNum = document.getElementById("score-num");
    const scoreLabel = document.getElementById("score-label");
    const circumference = 175.9;
    const score = data.score || 0;
    const strokeColor =
      score >= 60
        ? "var(--red)"
        : score >= 35
          ? "var(--amber)"
          : "var(--green)";
    ring.style.stroke = strokeColor;
    scoreLabel.style.color = strokeColor;
    scoreLabel.textContent =
      score >= 60
        ? "High Risk"
        : score >= 35
          ? "Medium Risk"
          : "Low Risk";
    setTimeout(() => {
      ring.style.strokeDashoffset =
        circumference - (score / 100) * circumference;
      animateCount(scoreNum, score, 0, 1200);
    }, 200);

    // ── REASONS ──
    const reasonsList = document.getElementById("reasons-list");
    reasonsList.innerHTML = "";
    if (data.reasons && data.reasons.length > 0) {
      data.reasons.forEach((r, i) => {
        const d = document.createElement("div");
        d.style.cssText =
          "display:flex;align-items:flex-start;gap:7px;opacity:0;animation:fade-up 0.4s ease both;";
        d.style.animationDelay = i * 0.1 + "s";
        d.innerHTML = `<span style="color:var(--amber);flex-shrink:0;margin-top:1px;">›</span><span>${r}</span>`;
        reasonsList.appendChild(d);
      });
    } else {
      reasonsList.innerHTML =
        '<span style="color:var(--text3);">No anomalies detected</span>';
    }

    // ── REGION ANALYSIS ──
    setTimeout(() => {
      document.getElementById("region-start").textContent =
        data.region_start.toFixed(4);
      document.getElementById("region-end").textContent =
        data.region_end.toFixed(4);
      document.getElementById("region-diff").textContent =
        data.region_difference.toFixed(4);
      document.getElementById("region-diff-pct").textContent =
        data.region_difference.toFixed(4);

      const regionBadge = document.getElementById("region-badge");
      const regionGauge = document.getElementById("region-gauge");
      const diff = data.region_difference;

      if (diff > 0.02) {
        regionBadge.textContent = "⚠ Pattern Found";
        regionBadge.style.cssText =
          "background:rgba(239,68,68,0.15);color:var(--red);font-size:10px;font-weight:700;padding:4px 12px;border-radius:12px;font-family:var(--mono);";
        regionGauge.style.background = "var(--red)";
      } else if (diff > 0.01) {
        regionBadge.textContent = "~ Variation";
        regionBadge.style.cssText =
          "background:rgba(245,158,11,0.15);color:var(--amber);font-size:10px;font-weight:700;padding:4px 12px;border-radius:12px;font-family:var(--mono);";
        regionGauge.style.background = "var(--amber)";
      } else {
        regionBadge.textContent = "✓ Stable";
        regionBadge.style.cssText =
          "background:rgba(0,229,160,0.15);color:var(--green);font-size:10px;font-weight:700;padding:4px 12px;border-radius:12px;font-family:var(--mono);";
        regionGauge.style.background = "var(--green)";
      }

      // Scale gauge: 0.04 = 100%
      const gaugeWidth = Math.min((diff / 0.04) * 100, 100);
      regionGauge.style.width = gaugeWidth + "%";
    }, 300);

    // ── METRIC BARS ANIMATION ──
    setTimeout(() => {
      document
        .querySelectorAll(".metric-bar")
        .forEach((b) => (b.style.transform = "scaleX(1)"));
    }, 400);

    // ── SUPPORTING METRICS ──
    setTimeout(() => {
      document.getElementById("sv-balance").textContent =
        (data.balance_ratio * 100).toFixed(2) + "%";
      document.getElementById("sv-entropy").textContent =
        data.lsb_entropy.toFixed(4);
      document.getElementById("sv-chip").textContent =
        data.chi_p < 0.0001 ? "<0.0001" : data.chi_p.toFixed(4);
    }, 450);

    // ── LSB PLANE ──
    document.getElementById("lsb-img").src =
      "data:image/png;base64," + data.lsb_plane;
    document.getElementById("ls-total").textContent =
      data.total.toLocaleString();
    document.getElementById("ls-ones").textContent =
      data.ones.toLocaleString();
    document.getElementById("ls-zeros").textContent =
      data.zeros.toLocaleString();
    const ratioPct = (data.lsb_ratio * 100).toFixed(1);
    document.getElementById("ls-ratio").textContent = ratioPct + "%";

    // ── EXPLAIN ──
    document.getElementById("explain-box").innerHTML = `
<strong>How to read this result:</strong>
The verdict is generated using multiple LSB statistical indicators including 
<strong>regional variation, LSB balance, entropy, and Chi-Square analysis</strong>.
<br><br>

Region difference: ${data.region_difference.toFixed(4)}<br>
LSB entropy: ${data.lsb_entropy.toFixed(4)}<br>
LSB balance: ${ratioPct}%<br>
Chi-Square p-value: ${data.chi_p < 0.0001 ? "<0.0001" : data.chi_p.toFixed(4)}

<br><br>
A single value does not confirm hidden data; the final risk score combines multiple signals.
`;
  } catch (e) {
    showErr("detect-err", "Server error. Is Flask running?");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = "<span>📊</span><span>Run full analysis</span>";
    }
  }
}

function showImageCapacity(input) {
  const file = input.files[0];

  if (!file) return;

  const img = new Image();

  img.onload = function () {
    const capacityBytes = (img.width * img.height * 3) / 8;

    const userCapacity = capacityBytes * 0.7;

    const mb = userCapacity / (1024 * 1024);

    const box = document.getElementById("capacity-info");

    box.style.display = "block";

    box.innerHTML = `ⓘ Estimated hiding capacity: about ${mb.toFixed(2)} MB of data.`;
  };

  img.src = URL.createObjectURL(file);
}

function showToast(message) {
  const toast = document.getElementById("toast");

  toast.textContent = message;

  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2000);
}
