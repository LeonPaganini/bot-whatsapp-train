const API_BASE = window.API_BASE || localStorage.getItem('apiBase') || '';

function saveWhatsapp(value) {
  localStorage.setItem('whatsapp_e164', value);
}

function getWhatsapp() {
  return localStorage.getItem('whatsapp_e164') || '';
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return response.json();
}

function setupCadastro() {
  const form = document.querySelector('#cadastro-form');
  if (!form) return;
  form.whatsapp_e164.value = getWhatsapp();
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
      nome: form.nome.value,
      whatsapp_e164: form.whatsapp_e164.value,
      sexo: form.sexo.value,
      altura_cm: Number(form.altura_cm.value),
      personal_id: form.personal_id.value || 'default',
    };
    const data = await postJson(`${API_BASE}/api/register`, payload);
    saveWhatsapp(form.whatsapp_e164.value);
    alert(`Cadastro: ${data.status}`);
  });
}

function setupMedidas() {
  const form = document.querySelector('#medidas-form');
  if (!form) return;
  form.whatsapp_e164.value = getWhatsapp();
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
      whatsapp_e164: form.whatsapp_e164.value,
      data: form.data.value,
      peso_kg: Number(form.peso_kg.value),
      cintura_cm: Number(form.cintura_cm.value),
      pescoco_cm: Number(form.pescoco_cm.value),
      quadril_cm: form.quadril_cm.value ? Number(form.quadril_cm.value) : null,
    };
    const data = await postJson(`${API_BASE}/api/measurements`, payload);
    saveWhatsapp(form.whatsapp_e164.value);
    alert(`BF%: ${data.bf_percent?.toFixed(2)}`);
  });
}

function buildLineChart(ctx, label, labels, data, color) {
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{ label, data, borderColor: color, fill: false }],
    },
  });
}

async function setupDashboard() {
  const container = document.querySelector('#dashboard');
  if (!container) return;
  const whatsapp = getWhatsapp();
  if (!whatsapp) {
    container.innerHTML = '<p>Cadastre um WhatsApp primeiro.</p>';
    return;
  }
  const response = await fetch(`${API_BASE}/api/dashboard?whatsapp_e164=${encodeURIComponent(whatsapp)}`);
  const payload = await response.json();
  const data = payload.data || {};

  const pesoLabels = data.peso?.map((item) => item.data) || [];
  const pesoValues = data.peso?.map((item) => item.peso) || [];
  buildLineChart(document.querySelector('#peso-chart'), 'Peso (kg)', pesoLabels, pesoValues, '#1e88e5');

  const bfLabels = data.bf?.map((item) => item.data) || [];
  const bfValues = data.bf?.map((item) => item.bf) || [];
  buildLineChart(document.querySelector('#bf-chart'), 'BF%', bfLabels, bfValues, '#e53935');

  const ffmValues = data.bf?.map((item) => item.ffm) || [];
  buildLineChart(document.querySelector('#ffm-chart'), 'Massa magra', bfLabels, ffmValues, '#43a047');

  const volSemLabels = data.volume_semanal?.map((item) => item.semana) || [];
  const volSemValues = data.volume_semanal?.map((item) => item.volume) || [];
  buildLineChart(document.querySelector('#volume-semanal'), 'Volume semanal', volSemLabels, volSemValues, '#8e24aa');

  const consLabels = data.consistencia?.map((item) => item.semana) || [];
  const consValues = data.consistencia?.map((item) => item.treinos) || [];
  buildLineChart(document.querySelector('#consistencia'), 'Treinos/semana', consLabels, consValues, '#fb8c00');

  const exercicioSelect = document.querySelector('#exercicio-select');
  const exercicios = data.exercicios_disponiveis || [];
  exercicios.forEach((nome) => {
    const option = document.createElement('option');
    option.value = nome;
    option.textContent = nome;
    exercicioSelect.appendChild(option);
  });

  function updateExerciseChart(nome) {
    const series = data.cargas?.[nome] || [];
    const labels = series.map((item) => item.data);
    const values = series.map((item) => item.load);
    buildLineChart(document.querySelector('#carga-exercicio'), `Carga - ${nome}`, labels, values, '#3949ab');
  }

  exercicioSelect.addEventListener('change', (event) => {
    updateExerciseChart(event.target.value);
  });
  if (exercicios.length > 0) {
    updateExerciseChart(exercicios[0]);
  }

  const strengthLabels = data.strength_index?.map((item) => item.semana) || [];
  const strengthValues = data.strength_index?.map((item) => item.value) || [];
  buildLineChart(
    document.querySelector('#strength-index'),
    'Strength Index',
    strengthLabels,
    strengthValues,
    '#6d4c41'
  );
}

document.addEventListener('DOMContentLoaded', () => {
  setupCadastro();
  setupMedidas();
  setupDashboard();
});
