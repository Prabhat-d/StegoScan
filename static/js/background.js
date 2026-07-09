// ============================================
// CANVAS BACKGROUND ANIMATION
// ============================================

// ── CANVAS BACKGROUND ──
let selectedPayloadMB = 0;
const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");
let W,
  H,
  particles = [],
  orbits = [];

function resize() {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
}

function initParticles() {
  particles = [];
  const count = Math.floor((W * H) / 14000);
  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 2 + 0.8,
      a: Math.random() * 0.5 + 0.35,
    });
  }

  // glowing orbit circles

  orbits = [];

  for (let i = 0; i < 5; i++) {
    orbits.push({
      x: Math.random() * W,

      y: Math.random() * H,

      radius: Math.random() * 80 + 80,

      angle: Math.random() * Math.PI * 2,

      speed: 0.002 + Math.random() * 0.002,
    });
  }
}

function drawParticles() {
  ctx.clearRect(0, 0, W, H);

  // draw orbit systems

  for (let o of orbits) {
    o.angle += o.speed;

    ctx.beginPath();

    ctx.arc(o.x, o.y, o.radius, 0, Math.PI * 2);

    ctx.strokeStyle = "rgba(157,127,212,0.15)";

    ctx.lineWidth = 1;

    ctx.stroke();

    // orbiting star

    const px = o.x + Math.cos(o.angle) * o.radius;

    const py = o.y + Math.sin(o.angle) * o.radius;

    ctx.beginPath();

    ctx.arc(px, py, 3, 0, Math.PI * 2);

    ctx.fillStyle = "rgba(0,229,160,0.8)";

    ctx.shadowBlur = 15;

    ctx.shadowColor = "rgba(0,229,160,1)";

    ctx.fill();

    ctx.shadowBlur = 0;
  }

  for (let p of particles) {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0 || p.x > W) p.vx *= -1;
    if (p.y < 0 || p.y > H) p.vy *= -1;

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    const glow = p.a + Math.sin(Date.now() * 0.003 + p.x) * 0.2;

    ctx.fillStyle = `rgba(157,127,212,${glow})`;
    ctx.fill();
  }

  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < 120) {
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = `rgba(157,127,212,${0.35 * (1 - d / 120)})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }
    }
  }
  requestAnimationFrame(drawParticles);
}

resize();
initParticles();
drawParticles();
window.addEventListener("resize", () => {
  resize();
  initParticles();
});
