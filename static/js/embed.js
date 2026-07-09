// ============================================
// EMBED — hide data inside an image
// ============================================

// ── EMBED ──
let stegoB64 = null;
async function runEmbed() {
  const coverImage = document.getElementById("embed-file").files[0];
  const hideType = document.getElementById("hide-type").value;
  const message = document.getElementById("embed-msg").value.trim();
  const password = document.getElementById("embed-password").value;

  const embeddingProfile =
    document.getElementById("embedding-profile").value;

  const hiddenFile = document.getElementById("secret-file").files[0];
  const hiddenImage = document.getElementById("secret-image").files[0];

  const btn = document.getElementById("embed-btn");
  // Cover image optimization notice
  const optimizeBox = document.getElementById("embed-success");
  hideErr("embed-err");
  document.getElementById("embed-result").classList.remove("visible");

  if (!coverImage)
    return showErr("embed-err", "Please select a cover image.");

  if (hideType === "text" && !message)
    return showErr("embed-err", "Please enter a message.");

  if (hideType === "file" && !hiddenFile)
    return showErr("embed-err", "Please choose a file to hide.");

  if (hideType === "image" && !hiddenImage)
    return showErr("embed-err", "Please choose an image to hide.");

  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div><span>Embedding...</span>';

  const form = new FormData();

  form.append("image", coverImage);
  form.append("password", password);
  form.append("payload_type", hideType);

  form.append("embedding_profile", embeddingProfile);

  if (hideType === "text") {
    form.append("message", message);
  }

  if (hideType === "file") {
    form.append("hidden_file", hiddenFile);
  }

  if (hideType === "image") {
    form.append("hidden_image", hiddenImage);
  }

  try {
    optimizeBox.style.display = "block";

    if (selectedPayloadMB >= 1) {
      optimizeBox.textContent =
        "Large hidden data detected. Original image quality will be preserved, so embedding may take longer.";
    } else {
      optimizeBox.textContent =
        "Optimizing cover image for faster and reliable LSB embedding.";
    }

    // allow browser to update UI before processing
    await new Promise((resolve) => setTimeout(resolve, 100));

    const res = await fetch("/embed", {
      method: "POST",
      body: form,
    });

    const data = await res.json();

    if (data.error) {
      showErr("embed-err", data.error);
      return;
    }

    optimizeBox.style.display = "block";

    optimizeBox.textContent = "Embedding completed successfully.";

    stegoB64 = data.stego;

    document.getElementById("embed-stego").src =
      "data:image/png;base64," + data.stego;

    const pct = ((data.bits_used / data.capacity) * 100).toFixed(1);

    document.getElementById("cap-label").textContent =
      `Capacity used: ${pct}% (${data.bits_used} of ${data.capacity} bits)`;

    document.getElementById("cap-fill").style.width = pct + "%";

    document.getElementById("meta-bits").textContent =
      data.bits_used.toLocaleString();

    document.getElementById("meta-cap").textContent =
      data.capacity.toLocaleString();

    document.getElementById("embed-result").classList.add("visible");

    document.getElementById("dl-btn").onclick = () => {
      const a = document.createElement("a");
      a.href = "data:image/png;base64," + stegoB64;
      a.download = "secure_stego_image.png";
      a.click();
    };
  } catch (e) {
    showErr("embed-err", "Server error.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "<span>🔒</span><span>Embed into image</span>";
  }
}
