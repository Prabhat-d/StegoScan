/* UI interactions, file pickers, comparison slider, and modal handlers */

const ALLOWED_IMAGE_EXTS = new Set(['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'tif']);
const PNG_ONLY_EXTS = new Set(['png']);

// Pops a red error banner at top-center of the screen — visible regardless of scroll position
function showFormatErrorToast(msg) {
  let toast = document.getElementById('format-error-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'format-error-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toast._hideTimer);
  toast._hideTimer = setTimeout(() => toast.classList.remove('show'), 4500);
}

/**
 * Validates file extension immediately on file pick.
 * allowedExts: Set of allowed extensions (default: all image types)
 * customMsg:   Optional override for the toast message
 */
function validateImageFile(input, errId, allowedExts, customMsg) {
  if (errId) hideErr(errId);
  const file = input.files[0];
  if (!file) return true;

  const exts = allowedExts || ALLOWED_IMAGE_EXTS;
  const ext = file.name.split('.').pop().toLowerCase();
  if (!exts.has(ext)) {
    const friendly = ext ? ext.toUpperCase() : 'Unknown';
    const msg = customMsg
      ? customMsg.replace('{ext}', friendly)
      : `\u274c Unsupported format: ${friendly} \u2014 please select a PNG, JPG, WEBP, or BMP image.`;
    showFormatErrorToast(msg);
    input.value = '';
    return false;
  }
  return true;
}

function toggleMobileDropdown() {
  const dd = document.getElementById("mobile-tool-dropdown");
  if (dd) dd.classList.toggle("open");
}

function selectMobileTool(name, icon, label) {
  const iconEl = document.getElementById("mobile-dropdown-selected-icon");
  const textEl = document.getElementById("mobile-dropdown-selected-text");
  if (iconEl) iconEl.textContent = icon;
  if (textEl) textEl.textContent = label;

  document.querySelectorAll(".custom-dropdown-option").forEach((opt) => opt.classList.remove("active"));
  const activeOpt = document.getElementById("opt-" + name);
  if (activeOpt) activeOpt.classList.add("active");

  const dd = document.getElementById("mobile-tool-dropdown");
  if (dd) dd.classList.remove("open");

  switchTab(name, null);
}

document.addEventListener("click", (e) => {
  const dd = document.getElementById("mobile-tool-dropdown");
  if (dd && !dd.contains(e.target)) {
    dd.classList.remove("open");
  }
});

function switchTab(name, btn) {
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));

  if (btn) {
    btn.classList.add("active");
  } else {
    const targetBtn = document.querySelector(`.tab-btn[onclick*="'${name}'"]`);
    if (targetBtn) targetBtn.classList.add("active");
  }

  const panel = document.getElementById("panel-" + name);
  if (panel) panel.classList.add("active");

  const labels = {
    embed: { icon: "🔒", label: "Embed Secret Message" },
    extract: { icon: "🔍", label: "Extract Secret Payload" },
    detect: { icon: "📊", label: "Detect Steganography" }
  };
  if (labels[name]) {
    const iconEl = document.getElementById("mobile-dropdown-selected-icon");
    const textEl = document.getElementById("mobile-dropdown-selected-text");
    if (iconEl) iconEl.textContent = labels[name].icon;
    if (textEl) textEl.textContent = labels[name].label;

    document.querySelectorAll(".custom-dropdown-option").forEach((opt) => opt.classList.remove("active"));
    const activeOpt = document.getElementById("opt-" + name);
    if (activeOpt) activeOpt.classList.add("active");
  }
}

function previewImage(input, id) {
  const file = input.files[0];
  if (!file) return;

  if (file.size > 25 * 1024 * 1024) {
    showToast("Image size must be below 25 MB");
    input.value = "";
    return;
  }

  if (!file.type.startsWith("image/")) {
    showToast("Please select a valid image file");
    input.value = "";
    return;
  }

  showToast(`✓ ${file.name} selected (${(file.size / (1024 * 1024)).toFixed(2)} MB)`);

  const el = document.getElementById(id);
  const wrap = document.getElementById(id + "-wrap");
  el.src = URL.createObjectURL(file);
  el.style.display = "block";
  if (wrap) wrap.style.display = "inline-block";
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
  if (wrap) wrap.style.display = "none";
}

function resetResults() {
  document.querySelectorAll(".result-box").forEach((box) => box.classList.remove("visible"));
  document.querySelectorAll(".err").forEach((err) => (err.style.display = "none"));

  const success = document.getElementById("embed-success");
  if (success) success.style.display = "none";
}

function resetEmbedForm() {
  resetResults();
  document.getElementById("embed-msg").value = "";
  document.getElementById("embed-password").value = "";
  document.getElementById("secret-file").value = "";
  document.getElementById("secret-image").value = "";

  document.getElementById("hidden-file-info").style.display = "none";
  document.getElementById("hidden-image-info").style.display = "none";
  document.getElementById("hidden-image-wrap").style.display = "none";

  selectedPayloadMB = 0;
  document.getElementById("embedding-profile").value = "standard";
  document.getElementById("profile-selected").textContent = "Standard";
  document.getElementById("profile-description").textContent =
    "Standard profile embeds only the original payload for minimal image modification.";
  document.getElementById("embed-success").style.display = "none";
}

function toggleHideType() {
  const type = document.getElementById("hide-type").value;
  document.getElementById("hide-text-block").style.display = type === "text" ? "block" : "none";
  document.getElementById("hide-file-block").style.display = type === "file" ? "block" : "none";
  document.getElementById("hide-image-block").style.display = type === "image" ? "block" : "none";
}

function toggleCustomSelect() {
  document.getElementById("hide-type-select").classList.toggle("open");
}

function selectHideType(value, label) {
  document.getElementById("hide-type").value = value;
  document.getElementById("hide-type-selected").textContent = label;

  document.querySelectorAll(".custom-select-option").forEach((option) => {
    option.classList.remove("active");
    if (option.dataset.value === value) option.classList.add("active");
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
  box.innerHTML = `📄 ${file.name}<br>Size: ${mb.toFixed(2)} MB`;
}

function showHiddenImage(input) {
  const file = input.files[0];
  if (!file) return;
  const mb = (file.size * 1.35) / (1024 * 1024);
  selectedPayloadMB = mb;
  document.getElementById("hidden-image-info").style.display = "block";
  document.getElementById("hidden-image-info").innerHTML = `🖼️ ${file.name}<br>Size: ${mb.toFixed(2)} MB`;

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

  document.querySelectorAll("#profile-menu .custom-select-option").forEach((option) => {
    option.classList.remove("active");
    if (option.dataset.value === value) option.classList.add("active");
  });

  const desc = document.getElementById("profile-description");
  if (value === "standard") {
    desc.textContent = "Standard profile embeds only the original payload sequentially for minimal image modification.";
  } else {
    desc.textContent = "Robust profile uses Keyed PRNG Bit Scattering to distribute payload bits across the whole image, evading spatial region detectors.";
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

function showErr(id, msg) {
  const el = document.getElementById(id);
  el.textContent = "⚠ " + msg;
  el.style.display = "block";
}

function hideErr(id) {
  document.getElementById(id).style.display = "none";
}

function animateCount(el, target, decimals = 0, duration = 800) {
  let start = null;
  const step = (ts) => {
    if (!start) start = ts;
    const p = Math.min((ts - start) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    const val = ease * target;
    el.textContent = decimals ? val.toFixed(decimals) : Math.round(val).toLocaleString();
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

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

(() => {
  const warn = document.getElementById("embed-pass-warn");
  const inp = document.getElementById("embed-password");
  if (!warn || !inp) return;
  inp.addEventListener("input", (e) => {
    warn.style.display = e.target.value ? "block" : "none";
  });
})();

// Interactive stego comparison slider
function setupComparisonSlider() {
  const container = document.getElementById("stego-slider-container");
  const overlay = document.getElementById("stego-slider-overlay");
  const handle = document.getElementById("stego-slider-handle");

  if (!container || !overlay || !handle) return;

  let isDragging = false;
  const moveSlider = (clientX) => {
    const rect = container.getBoundingClientRect();
    let x = clientX - rect.left;
    x = Math.max(0, Math.min(x, rect.width));
    const pct = (x / rect.width) * 100;
    overlay.style.width = pct + "%";
    handle.style.left = pct + "%";
  };

  handle.addEventListener("mousedown", () => (isDragging = true));
  window.addEventListener("mouseup", () => (isDragging = false));
  window.addEventListener("mousemove", (e) => {
    if (isDragging) moveSlider(e.clientX);
  });

  handle.addEventListener("touchstart", () => (isDragging = true));
  window.addEventListener("touchend", () => (isDragging = false));
  window.addEventListener("touchmove", (e) => {
    if (isDragging && e.touches[0]) moveSlider(e.touches[0].clientX);
  });
}

function updateClock() {
  const clock = document.getElementById("live-clock");
  if (!clock) return;
  const now = new Date();
  clock.textContent = now.toLocaleTimeString("en-IN", { hour12: false });
}

setInterval(updateClock, 1000);
updateClock();
document.addEventListener("DOMContentLoaded", setupComparisonSlider);

// Modal overlay triggers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("active");
    document.body.style.overflow = "hidden";
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("active");
    document.body.style.overflow = "";
  }
}

function closeModalOnOverlay(e, modalId) {
  if (e.target.classList.contains("modal-overlay")) {
    closeModal(modalId);
  }
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-overlay.active").forEach((m) => {
      m.classList.remove("active");
    });
    document.body.style.overflow = "";
  }
});

// ─── Drag & Drop Engine ──────────────────────────────────────────────────────
// Config for each dropzone: which input to populate, what to validate, what to run after drop
const DROPZONE_CONFIGS = [
  {
    zoneId:   "embed-drop",
    inputId:  "embed-file",
    errId:    "embed-err",
    allowedExts: ALLOWED_IMAGE_EXTS,
    customMsg: null,
    onDrop: (input) => {
      if (!validateImageFile(input, "embed-err")) return;
      resetResults();
      previewImage(input, "embed-prev");
      showImageCapacity(input);
    }
  },
  {
    zoneId:   "extract-drop",
    inputId:  "extract-file",
    errId:    "extract-err",
    allowedExts: PNG_ONLY_EXTS,
    customMsg: "❌ Extract requires a PNG image — {ext} files use lossy compression that destroys hidden data.",
    onDrop: (input) => {
      if (!validateImageFile(input, "extract-err", PNG_ONLY_EXTS,
        "❌ Extract requires a PNG image — {ext} files use lossy compression that destroys hidden data.")) return;
      resetResults();
      previewImage(input, "extract-prev");
    }
  },
  {
    zoneId:   "detect-drop",
    inputId:  "detect-file",
    errId:    "detect-err",
    allowedExts: ALLOWED_IMAGE_EXTS,
    customMsg: null,
    onDrop: (input) => {
      if (!validateImageFile(input, "detect-err")) return;
      resetResults();
      previewImage(input, "detect-prev");
    }
  }
];

function initDropzones() {
  DROPZONE_CONFIGS.forEach(({ zoneId, inputId, onDrop }) => {
    const zone  = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    if (!zone || !input) return;

    // Prevent browser default of opening the file in a new tab
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.stopPropagation();
      zone.classList.add("over");
    });

    zone.addEventListener("dragenter", (e) => {
      e.preventDefault();
      e.stopPropagation();
      zone.classList.add("over");
    });

    zone.addEventListener("dragleave", (e) => {
      // Only remove highlight when cursor truly leaves the zone (not a child element)
      if (!zone.contains(e.relatedTarget)) {
        zone.classList.remove("over");
      }
    });

    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      e.stopPropagation();
      zone.classList.remove("over");

      const files = e.dataTransfer.files;
      if (!files || files.length === 0) return;

      // Inject the dropped file into the hidden <input> so onDrop callbacks work normally
      const dt = new DataTransfer();
      dt.items.add(files[0]);
      input.files = dt.files;

      onDrop(input);
    });
  });
}

// Initialise after DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initDropzones);
} else {
  initDropzones();
}
