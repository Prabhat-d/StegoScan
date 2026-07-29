// ============================================
// CANVAS BACKGROUND ANIMATION (INTERACTIVE CYBER MESH)
// ============================================

let selectedPayloadMB = 0;
const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");
let W, H, particles = [], orbits = [];
let mouse = { x: null, y: null, radius: 150 };

window.addEventListener("mousemove", (e) => {
  mouse.x = e.clientX;
  mouse.y = e.clientY;
});

window.addEventListener("mouseleave", () => {
  mouse.x = null;
  mouse.y = null;
});

function resize() {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
}

function initParticles() {
  particles = [];
  // Cap count for optimal 60fps performance
  const count = Math.min(Math.floor((W * H) / 16000), 100);
  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      baseX: Math.random() * W,
      baseY: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 2 + 0.8,
      a: Math.random() * 0.4 + 0.3,
    });
  }

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

  // Draw subtle cyber grid overlay
  ctx.strokeStyle = "rgba(123, 94, 167, 0.03)";
  ctx.lineWidth = 1;
  const gridSize = 60;
  for (let x = 0; x < W; x += gridSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H);
    ctx.stroke();
  }
  for (let y = 0; y < H; y += gridSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }

  // Orbit systems
  for (let o of orbits) {
    o.angle += o.speed;
    ctx.beginPath();
    ctx.arc(o.x, o.y, o.radius, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(157,127,212,0.12)";
    ctx.lineWidth = 1;
    ctx.stroke();

    const px = o.x + Math.cos(o.angle) * o.radius;
    const py = o.y + Math.sin(o.angle) * o.radius;
    ctx.beginPath();
    ctx.arc(px, py, 3, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0,229,160,0.85)";
    ctx.shadowBlur = 12;
    ctx.shadowColor = "rgba(0,229,160,1)";
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  // Update & Draw particles
  for (let p of particles) {
    p.x += p.vx;
    p.y += p.vy;

    if (p.x < 0 || p.x > W) p.vx *= -1;
    if (p.y < 0 || p.y > H) p.vy *= -1;

    // Mouse interaction (repel)
    if (mouse.x !== null && mouse.y !== null) {
      let dx = mouse.x - p.x;
      let dy = mouse.y - p.y;
      let dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < mouse.radius) {
        let force = (mouse.radius - dist) / mouse.radius;
        let angle = Math.atan2(dy, dx);
        p.x -= Math.cos(angle) * force * 3;
        p.y -= Math.sin(angle) * force * 3;
      }
    }

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    const glow = p.a + Math.sin(Date.now() * 0.003 + p.x) * 0.2;
    ctx.fillStyle = `rgba(157,127,212,${glow})`;
    ctx.fill();
  }

  // Optimized distance connections (using distance threshold cap)
  const maxDist = 110;
  const maxDistSq = maxDist * maxDist;
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const distSq = dx * dx + dy * dy;
      if (distSq < maxDistSq) {
        const dist = Math.sqrt(distSq);
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = `rgba(157,127,212,${0.3 * (1 - dist / maxDist)})`;
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
