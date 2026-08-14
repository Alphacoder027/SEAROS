/* ============================================================
   SAEROS - Main JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  // ---- Sidebar Toggle ----
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (e) {
      if (window.innerWidth <= 768 &&
          sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) &&
          !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ---- Auto-dismiss alerts ----
  const alerts = document.querySelectorAll('.alert.alert-success, .alert.alert-info');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // ---- Confirm delete/reject actions ----
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  // ---- Composition total calculator ----
  const compositionFields = document.querySelectorAll('.composition-field');
  if (compositionFields.length > 0) {
    compositionFields.forEach(function (field) {
      field.addEventListener('input', updateCompositionTotal);
    });
    updateCompositionTotal();
  }

  // ---- Tooltips ----
  const tooltipEls = document.querySelectorAll('[title]');
  tooltipEls.forEach(function (el) {
    new bootstrap.Tooltip(el, { trigger: 'hover' });
  });

  // ---- Live yield prediction on composition change ----
  setupLivePrediction();

});


function updateCompositionTotal() {
  const fields = document.querySelectorAll('.composition-field');
  let total = 0;
  fields.forEach(function (f) {
    total += parseFloat(f.value) || 0;
  });

  const el = document.getElementById('totalPercent');
  if (el) {
    el.textContent = 'Total: ' + total.toFixed(1) + '%';
    if (total > 100) {
      el.className = 'fw-bold ms-2 text-danger';
    } else if (total > 90) {
      el.className = 'fw-bold ms-2 text-warning';
    } else {
      el.className = 'fw-bold ms-2 text-success';
    }
  }
}


function setupLivePrediction() {
  const predictBtn = document.getElementById('livePredictBtn');
  if (!predictBtn) return;

  predictBtn.addEventListener('click', async function () {
    const silica = document.getElementById('silica_percent')?.value;
    const iron = document.getElementById('iron_oxide_percent')?.value;
    const alumina = document.getElementById('alumina_percent')?.value;
    const moisture = document.getElementById('moisture_content')?.value;

    if (!silica || !iron || !alumina || !moisture) {
      showToast('Please fill in all composition fields first.', 'warning');
      return;
    }

    predictBtn.disabled = true;
    predictBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Predicting...';

    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          silica_percent: parseFloat(silica),
          iron_oxide_percent: parseFloat(iron),
          alumina_percent: parseFloat(alumina),
          moisture_content: parseFloat(moisture)
        })
      });

      const data = await response.json();

      if (response.ok) {
        updatePredictionDisplay(data);
      } else {
        showToast(data.error || 'Prediction failed', 'danger');
      }
    } catch (err) {
      showToast('Network error. Please try again.', 'danger');
    } finally {
      predictBtn.disabled = false;
      predictBtn.innerHTML = '<i class="bi bi-cpu me-2"></i>Get Prediction';
    }
  });
}


function updatePredictionDisplay(data) {
  const yieldEl = document.getElementById('predYield');
  const confEl = document.getElementById('predConfidence');
  const confBarEl = document.getElementById('predConfBar');
  const ratingEl = document.getElementById('predRating');
  const panelEl = document.getElementById('predictionPanel');

  if (panelEl) panelEl.style.display = 'block';
  if (yieldEl) yieldEl.textContent = data.predicted_yield + '%';
  if (confEl) confEl.textContent = data.confidence_score + '%';
  if (confBarEl) confBarEl.style.width = data.confidence_score + '%';
  if (ratingEl) {
    ratingEl.textContent = data.efficiency_rating;
    ratingEl.className = 'efficiency-badge efficiency-' +
      data.efficiency_rating.toLowerCase().replace(' ', '-');
  }
}


function showToast(message, type) {
  type = type || 'info';
  const container = document.querySelector('.flash-container') ||
                    document.querySelector('.page-content');
  if (!container) return;

  const alert = document.createElement('div');
  alert.className = `alert alert-${type} alert-dismissible fade show`;
  alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  container.insertBefore(alert, container.firstChild);

  setTimeout(function () {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
    if (bsAlert) bsAlert.close();
  }, 4000);
}


// ---- Chart.js global defaults for dark theme ----
if (typeof Chart !== 'undefined') {
  Chart.defaults.color = '#b8cfe0';           /* was #90a4b4 — brighter */
  Chart.defaults.borderColor = 'rgba(255,255,255,0.08)';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 12;
}
