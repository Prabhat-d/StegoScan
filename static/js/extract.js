// ============================================
// EXTRACT — reveal hidden data from an image
// ============================================

// ── EXTRACT ──
async function runExtract() {
  const file = document.getElementById("extract-file").files[0];
  const password = document.getElementById("extract-password").value;
  const btn = document.getElementById("extract-btn");

  hideErr("extract-err");
  document.getElementById("copy-extract-btn").style.display = "none";
  document.getElementById("extract-result").classList.remove("visible");

  if (!file)
    return showErr("extract-err", "Please select a stego image.");

  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div><span>Extracting...</span>';

  const form = new FormData();
  form.append("image", file);
  form.append("password", password);

  try {
    const res = await fetch("/extract", {
      method: "POST",
      body: form,
    });

    const contentType = res.headers.get("content-type") || "";

    // ============================
    // FILE / IMAGE DOWNLOAD
    // ============================
    if (!contentType.includes("application/json")) {
      const blob = await res.blob();

      let filename = "hidden_file";

      const disposition = res.headers.get("Content-Disposition");

      if (disposition) {
        const match = disposition.match(/filename="?([^"]+)"?/);
        if (match) filename = match[1];
      }

      const badge = document.getElementById("extract-badge");
      const msgEl = document.getElementById("extract-msg");
      const resultBox = document.getElementById("extract-result");
      const downloadBtn = document.getElementById("extract-download");

      badge.textContent = "Hidden File Found";
      badge.className = "badge badge-success";

      msgEl.textContent =
        "Filename : " +
        filename +
        "\n\nClick the button below to download.";

      downloadBtn.style.display = "block";

      downloadBtn.onclick = () => {
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();

        URL.revokeObjectURL(url);
      };

      resultBox.classList.add("visible");

      return;
    }

    // ============================
    // TEXT MESSAGE
    // ============================

    const data = await res.json();

    if (data.error) {
      showErr("extract-err", data.error);
      return;
    }

    const badge = document.getElementById("extract-badge");
    const msgEl = document.getElementById("extract-msg");
    const resultBox = document.getElementById("extract-result");

    document.getElementById("extract-download").style.display = "none";

    if (data.password_incorrect) {
      badge.textContent = "Incorrect password";
      badge.className = "badge badge-danger";

      msgEl.textContent = "The password you entered is incorrect.";
    } else if (data.password_required) {
      badge.textContent = "Password required";
      badge.className = "badge badge-warn";

      msgEl.textContent = "This payload is password protected.";
    } else if (!data.found || !data.message) {
      badge.textContent = "No message found";
      badge.className = "badge badge-warn";

      msgEl.textContent = "(No hidden message detected in this image)";
    } else {
      badge.textContent = "Message recovered";
      badge.className = "badge badge-success";

      document.getElementById("copy-extract-btn").style.display =
        "inline-flex";

      msgEl.textContent = "";

      const chars = data.message.split("");

      let i = 0;

      const type = () => {
        if (i < chars.length) {
          msgEl.textContent += chars[i++];
          setTimeout(type, 18);
        }
      };

      type();
    }

    resultBox.classList.add("visible");
  } catch (e) {
    showErr("extract-err", "Server error.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "<span>🔍</span><span>Extract message</span>";
  }
}
