const input = document.getElementById('audioInput');
const dropzone = document.getElementById('dropzone');
const analyzeBtn = document.getElementById('analyzeBtn');
const filenameEl = document.getElementById('filename');
const resultCard = document.getElementById('resultCard');
const errorCard = document.getElementById('errorCard');
const riskBar = document.getElementById('riskBar');
const riskLabel = document.getElementById('riskLabel');
const digitalList = document.getElementById('digitalList');
const bioList = document.getElementById('bioList');
const rawJson = document.getElementById('rawJson');
const apiBaseInput = document.getElementById('apiBaseInput');
const saveApiBaseBtn = document.getElementById('saveApiBaseBtn');
const apiHint = document.getElementById('apiHint');

let selectedFile = null;

function normalizeApiBase(url) {
  const trimmed = (url || '').trim();
  if (!trimmed) return '';
  return trimmed.replace(/\/$/, '');
}

function getApiBase() {
  const fromQuery = new URLSearchParams(window.location.search).get('api');
  if (fromQuery) {
    return normalizeApiBase(fromQuery);
  }

  const fromStorage = localStorage.getItem('aft_api_base');
  if (fromStorage) {
    return normalizeApiBase(fromStorage);
  }

  return normalizeApiBase(window.AFT_API_BASE || '');
}

function setApiHint(base) {
  if (!base) {
    apiHint.textContent = 'Using same-origin API (default). For GitHub Pages set your hosted API URL.';
  } else {
    apiHint.textContent = `Using API endpoint: ${base}`;
  }
}

function apiUrl(path) {
  const base = getApiBase();
  return base ? `${base}${path}` : path;
}

function saveApiBase() {
  const normalized = normalizeApiBase(apiBaseInput.value);
  localStorage.setItem('aft_api_base', normalized);
  apiBaseInput.value = normalized;
  setApiHint(normalized);
}

apiBaseInput.value = getApiBase();
setApiHint(getApiBase());
saveApiBaseBtn.addEventListener('click', saveApiBase);

const preventDefaults = (event) => {
  event.preventDefault();
  event.stopPropagation();
};

['dragenter', 'dragover', 'dragleave', 'drop'].forEach((evt) => {
  dropzone.addEventListener(evt, preventDefaults);
});

['dragenter', 'dragover'].forEach((evt) => {
  dropzone.addEventListener(evt, () => dropzone.classList.add('dragging'));
});

['dragleave', 'drop'].forEach((evt) => {
  dropzone.addEventListener(evt, () => dropzone.classList.remove('dragging'));
});

dropzone.addEventListener('drop', (event) => {
  const file = event.dataTransfer?.files?.[0];
  setFile(file);
});

input.addEventListener('change', () => {
  setFile(input.files?.[0]);
});

analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) {
    return;
  }

  errorCard.classList.add('hidden');
  resultCard.classList.add('hidden');
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = 'Analyzing...';

  const formData = new FormData();
  formData.append('audio_file', selectedFile);

  try {
    const response = await fetch(apiUrl('/api/analyze'), {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Analysis failed.');
    }

    renderReport(data);
  } catch (err) {
    showError(err.message || 'Analysis failed. If hosted on GitHub Pages, configure API Base URL.');
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Analyze Audio';
  }
});

function setFile(file) {
  selectedFile = file || null;
  if (selectedFile) {
    filenameEl.textContent = selectedFile.name;
    analyzeBtn.disabled = false;
  } else {
    filenameEl.textContent = 'No file selected';
    analyzeBtn.disabled = true;
  }
}

function renderReport(report) {
  const risk = Number(report.overall_fraud_risk || 0);
  riskBar.style.width = `${Math.max(0, Math.min(100, risk * 100))}%`;
  riskLabel.textContent = `Overall Fraud Risk: ${(risk * 100).toFixed(1)}%`;

  digitalList.innerHTML = '';
  bioList.innerHTML = '';

  addItem(digitalList, `SHA-256: ${report.digital.sha256}`);
  addItem(digitalList, `Sample Rate: ${report.digital.sample_rate} Hz`);
  addItem(digitalList, `Duration: ${report.digital.duration_seconds.toFixed(2)} s`);
  addItem(digitalList, `Integrity Risk: ${(report.digital.integrity_risk * 100).toFixed(1)}%`);
  (report.digital.metadata_flags || []).forEach((flag) => addItem(digitalList, `⚠️ ${flag}`));

  addItem(bioList, `Zero Crossing Rate: ${report.biological.zero_crossing_rate.toFixed(4)}`);
  addItem(bioList, `Energy Variation: ${report.biological.energy_variation.toFixed(4)}`);
  addItem(bioList, `Voiced Segment Ratio: ${(report.biological.voiced_segment_ratio * 100).toFixed(1)}%`);
  addItem(bioList, `Human Likeness: ${(report.biological.human_likeness * 100).toFixed(1)}%`);
  (report.biological.biometric_flags || []).forEach((flag) => addItem(bioList, `⚠️ ${flag}`));

  rawJson.textContent = JSON.stringify(report, null, 2);
  resultCard.classList.remove('hidden');
}

function addItem(parent, text) {
  const li = document.createElement('li');
  li.textContent = text;
  parent.appendChild(li);
}

function showError(message) {
  errorCard.textContent = message;
  errorCard.classList.remove('hidden');
}
