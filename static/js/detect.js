/* Steganalysis forensic detection & UI report rendering */

let currentBitplanes = null;

function toggleDetectView(mode) {
  const btnOverview = document.getElementById("tab-btn-overview");
  const btnAdvanced = document.getElementById("tab-btn-advanced");
  const viewOverview = document.getElementById("view-detect-overview");
  const viewAdvanced = document.getElementById("view-detect-advanced");

  if (!btnOverview || !btnAdvanced || !viewOverview || !viewAdvanced) return;

  if (mode === "overview") {
    btnOverview.style.borderColor = "var(--accent)";
    btnOverview.style.background = "var(--bg2)";
    btnOverview.style.color = "#fff";
    btnOverview.classList.add("active");

    btnAdvanced.style.borderColor = "var(--border)";
    btnAdvanced.style.background = "var(--bg1)";
    btnAdvanced.style.color = "var(--text2)";
    btnAdvanced.classList.remove("active");

    viewOverview.style.display = "block";
    viewAdvanced.style.display = "none";
  } else {
    btnAdvanced.style.borderColor = "var(--accent)";
    btnAdvanced.style.background = "var(--bg2)";
    btnAdvanced.style.color = "#fff";
    btnAdvanced.classList.add("active");

    btnOverview.style.borderColor = "var(--border)";
    btnOverview.style.background = "var(--bg1)";
    btnOverview.style.color = "var(--text2)";
    btnOverview.classList.remove("active");

    viewOverview.style.display = "none";
    viewAdvanced.style.display = "block";
  }
}

function switchBitplane(channel, btn) {
  if (!currentBitplanes) return;
  document.querySelectorAll(".bitplane-tab-btn").forEach((b) => b.classList.remove("active"));
  if (btn) btn.classList.add("active");

  const lsbImg = document.getElementById("lsb-img");
  if (channel in currentBitplanes) {
    lsbImg.src = "data:image/png;base64," + currentBitplanes[channel];
  }
}

async function runDetect() {
  const file = document.getElementById("detect-file").files[0];
  hideErr("detect-err");
  document.getElementById("detect-result").classList.remove("visible");

  if (!file) return showErr("detect-err", "Please select an image to analyse.");

  const btn = document.getElementById("detect-btn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div><span>Analyzing...</span>';
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
    
    // Always default to Overview mode on new scan
    toggleDetectView("overview");

    // Verdict summary banner
    const banner = document.getElementById("verdict-banner");
    const icon = document.getElementById("verdict-icon");
    const title = document.getElementById("verdict-title");
    const sub = document.getElementById("verdict-sub");
    const sigType = data.sig_type || "StegoScan Payload";

    if (data.score >= 60) {
      banner.style.cssText += "background:rgba(239,68,68,0.08);border-color:rgba(239,68,68,0.3);color:var(--red);";
      icon.textContent = "🚨";
      title.textContent = "Strong Indicators of Hidden Data";
      sub.textContent = data.signature_detected
        ? `Verified ${sigType} header identified in image LSB plane.`
        : "Multiple statistical signals (RS Steganalysis, Chi-Square, Entropy) confirm high likelihood of hidden steganographic payload.";
    } else if (data.score >= 35) {
      banner.style.cssText += "background:rgba(245,158,11,0.08);border-color:rgba(245,158,11,0.3);color:var(--amber);";
      icon.textContent = "⚠️";
      title.textContent = "Possible Hidden Data";
      sub.textContent = "Some statistical anomalies detected. The image exhibits mild LSB distribution shifts.";
    } else {
      banner.style.cssText += "background:rgba(0,229,160,0.08);border-color:rgba(0,229,160,0.3);color:var(--green);";
      icon.textContent = "✅";
      title.textContent = "Image Appears Clean";
      sub.textContent = "No significant LSB statistical anomalies or RS steganography signals detected.";
    }

    // Risk score gauge & SVG ring
    const ring = document.getElementById("score-ring");
    const scoreNum = document.getElementById("score-num");
    const scoreLabel = document.getElementById("score-label");
    const circumference = 175.9;
    const score = data.score || 0;
    const strokeColor = score >= 60 ? "var(--red)" : score >= 35 ? "var(--amber)" : "var(--green)";
    ring.style.stroke = strokeColor;
    scoreLabel.style.color = strokeColor;
    scoreLabel.textContent = score >= 60 ? "High Risk" : score >= 35 ? "Medium Risk" : "Low Risk";
    setTimeout(() => {
      ring.style.strokeDashoffset = circumference - (score / 100) * circumference;
      animateCount(scoreNum, score, 0, 1200);
    }, 200);

    // Forensic findings list
    const reasonsList = document.getElementById("reasons-list");
    reasonsList.innerHTML = "";
    if (data.reasons && data.reasons.length > 0) {
      data.reasons.forEach((r, i) => {
        const d = document.createElement("div");
        d.style.cssText = "display:flex;align-items:flex-start;gap:7px;opacity:0;animation:fade-up 0.4s ease both;";
        d.style.animationDelay = i * 0.1 + "s";
        d.innerHTML = `<span style="color:var(--amber);flex-shrink:0;margin-top:1px;">›</span><span>${r}</span>`;
        reasonsList.appendChild(d);
      });
    } else {
      reasonsList.innerHTML = '<span style="color:var(--text3);">No statistical anomalies detected</span>';
    }

    // Executive Plain-English Summary Text
    const summaryBox = document.getElementById("executive-summary-text");
    if (summaryBox) {
      if (score >= 60) {
        summaryBox.innerHTML = `
          <strong>Verdict:</strong> 🔴 <span style="color: var(--red); font-weight:700;">Secret Hidden Payload Detected (~${data.rs_estimated_kb} KB)</span><br>
          <strong>Explanation:</strong> StegoScan identified artificial pixel alterations consistent with hidden data embedding. Natural camera photos do not exhibit this degree of lower-bit distribution shift.
        `;
      } else if (score >= 35) {
        summaryBox.innerHTML = `
          <strong>Verdict:</strong> 🟡 <span style="color: var(--amber); font-weight:700;">Suspicious Pixel Anomalies (~${data.rs_estimated_kb} KB)</span><br>
          <strong>Explanation:</strong> Mild LSB noise detected. This can happen with heavy image compression or low-light photos, but could indicate low-density hidden data.
        `;
      } else {
        summaryBox.innerHTML = `
          <strong>Verdict:</strong> 🟢 <span style="color: var(--green); font-weight:700;">Clean & Natural Image</span><br>
          <strong>Explanation:</strong> Pixel bits strictly follow natural camera photo distributions. No steganographic signatures or secret hidden payloads were found.
        `;
      }
    }

    // Spatial region LSB variance
    setTimeout(() => {
      document.getElementById("region-start").textContent = data.region_start.toFixed(4);
      document.getElementById("region-end").textContent = data.region_end.toFixed(4);
      document.getElementById("region-diff").textContent = data.region_difference.toFixed(4);
      document.getElementById("region-diff-pct").textContent = data.region_difference.toFixed(4);

      const regionBadge = document.getElementById("region-badge");
      const regionGauge = document.getElementById("region-gauge");
      const diff = data.region_difference;

      if (data.signature_detected) {
        regionBadge.textContent = "⚠ Signature Verified";
        regionBadge.style.cssText =
          "background:rgba(239,68,68,0.15);color:var(--red);font-size:10px;font-weight:700;padding:4px 12px;border-radius:12px;font-family:var(--mono);";
        regionGauge.style.background = "var(--red)";
        regionGauge.style.width = "100%";
      } else if (diff > 0.02) {
        regionBadge.textContent = "⚠ Pattern Found";
        regionBadge.style.cssText =
          "background:rgba(239,68,68,0.15);color:var(--red);font-size:10px;font-weight:700;padding:4px 12px;border-radius:12px;font-family:var(--mono);";
        regionGauge.style.background = "var(--red)";
        regionGauge.style.width = Math.min((diff / 0.04) * 100, 100) + "%";
      } else if (diff > 0.01) {
        regionBadge.textContent = "~ Variation";
        regionBadge.style.cssText =
          "background:rgba(245,158,11,0.15);color:var(--amber);font-size:10px;font-weight:700;padding:4px 12px;border-radius:12px;font-family:var(--mono);";
        regionGauge.style.background = "var(--amber)";
        regionGauge.style.width = Math.min((diff / 0.04) * 100, 100) + "%";
      } else {
        regionBadge.textContent = "✓ Stable";
        regionBadge.style.cssText =
          "background:rgba(0,229,160,0.15);color:var(--green);font-size:10px;font-weight:700;padding:4px 12px;border-radius:12px;font-family:var(--mono);";
        regionGauge.style.background = "var(--green)";
        regionGauge.style.width = Math.min((diff / 0.04) * 100, 100) + "%";
      }
    }, 300);

    setTimeout(() => {
      document.querySelectorAll(".metric-bar").forEach((b) => (b.style.transform = "scaleX(1)"));
    }, 400);

    // Supporting metrics values
    setTimeout(() => {
      document.getElementById("sv-balance").textContent = (data.balance_ratio * 100).toFixed(2) + "%";
      document.getElementById("sv-entropy").textContent = data.lsb_entropy.toFixed(4);
      document.getElementById("sv-chip").textContent = data.chi_p < 0.0001 ? "<0.0001" : data.chi_p.toFixed(4);

      const rsRatioEl = document.getElementById("sv-rs-ratio");
      const rsKbEl = document.getElementById("sv-rs-kb");
      if (rsRatioEl) rsRatioEl.textContent = (data.rs_payload_ratio * 100).toFixed(1) + "%";
      if (rsKbEl) rsKbEl.textContent = `est. ~${data.rs_estimated_kb} KB payload`;
    }, 450);

    // Bitplane images (R, G, B, RGB)
    currentBitplanes = data.bitplanes || { red: data.lsb_plane };
    document.getElementById("lsb-img").src = "data:image/png;base64," + currentBitplanes.red;

    document.querySelectorAll(".bitplane-tab-btn").forEach((b, idx) => {
      if (idx === 0) b.classList.add("active");
      else b.classList.remove("active");
    });

    document.getElementById("ls-total").textContent = data.total.toLocaleString();
    document.getElementById("ls-ones").textContent = data.ones.toLocaleString();
    document.getElementById("ls-zeros").textContent = data.zeros.toLocaleString();
    const ratioPct = (data.lsb_ratio * 100).toFixed(1);
    document.getElementById("ls-ratio").textContent = ratioPct + "%";

    // Written summary report
    document.getElementById("explain-box").innerHTML = `
<strong>Steganalysis Forensic Report:</strong><br>
The risk assessment combines <strong>Header Signature Verification</strong>, <strong>RS Steganalysis (Fridrich et al.)</strong>, 
<strong>Chi-Square PoV</strong>, <strong>LSB Entropy</strong>, and <strong>Regional Variation</strong>.
<br><br>
• Signature Status: ${data.signature_detected ? "Verified Magic Header Signature (" + sigType + ")" : "No Magic Signature Header"}<br>
• RS Estimated Payload: ${(data.rs_payload_ratio * 100).toFixed(1)}% of capacity (${data.rs_estimated_kb} KB)<br>
• Regional Difference: ${data.region_difference.toFixed(4)}<br>
• LSB Entropy: ${data.lsb_entropy.toFixed(4)}<br>
• LSB Bit Ratio: ${ratioPct}%<br>
• Chi-Square p-value: ${data.chi_p < 0.0001 ? "<0.0001" : data.chi_p.toFixed(4)}
<br><br>
<em>Result interpretation: High risk score indicates confirmed presence of steganographic payload data.</em>
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
    box.innerHTML = `ⓘ <strong>Image Specs:</strong> ${img.width}×${img.height} px | Hiding Capacity: ~${mb.toFixed(2)} MB`;
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
