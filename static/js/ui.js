// ============================================
// UI HELPERS — tabs, image preview, errors,
// counter animation, dropzone drag, misc toggles
// ============================================

// ── TABS ──
function switchTab(name, btn) {
  document
    .querySelectorAll(".tab-btn")
    .forEach((b) => b.classList.remove("active"));
  document
    .querySelectorAll(".panel")
    .forEach((p) => p.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("panel-" + name).classList.add("active");
}

// ── IMAGE PREVIEW ──
function previewImage(input, id) {
  const file = input.files[0];

  if(file.size > 25 * 1024 * 1024){

    showToast(
      "Image size must be below 25 MB"
    );

    input.value = "";

    return;
}

  if (file && !file.type.startsWith("image/")) {
    showToast("Please select a valid image file");

    input.value = "";

    return;
  }
  if (file) {
    showToast(`✓ ${file.name} selected`);
  }
  if (!file) return;

  const el = document.getElementById(id);
  const wrap = document.getElementById(id + "-wrap");

  el.src = URL.createObjectURL(file);
  el.style.display = "block";

  if (wrap) {
    wrap.style.display = "inline-block";
  }
}

function copyExtractedText() {
  const text = document.getElementById("extract-msg").textContent;

  navigator.clipboard.writeText(text);

  showToast("Copied to clipboard");
}

function clearSelectedImage(inputId, imgId, wrapId) {
  const input = document.getElementById(inputId);
  const img = document.getElementById(imgId);
  const wrap = document.getElementById(wrapId);

  if (input) input.value = "";
  if (img) {
    img.src = "";
    img.style.display = "none";
  }
  if (wrap) {
    wrap.style.display = "none";
  }
}

function resetResults() {
  document.querySelectorAll(".result-box").forEach((box) => {
    box.classList.remove("visible");
  });

  document.querySelectorAll(".err").forEach((err) => {
    err.style.display = "none";
  });

  const success = document.getElementById("embed-success");

  if (success) {
    success.style.display = "none";
  }
}

function resetEmbedForm() {
  resetResults();

  // message
  document.getElementById("embed-msg").value = "";

  // password
  document.getElementById("embed-password").value = "";

  // hidden files
  document.getElementById("secret-file").value = "";

  document.getElementById("secret-image").value = "";

  // hide file info
  document.getElementById("hidden-file-info").style.display = "none";

  document.getElementById("hidden-image-info").style.display = "none";

  document.getElementById("hidden-image-wrap").style.display = "none";

  // reset payload size
  selectedPayloadMB = 0;

  // reset profile backend value
  document.getElementById("embedding-profile").value = "standard";

  // reset profile text
  document.getElementById("profile-selected").textContent = "Standard";

  document.getElementById("profile-description").textContent =
    "Standard profile embeds only the original payload for minimal image modification.";

  // hide processing/success message
  document.getElementById("embed-success").style.display = "none";
}

function toggleHideType() {
  const type = document.getElementById("hide-type").value;

  document.getElementById("hide-text-block").style.display =
    type === "text" ? "block" : "none";

  document.getElementById("hide-file-block").style.display =
    type === "file" ? "block" : "none";

  document.getElementById("hide-image-block").style.display =
    type === "image" ? "block" : "none";
}

function toggleCustomSelect() {
  const select = document.getElementById("hide-type-select");
  select.classList.toggle("open");
}

function selectHideType(value, label) {
  document.getElementById("hide-type").value = value;
  document.getElementById("hide-type-selected").textContent = label;

  document.querySelectorAll(".custom-select-option").forEach((option) => {
    option.classList.remove("active");
    if (option.dataset.value === value) {
      option.classList.add("active");
    }
  });

  document.getElementById("hide-type-select").classList.remove("open");
  toggleHideType();
}

function showHiddenFile(input) {
  const file = input.files[0];

  const box = document.getElementById("hidden-file-info");

  if (!file) {
    box.style.display = "none";
    return;
  }

  const mb = (file.size * 1.35) / (1024 * 1024);

  selectedPayloadMB = mb;

  box.style.display = "block";

  box.innerHTML = `
    📄 ${file.name}<br>
    Size: ${mb.toFixed(2)} MB
    `;
}

function showHiddenImage(input) {
  const file = input.files[0];

  if (!file) return;

  const mb = (file.size * 1.35) / (1024 * 1024);

  selectedPayloadMB = mb;

  document.getElementById("hidden-image-info").style.display = "block";

  document.getElementById("hidden-image-info").innerHTML = `
    🖼️ ${file.name}<br>
    Size: ${mb.toFixed(2)} MB
    `;

  const preview = document.getElementById("hidden-image-preview");

  preview.src = URL.createObjectURL(file);

  document.getElementById("hidden-image-wrap").style.display = "block";
}

function toggleProfileSelect() {
  document.getElementById("profile-select").classList.toggle("open");
}

function selectProfile(value, label) {
  document.getElementById("embedding-profile").value = value;

  document.getElementById("profile-selected").textContent = label;

  document
    .querySelectorAll("#profile-menu .custom-select-option")
    .forEach((option) => {
      option.classList.remove("active");

      if (option.dataset.value === value) option.classList.add("active");
    });

  const desc = document.getElementById("profile-description");

  if (value === "standard") {
    desc.textContent =
      "Standard profile embeds only the original payload for minimal image modification.";
  } else {
    desc.textContent =
      "Robust profile increases embedding density by utilizing additional image capacity while preserving extraction accuracy.";
  }

  document.getElementById("profile-select").classList.remove("open");
}

function updatePickedFile(input, pickerId, textId, defaultText) {
  const picker = document.getElementById(pickerId);
  const text = document.getElementById(textId);

  if (input.files && input.files[0]) {
    picker.classList.add("active");
    text.textContent = input.files[0].name;
  } else {
    picker.classList.remove("active");
    text.textContent = defaultText;
  }
}

// ── ERRORS ──
function showErr(id, msg) {
  const el = document.getElementById(id);
  el.textContent = "⚠ " + msg;
  el.style.display = "block";
}
function hideErr(id) {
  document.getElementById(id).style.display = "none";
}

// ── COUNTER ANIMATION ──
function animateCount(el, target, decimals = 0, duration = 800) {
  let start = null;
  const step = (ts) => {
    if (!start) start = ts;
    const p = Math.min((ts - start) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    const val = ease * target;
    el.textContent = decimals
      ? val.toFixed(decimals)
      : Math.round(val).toLocaleString();
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// ── DROPZONE DRAG ──
document.querySelectorAll(".dropzone").forEach((dz) => {
  dz.addEventListener("dragover", (e) => {
    e.preventDefault();
    dz.classList.add("over");
  });
  dz.addEventListener("dragleave", () => dz.classList.remove("over"));
  dz.addEventListener("drop", (e) => {
    e.preventDefault();
    dz.classList.remove("over");
  });
});

// ── PASSWORD WARNING TOGGLE ──
(() => {
  const warn = document.getElementById("embed-pass-warn");
  const inp = document.getElementById("embed-password");
  if (!warn || !inp) return;
  inp.addEventListener("input", (e) => {
    warn.style.display = e.target.value ? "block" : "none";
  });
})();
