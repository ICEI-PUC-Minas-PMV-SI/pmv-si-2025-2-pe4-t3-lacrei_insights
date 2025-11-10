// no início do graficos.js
Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
Chart.defaults.color = "#333";

function getDatasetsFromDOM() {
  const el = document.getElementById('datasets-json');
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch (e) {
    console.error('Falha ao parsear datasets-json:', e);
    return null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const D = getDatasetsFromDOM();
  if (!D) {
    console.error('DATASETS ausente. Verifique a injeção no graficos.html e o render_template.');
    return;
  }

  const yRight = (id, title) => ({
    id, position: 'right', grid: { drawOnChartArea:false }, title: { display:true, text:title }
  });
  const yLeft  = (id, title) => ({
    id, position: 'left', title: { display:true, text:title }
  });

  // --- Pacientes por mês ---
  const ctxMonth = document.getElementById('cPatientsMonth');
  if (ctxMonth) new Chart(ctxMonth, {
    type: 'bar',
    data: {
      labels: D.patients_month.labels,
      datasets: [
        { type:'bar', label:'Total de pacientes', data: D.patients_month.totals, yAxisID:'y1' },
        { type:'line', label:'% ativos (média)', data: D.patients_month.active_pct, yAxisID:'y2' }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: { y1: yLeft('y1', 'Total'), y2: yRight('y2', '% Ativos') }
    }
  });

  // --- Faixa etária ---
  const lbAge = document.getElementById('lbAgeMonth');
  if (lbAge) lbAge.textContent = D.patients_age.last_month ? `Mês: ${D.patients_age.last_month}` : 'Sem dados';
  const ctxAge = document.getElementById('cPatientsAge');
  if (ctxAge) new Chart(ctxAge, {
    type: 'bar',
    data: {
      labels: D.patients_age.labels,
      datasets: [
        { type:'bar', label:'Total de pacientes', data: D.patients_age.totals, yAxisID:'y1' },
        { type:'line', label:'% ativos (média)', data: D.patients_age.active_pct, yAxisID:'y2' }
      ]
    },
    options: {
      responsive: true,
      scales: { y1: yLeft('y1', 'Total'), y2: yRight('y2', '% Ativos') }
    }
  });

  // --- Tipos de deficiência ---
  const lbDis = document.getElementById('lbDisabMonth');
  if (lbDis) lbDis.textContent = D.disability.last_month ? `Mês: ${D.disability.last_month}` : 'Sem dados';
  const ctxDis = document.getElementById('cDisability');
  if (ctxDis) new Chart(ctxDis, {
    type: 'bar',
    data: { labels: D.disability.labels, datasets: [{ label:'Pacientes', data: D.disability.totals }] },
    options: { responsive: true, indexAxis: 'y' }
  });

  // --- Especialidades ---
  const ctxSpec = document.getElementById('cProfSpec');
  if (ctxSpec) new Chart(ctxSpec, {
    type: 'bar',
    data: {
      labels: D.prof_spec.labels,
      datasets: [
        { type:'bar', label:'Atendimentos', data: D.prof_spec.totals, yAxisID:'y1' },
        { type:'line', label:'Média de nota', data: D.prof_spec.avg_rating, yAxisID:'y2' }
      ]
    },
    options: {
      responsive: true,
      scales: { y1: yLeft('y1', 'Atendimentos'), y2: yRight('y2', 'Média de nota') }
    }
  });

  // --- Série de atendimentos ---
  const ctxSeries = document.getElementById('cProfSeries');
  if (ctxSeries) new Chart(ctxSeries, {
    type: 'bar',
    data: {
      labels: D.prof_series.labels,
      datasets: [
        { type:'bar', label:'Atendimentos', data: D.prof_series.totals, yAxisID:'y1' },
        { type:'line', label:'% concluídos (média)', data: D.prof_series.completion, yAxisID:'y2' }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: { y1: yLeft('y1', 'Atendimentos'), y2: yRight('y2', '% Conclusão') }
    }
  });
});
