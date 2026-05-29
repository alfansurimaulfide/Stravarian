// ChessgRunts — Main JS

// Auto-dismiss flash messages
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => el.remove());
}, 5000);

// Format seconds to mm:ss
function fmtTime(secs) {
  if (!secs) return '—';
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  return `${m}:${String(s).padStart(2,'0')}`;
}

// Format pace (sec/km) to min:sec/km
function fmtPace(secPerKm) {
  if (!secPerKm) return '—';
  const m = Math.floor(secPerKm / 60);
  const s = Math.round(secPerKm % 60);
  return `${m}:${String(s).padStart(2,'0')}/km`;
}

// Format distance
function fmtDist(meters) {
  if (!meters) return '—';
  return (meters / 1000).toFixed(2) + ' km';
}

// Animate numbers
function animateNumber(el, to, decimals = 0, suffix = '') {
  const from = 0;
  const duration = 800;
  const start = performance.now();
  const update = (now) => {
    const t = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - t, 3);
    el.textContent = (from + (to - from) * ease).toFixed(decimals) + suffix;
    if (t < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

// Animate all stat values on load
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-animate]').forEach(el => {
    const val = parseFloat(el.dataset.animate);
    const dec = parseInt(el.dataset.decimals || 0);
    const suf = el.dataset.suffix || '';
    animateNumber(el, val, dec, suf);
  });

  // Progress bars
  document.querySelectorAll('.progress-fill[data-width]').forEach(el => {
    setTimeout(() => { el.style.width = el.dataset.width + '%'; }, 100);
  });
});
