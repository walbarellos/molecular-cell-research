/**
 * CELL LAB — Scientific Systems Exploration Platform (SSEP)
 * Academic Interactive Dashboard Frontend Controller (L7 Web)
 * STRICT REQUIREMENT: ZERO EMOJIS ANYWHERE
 */

// Estado Global da Aplicacao
const State = {
  atp: 1000.0,
  load: 0.0,
  temp: 24.0,
  model: 'MOD-KIF5B-4STATE-FORCE-DEPENDENT',
  kinesinSimData: null,
  animationId: null,
  stepPhase: 0.0,
  motorX: 120.0,
  towSimData: null,
  langSimData: null,
  provenanceData: null,
};

// ============================================================================
// Inicializacao e Navegacao
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupKinesinControls();
  setupTugOfWarControls();
  setupLangevinControls();
  startSteppingAnimation();
  
  // Dispara primeira simulacao do motor
  fetchKinesinSimulation();
  fetchProvenanceGraph();
  drawDiscriminatorMatrix();

  // Atualiza relogio
  const clockEl = document.getElementById('clockDisplay');
  if (clockEl) {
    const now = new Date();
    clockEl.textContent = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  }
});

function setupTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      const pane = document.getElementById(targetId);
      if (pane) pane.classList.add('active');

      // Redesenha plots na troca de aba
      if (targetId === 'tab-tug-of-war' && !State.towSimData) {
        runTugOfWarSimulation();
      } else if (targetId === 'tab-langevin' && !State.langSimData) {
        runLangevinSimulation();
      } else if (targetId === 'tab-provenance') {
        drawProvenanceGraph();
      } else if (targetId === 'tab-design') {
        drawDiscriminatorMatrix();
      }
    });
  });
}

// ============================================================================
// Tab 1: Kinesin Mechanochemistry Controls & Simulation
// ============================================================================
function setupKinesinControls() {
  const sliderAtp = document.getElementById('sliderAtp');
  const sliderLoad = document.getElementById('sliderLoad');
  const sliderTemp = document.getElementById('sliderTemp');
  const selectModel = document.getElementById('selectModel');

  const valAtp = document.getElementById('valAtp');
  const valLoad = document.getElementById('valLoad');
  const valTemp = document.getElementById('valTemp');

  sliderAtp.addEventListener('input', (e) => {
    State.atp = parseFloat(e.target.value);
    valAtp.textContent = State.atp.toFixed(1) + ' μM';
    fetchKinesinSimulation();
  });

  sliderLoad.addEventListener('input', (e) => {
    State.load = parseFloat(e.target.value);
    valLoad.textContent = State.load.toFixed(2) + ' pN';
    fetchKinesinSimulation();
  });

  sliderTemp.addEventListener('input', (e) => {
    State.temp = parseFloat(e.target.value);
    valTemp.textContent = State.temp.toFixed(1) + ' °C';
    fetchKinesinSimulation();
  });

  selectModel.addEventListener('change', (e) => {
    State.model = e.target.value;
    fetchKinesinSimulation();
  });

  // Presets
  document.getElementById('btnPresetValid').addEventListener('click', () => {
    sliderAtp.value = 1000;
    sliderLoad.value = 0.0;
    selectModel.value = 'MOD-KIF5B-MINIMAL-MM';
    State.atp = 1000.0;
    State.load = 0.0;
    State.model = selectModel.value;
    valAtp.textContent = '1000.0 μM';
    valLoad.textContent = '0.00 pN';
    fetchKinesinSimulation();
  });

  document.getElementById('btnPresetFalsified').addEventListener('click', () => {
    sliderAtp.value = 1000;
    sliderLoad.value = 4.0;
    selectModel.value = 'MOD-KIF5B-MINIMAL-MM';
    State.atp = 1000.0;
    State.load = 4.0;
    State.model = selectModel.value;
    valAtp.textContent = '1000.0 μM';
    valLoad.textContent = '4.00 pN';
    fetchKinesinSimulation();
  });

  document.getElementById('btnPresetStall').addEventListener('click', () => {
    sliderAtp.value = 1000;
    sliderLoad.value = 6.0;
    selectModel.value = 'MOD-KIF5B-4STATE-FORCE-DEPENDENT';
    State.atp = 1000.0;
    State.load = 6.0;
    State.model = selectModel.value;
    valAtp.textContent = '1000.0 μM';
    valLoad.textContent = '6.00 pN';
    fetchKinesinSimulation();
  });
}

let kinesinDebounceTimer = null;
function fetchKinesinSimulation() {
  clearTimeout(kinesinDebounceTimer);
  kinesinDebounceTimer = setTimeout(async () => {
    try {
      const resp = await fetch('/api/simulate/kinesin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          atp_uM: State.atp,
          load_pN: State.load,
          model_id: State.model,
        })
      });
      const data = await resp.json();
      State.kinesinSimData = data;
      updateKinesinUI(data);
    } catch (err) {
      console.error('Erro na simulacao de kinesina:', err);
    }
  }, 40);
}

function updateKinesinUI(data) {
  const op = data.curves.operating_point;
  const user = data.user_state;

  document.getElementById('dispVelM2').textContent = op.velocity_m2_um_s.toFixed(3) + ' μm/s';
  document.getElementById('dispVelM1').textContent = op.velocity_m1_um_s.toFixed(3) + ' μm/s';
  document.getElementById('dispOperState').textContent = user.operational_state;

  const stepRate = (op.velocity_m2_um_s * 1000.0 / 8.2).toFixed(1);
  document.getElementById('steppingRateLabel').textContent = `Taxa: ${stepRate} passos/s (v = ${op.velocity_m2_um_s.toFixed(3)} μm/s)`;

  // Atualiza Firewall Epistemico
  const headerFirewall = document.getElementById('headerFirewallBadge');
  const alertValid = document.getElementById('firewallAlertValid');
  const alertDanger = document.getElementById('firewallAlertDanger');
  const alertText = document.getElementById('firewallAlertText');

  if (user.is_within_validated_envelope) {
    headerFirewall.className = 'badge-tag validated';
    headerFirewall.textContent = '[EPISTEMIC::VALIDATED]';
    alertValid.style.display = 'block';
    alertDanger.style.display = 'none';
  } else {
    headerFirewall.className = 'badge-tag refuted';
    headerFirewall.textContent = '[FIREWALL::ENGAGED]';
    alertValid.style.display = 'none';
    alertDanger.style.display = 'block';
    alertText.textContent = user.epistemic_warning || 'Operacao fora dos limites empiricamente validados.';
  }

  // Desenha os dois plots
  drawForceVelocityPlot(data);
  drawMichaelisMentenPlot(data);
}

// ============================================================================
// Stepping Animation Engine
// ============================================================================
function startSteppingAnimation() {
  const canvas = document.getElementById('canvasStepping');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Velocidade em nm/s
    const vel_um_s = State.kinesinSimData ? State.kinesinSimData.curves.operating_point.velocity_m2_um_s : 0.778;
    const speedFactor = Math.max(0.0, vel_um_s) * 0.08;
    State.stepPhase = (State.stepPhase + speedFactor) % (Math.PI * 2);

    // 1. Desenha Microtubulo (Dimeros alpha/beta tubulina)
    const trackY = 110;
    const dimerWidth = 36;
    const numDimers = Math.ceil(canvas.width / dimerWidth) + 2;

    for (let i = 0; i < numDimers; i++) {
      const x = i * dimerWidth;
      // Alpha tubulina
      ctx.fillStyle = '#0e7490';
      ctx.beginPath();
      ctx.roundRect(x, trackY, 16, 24, 4);
      ctx.fill();
      ctx.strokeStyle = '#155e75';
      ctx.stroke();

      // Beta tubulina
      ctx.fillStyle = '#1e3a8a';
      ctx.beginPath();
      ctx.roundRect(x + 18, trackY, 16, 24, 4);
      ctx.fill();
      ctx.strokeStyle = '#1d4ed8';
      ctx.stroke();

      // Marcacao do passo de 8.2 nm
      if (i % 2 === 0) {
        ctx.fillStyle = '#475569';
        ctx.font = '8px monospace';
        ctx.fillText('8.2nm', x + 6, trackY + 36);
      }
    }

    // 2. Kinesina Motor Heads & Neck Linkers
    const baseX = 380;
    const headRadius = 8;
    
    // Angulos oscilatorios mecanoquimicos
    const angle1 = Math.sin(State.stepPhase) * 0.6;
    const angle2 = Math.sin(State.stepPhase + Math.PI) * 0.6;

    const head1X = baseX + Math.sin(angle1) * 22;
    const head1Y = trackY - headRadius;
    const head2X = baseX + Math.sin(angle2) * 22 + 18;
    const head2Y = trackY - headRadius;

    const stalkX = baseX + 9;
    const stalkY = trackY - 50;

    // Stalk (coiled-coil) e Cargo Bead
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(head1X, head1Y);
    ctx.lineTo(stalkX, stalkY);
    ctx.lineTo(head2X, head2Y);
    ctx.stroke();

    // Cargo Bead (Poliestireno em Pinca Optica)
    const beadRadius = 20;
    const beadX = stalkX;
    const beadY = stalkY - beadRadius - 2;

    ctx.fillStyle = 'rgba(56, 189, 248, 0.25)';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(beadX, beadY, beadRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#f8fafc';
    ctx.font = '9px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('CARGO', beadX, beadY + 3);

    // Cabecas cataliticas
    // Head 1 (Leading)
    ctx.fillStyle = '#38bdf8';
    ctx.beginPath();
    ctx.arc(head1X, head1Y, headRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#0284c7';
    ctx.stroke();

    // Head 2 (Trailing)
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath();
    ctx.arc(head2X, head2Y, headRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#d97706';
    ctx.stroke();

    // Vetor de Forca Contraria F_load
    if (State.load > 0) {
      const arrowLen = Math.min(80, State.load * 12);
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(beadX, beadY);
      ctx.lineTo(beadX - arrowLen, beadY);
      ctx.stroke();

      // Seta ponta
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.moveTo(beadX - arrowLen, beadY);
      ctx.lineTo(beadX - arrowLen + 6, beadY - 4);
      ctx.lineTo(beadX - arrowLen + 6, beadY + 4);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = '#ef4444';
      ctx.font = '10px monospace';
      ctx.textAlign = 'right';
      ctx.fillText(`F_load = ${State.load.toFixed(1)} pN`, beadX - arrowLen - 6, beadY + 3);
    }

    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);
}

// ============================================================================
// Scientific Canvas Plotting (Force-Velocity & Michaelis-Menten)
// ============================================================================
function drawForceVelocityPlot(data) {
  const canvas = document.getElementById('canvasFV');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 45;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 35;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  // Escalas: F in [0, 7.0] pN, V in [0, 1.0] um/s
  const maxF = 7.0;
  const maxV = 1.0;

  function toX(f) { return padLeft + (f / maxF) * plotW; }
  function toY(v) { return padTop + plotH - (v / maxV) * plotH; }

  // Grid e Eixos
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  ctx.font = '10px monospace';
  ctx.fillStyle = '#64748b';
  ctx.textAlign = 'right';

  for (let v = 0; v <= maxV; v += 0.2) {
    const y = toY(v);
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(w - padRight, y);
    ctx.stroke();
    ctx.fillText(v.toFixed(1), padLeft - 6, y + 3);
  }

  ctx.textAlign = 'center';
  for (let f = 0; f <= maxF; f += 1.0) {
    const x = toX(f);
    ctx.beginPath();
    ctx.moveTo(x, padTop);
    ctx.lineTo(x, padTop + plotH);
    ctx.stroke();
    ctx.fillText(f.toFixed(0), x, h - padBottom + 14);
  }

  // Linha de Stall Force (6.13 pN)
  const stallX = toX(6.13);
  ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(stallX, padTop);
  ctx.lineTo(stallX, padTop + plotH);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = '#ef4444';
  ctx.fillText('F_stall ~6.1 pN', stallX - 8, padTop + 12);

  // Curva M1 (Linha tracejada laranja)
  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 1.8;
  ctx.setLineDash([5, 4]);
  ctx.beginPath();
  data.curves.force_velocity_curve.m1.forEach((pt, idx) => {
    const px = toX(pt.load_pN);
    const py = toY(pt.velocity_um_s);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();
  ctx.setLineDash([]);

  // Curva M2 (Linha solida azul)
  ctx.strokeStyle = '#38bdf8';
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  data.curves.force_velocity_curve.m2.forEach((pt, idx) => {
    const px = toX(pt.load_pN);
    const py = toY(pt.velocity_um_s);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // Dados Empiricos: Dataset B (Visscher 1999) com barras de erro
  data.empirical_data.dataset_b.forEach(pt => {
    const px = toX(pt.load_force_pN);
    const py = toY(pt.velocity_um_s);
    const uncY1 = toY(pt.velocity_um_s + pt.uncertainty_um_s);
    const uncY2 = toY(Math.max(0, pt.velocity_um_s - pt.uncertainty_um_s));

    // Barra de erro vertical
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(px, uncY1);
    ctx.lineTo(px, uncY2);
    ctx.stroke();

    // Cap horizontal
    ctx.beginPath();
    ctx.moveTo(px - 3, uncY1);
    ctx.lineTo(px + 3, uncY1);
    ctx.moveTo(px - 3, uncY2);
    ctx.lineTo(px + 3, uncY2);
    ctx.stroke();

    // Ponto central
    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.arc(px, py, 3.5, 0, Math.PI * 2);
    ctx.fill();
  });

  // Marcador do Ponto Operacional Atual
  const curF = data.curves.operating_point.load_pN;
  const curV = data.curves.operating_point.velocity_m2_um_s;
  const curX = toX(curF);
  const curY = toY(curV);

  ctx.fillStyle = '#ef4444';
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(curX, curY, 6, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Titulos dos eixos
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('Forca Contraria F_load (pN)', padLeft + plotW / 2, h - 6);

  ctx.save();
  ctx.translate(12, padTop + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('Velocidade v (μm/s)', 0, 0);
  ctx.restore();
}

function drawMichaelisMentenPlot(data) {
  const canvas = document.getElementById('canvasMM');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 45;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 35;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const maxAtp = 2500.0;
  const maxV = 1.0;

  function toX(a) { return padLeft + (a / maxAtp) * plotW; }
  function toY(v) { return padTop + plotH - (v / maxV) * plotH; }

  // Grid e Eixos
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  ctx.font = '10px monospace';
  ctx.fillStyle = '#64748b';
  ctx.textAlign = 'right';

  for (let v = 0; v <= maxV; v += 0.2) {
    const y = toY(v);
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(w - padRight, y);
    ctx.stroke();
    ctx.fillText(v.toFixed(1), padLeft - 6, y + 3);
  }

  ctx.textAlign = 'center';
  for (let a = 0; a <= maxAtp; a += 500) {
    const x = toX(a);
    ctx.beginPath();
    ctx.moveTo(x, padTop);
    ctx.lineTo(x, padTop + plotH);
    ctx.stroke();
    ctx.fillText(a.toFixed(0), x, h - padBottom + 14);
  }

  // Curva M1
  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 1.8;
  ctx.setLineDash([5, 4]);
  ctx.beginPath();
  data.curves.michaelis_menten_curve.m1.forEach((pt, idx) => {
    const px = toX(pt.atp_uM);
    const py = toY(pt.velocity_um_s);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();
  ctx.setLineDash([]);

  // Curva M2
  ctx.strokeStyle = '#38bdf8';
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  data.curves.michaelis_menten_curve.m2.forEach((pt, idx) => {
    const px = toX(pt.atp_uM);
    const py = toY(pt.velocity_um_s);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // Dados Empiricos: Dataset A (Schnitzer 1997)
  data.empirical_data.dataset_a.forEach(pt => {
    const px = toX(pt.atp_uM);
    const py = toY(pt.velocity_um_s);
    const uncY1 = toY(pt.velocity_um_s + pt.uncertainty_um_s);
    const uncY2 = toY(Math.max(0, pt.velocity_um_s - pt.uncertainty_um_s));

    // Barra de erro vertical
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(px, uncY1);
    ctx.lineTo(px, uncY2);
    ctx.stroke();

    // Cap horizontal
    ctx.beginPath();
    ctx.moveTo(px - 3, uncY1);
    ctx.lineTo(px + 3, uncY1);
    ctx.moveTo(px - 3, uncY2);
    ctx.lineTo(px + 3, uncY2);
    ctx.stroke();

    // Ponto
    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.arc(px, py, 3.5, 0, Math.PI * 2);
    ctx.fill();
  });

  // Ponto Operacional
  const curA = data.curves.operating_point.atp_uM;
  const curV = data.curves.operating_point.velocity_m2_um_s;
  const curX = toX(curA);
  const curY = toY(curV);

  ctx.fillStyle = '#ef4444';
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(curX, curY, 6, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Titulos dos eixos
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('Concentracao de ATP (μM)', padLeft + plotW / 2, h - 6);

  ctx.save();
  ctx.translate(12, padTop + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('Velocidade v (μm/s)', 0, 0);
  ctx.restore();
}

// ============================================================================
// Tab 2: Motor Competition (Tug-of-War Kinesin vs Dynein - Ciclo 12)
// ============================================================================
function setupTugOfWarControls() {
  const sliderNk = document.getElementById('sliderTowNk');
  const sliderNd = document.getElementById('sliderTowNd');
  const sliderFext = document.getElementById('sliderTowFext');
  const sliderDur = document.getElementById('sliderTowDur');
  const btnRun = document.getElementById('btnRunTow');

  sliderNk.addEventListener('input', (e) => {
    document.getElementById('valTowNk').textContent = e.target.value;
  });
  sliderNd.addEventListener('input', (e) => {
    document.getElementById('valTowNd').textContent = e.target.value;
  });
  sliderFext.addEventListener('input', (e) => {
    document.getElementById('valTowFext').textContent = parseFloat(e.target.value).toFixed(1) + ' pN';
  });
  sliderDur.addEventListener('input', (e) => {
    document.getElementById('valTowDur').textContent = parseFloat(e.target.value).toFixed(1) + ' s';
  });

  btnRun.addEventListener('click', runTugOfWarSimulation);
}

async function runTugOfWarSimulation() {
  const nk = parseInt(document.getElementById('sliderTowNk').value);
  const nd = parseInt(document.getElementById('sliderTowNd').value);
  const fext = parseFloat(document.getElementById('sliderTowFext').value);
  const dur = parseFloat(document.getElementById('sliderTowDur').value);

  try {
    const resp = await fetch('/api/simulate/tug-of-war', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        num_kinesins: nk,
        num_dyneins: nd,
        external_load_pN: fext,
        duration_s: dur,
        seed: Math.floor(Math.random() * 10000),
      })
    });
    const result = await resp.json();
    State.towSimData = result;
    updateTugOfWarUI(result);
  } catch (err) {
    console.error('Erro na simulacao de Tug-of-War:', err);
  }
}

function updateTugOfWarUI(res) {
  const m = res.metrics;
  document.getElementById('mTowNetVel').textContent = m.net_velocity_nm_s.toFixed(1) + ' nm/s';
  document.getElementById('mTowTotDist').textContent = m.total_distance_nm.toFixed(1) + ' nm';
  document.getElementById('mTowReversals').textContent = m.directional_reversals;
  document.getElementById('mTowFracPlus').textContent = (m.fraction_plus_end * 100).toFixed(1) + ' %';
  document.getElementById('mTowFracMinus').textContent = (m.fraction_minus_end * 100).toFixed(1) + ' %';
  document.getElementById('mTowFracPause').textContent = (m.fraction_pause_tug_of_war * 100).toFixed(1) + ' %';
  document.getElementById('mTowMeanNk').textContent = m.mean_kinesins_engaged.toFixed(1);
  document.getElementById('mTowMeanNd').textContent = m.mean_dyneins_engaged.toFixed(1);

  drawTowTrajectoryPlot(res.trajectory);
  drawTowMotorsPlot(res.trajectory);
  drawTowDistributionPlot(res.steady_state_distribution);
}

function drawTowTrajectoryPlot(traj) {
  const canvas = document.getElementById('canvasTowTrajectory');
  if (!canvas || !traj || traj.length === 0) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 60;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 35;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const maxT = traj[traj.length - 1].time_s;
  const positions = traj.map(pt => pt.cargo_position_nm);
  const minX = Math.min(0, Math.min(...positions));
  const maxX = Math.max(100, Math.max(...positions));
  const spanX = Math.max(10, maxX - minX);

  function toScreenX(t) { return padLeft + (t / maxT) * plotW; }
  function toScreenY(x) { return padTop + plotH - ((x - minX) / spanX) * plotH; }

  // Grid
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padLeft, toScreenY(0));
  ctx.lineTo(w - padRight, toScreenY(0));
  ctx.stroke();

  // Traco de Trajetoria
  ctx.lineWidth = 2.2;
  for (let i = 0; i < traj.length - 1; i++) {
    const pt1 = traj[i];
    const pt2 = traj[i + 1];

    if (pt1.state_classification === 'PLUS_END_MOTION') {
      ctx.strokeStyle = '#10b981'; // Verde (Kinesin)
    } else if (pt1.state_classification === 'MINUS_END_MOTION') {
      ctx.strokeStyle = '#8b5cf6'; // Violeta (Dynein)
    } else if (pt1.state_classification === 'TUG_OF_WAR_PAUSE') {
      ctx.strokeStyle = '#f59e0b'; // Laranja (Pausa)
    } else {
      ctx.strokeStyle = '#64748b'; // Cinza (Desprendido)
    }

    ctx.beginPath();
    ctx.moveTo(toScreenX(pt1.time_s), toScreenY(pt1.cargo_position_nm));
    ctx.lineTo(toScreenX(pt2.time_s), toScreenY(pt2.cargo_position_nm));
    ctx.stroke();
  }

  // Eixos e Labels
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('Tempo (s)', padLeft + plotW / 2, h - 6);

  ctx.save();
  ctx.translate(16, padTop + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('Posicao da Carga x (nm)', 0, 0);
  ctx.restore();
}

function drawTowMotorsPlot(traj) {
  const canvas = document.getElementById('canvasTowMotors');
  if (!canvas || !traj || traj.length === 0) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 40;
  const padRight = 15;
  const padTop = 15;
  const padBottom = 30;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const maxT = traj[traj.length - 1].time_s;
  const maxMotors = 10;

  function toScreenX(t) { return padLeft + (t / maxT) * plotW; }
  function toScreenY(n) { return padTop + plotH - (n / maxMotors) * plotH; }

  // Linha Kinesinas (Verde)
  ctx.strokeStyle = '#10b981';
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  traj.forEach((pt, idx) => {
    const px = toScreenX(pt.time_s);
    const py = toScreenY(pt.bound_kinesins);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // Linha Dineinas (Violeta)
  ctx.strokeStyle = '#8b5cf6';
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  traj.forEach((pt, idx) => {
    const px = toScreenX(pt.time_s);
    const py = toScreenY(pt.bound_dyneins);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // Labels
  ctx.fillStyle = '#94a3b8';
  ctx.font = '9px monospace';
  ctx.fillText('n_+ (Kinesina: Verde) vs n_- (Dineina: Violeta)', padLeft + 10, padTop + 12);
}

function drawTowDistributionPlot(dist) {
  const canvas = document.getElementById('canvasTowDistribution');
  if (!canvas || !dist) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 40;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 30;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const items = [
    { label: 'Plus-End', val: dist.summary_p_plus || 0.0, color: '#10b981' },
    { label: 'Minus-End', val: dist.summary_p_minus || 0.0, color: '#8b5cf6' },
    { label: 'Tug-of-War', val: dist.summary_p_pause || 0.0, color: '#f59e0b' },
    { label: 'Unbound', val: dist.summary_p_unbound || 0.0, color: '#64748b' },
  ];

  const barWidth = plotW / items.length - 16;

  items.forEach((item, idx) => {
    const bx = padLeft + idx * (plotW / items.length) + 8;
    const bh = item.val * plotH;
    const by = padTop + plotH - bh;

    ctx.fillStyle = item.color;
    ctx.fillRect(bx, by, barWidth, bh);

    ctx.fillStyle = '#f8fafc';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText((item.val * 100).toFixed(1) + '%', bx + barWidth / 2, by - 4);
    ctx.fillText(item.label, bx + barWidth / 2, h - padBottom + 14);
  });
}

// ============================================================================
// Tab 3: Langevin Stochastic Dynamics (Ciclo 13)
// ============================================================================
function setupLangevinControls() {
  const sliderK = document.getElementById('sliderLangKtrap');
  const sliderAtp = document.getElementById('sliderLangAtp');
  const sliderTime = document.getElementById('sliderLangTime');
  const btnRun = document.getElementById('btnRunLang');

  sliderK.addEventListener('input', (e) => {
    document.getElementById('valLangKtrap').textContent = parseFloat(e.target.value).toFixed(3) + ' pN/nm';
  });
  sliderAtp.addEventListener('input', (e) => {
    document.getElementById('valLangAtp').textContent = e.target.value + ' μM';
  });
  sliderTime.addEventListener('input', (e) => {
    document.getElementById('valLangTime').textContent = e.target.value + ' ms';
  });

  btnRun.addEventListener('click', runLangevinSimulation);
}

async function runLangevinSimulation() {
  const ktrap = parseFloat(document.getElementById('sliderLangKtrap').value);
  const atp = parseFloat(document.getElementById('sliderLangAtp').value);
  const time = parseFloat(document.getElementById('sliderLangTime').value);

  try {
    const resp = await fetch('/api/simulate/langevin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trap_stiffness_pN_nm: ktrap,
        atp_uM: atp,
        total_time_ms: time,
        dt_us: 2.0,
        seed: Math.floor(Math.random() * 10000),
      })
    });
    const result = await resp.json();
    State.langSimData = result;
    updateLangevinUI(result);
  } catch (err) {
    console.error('Erro na simulacao de Langevin:', err);
  }
}

function updateLangevinUI(res) {
  const m = res.metrics;
  document.getElementById('mLangSteps').textContent = m.total_steps;
  document.getElementById('mLangMaxForce').textContent = m.stall_force_reached_pN.toFixed(2) + ' pN';
  document.getElementById('mLangRms').textContent = m.thermal_noise_rms_nm.toFixed(2) + ' nm';
  document.getElementById('mLangGamma').textContent = m.drag_coefficient_pN_us_nm.toFixed(6) + ' pN·μs/nm';
  document.getElementById('mLangDiff').textContent = m.diffusion_coefficient_nm2_us.toFixed(1) + ' nm²/μs';

  drawLangevinTrajectoryPlot(res.points);
  drawLangevinForcePlot(res.points);
  drawLangevinHistogramPlot(res.histogram_bins, res.histogram_counts);
}

function drawLangevinTrajectoryPlot(points) {
  const canvas = document.getElementById('canvasLangTrajectory');
  if (!canvas || !points || points.length === 0) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 55;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 35;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const maxT = points[points.length - 1].time_ms;
  const beadPos = points.map(p => p.bead_position_nm);
  const minX = Math.min(-10, Math.min(...beadPos));
  const maxX = Math.max(50, Math.max(...beadPos));
  const spanX = Math.max(10, maxX - minX);

  function toScreenX(t) { return padLeft + (t / maxT) * plotW; }
  function toScreenY(x) { return padTop + plotH - ((x - minX) / spanX) * plotH; }

  // Grade
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padLeft, toScreenY(0));
  ctx.lineTo(w - padRight, toScreenY(0));
  ctx.stroke();

  // Linha Degraus Motor (Amarela)
  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 2.0;
  ctx.beginPath();
  points.forEach((p, idx) => {
    const px = toScreenX(p.time_ms);
    const py = toScreenY(p.motor_position_nm);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // Traco Browniano Bead (Ciano)
  ctx.strokeStyle = '#38bdf8';
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  points.forEach((p, idx) => {
    const px = toScreenX(p.time_ms);
    const py = toScreenY(p.bead_position_nm);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // Eixos
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('Tempo (ms)', padLeft + plotW / 2, h - 6);

  ctx.save();
  ctx.translate(16, padTop + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('Deslocamento (nm)', 0, 0);
  ctx.restore();
}

function drawLangevinForcePlot(points) {
  const canvas = document.getElementById('canvasLangForce');
  if (!canvas || !points || points.length === 0) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 45;
  const padRight = 15;
  const padTop = 15;
  const padBottom = 30;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const maxT = points[points.length - 1].time_ms;
  const forces = points.map(p => p.trap_force_pN);
  const maxF = Math.max(6.5, Math.max(...forces));

  function toScreenX(t) { return padLeft + (t / maxT) * plotW; }
  function toScreenY(f) { return padTop + plotH - (f / maxF) * plotH; }

  // Linha de forca
  ctx.strokeStyle = '#ef4444';
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  points.forEach((p, idx) => {
    const px = toScreenX(p.time_ms);
    const py = toScreenY(p.trap_force_pN);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // Labels
  ctx.fillStyle = '#94a3b8';
  ctx.font = '9px monospace';
  ctx.fillText('Forca Restauradora F_trap (pN)', padLeft + 10, padTop + 12);
}

function drawLangevinHistogramPlot(bins, counts) {
  const canvas = document.getElementById('canvasLangHistogram');
  if (!canvas || !bins || bins.length === 0) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 40;
  const padRight = 15;
  const padTop = 15;
  const padBottom = 30;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const maxCount = Math.max(...counts);
  const barW = plotW / bins.length;

  bins.forEach((b, idx) => {
    const c = counts[idx];
    const bx = padLeft + idx * barW;
    const bh = (c / maxCount) * plotH;
    const by = padTop + plotH - bh;

    ctx.fillStyle = '#38bdf8';
    ctx.fillRect(bx, by, barW - 1, bh);
  });

  ctx.fillStyle = '#94a3b8';
  ctx.font = '9px monospace';
  ctx.fillText('Distribuicao Espacial (Periodicidade 8.2 nm)', padLeft + 10, padTop + 12);
}

// ============================================================================
// Tab 4: Provenance Graph
// ============================================================================
async function fetchProvenanceGraph() {
  try {
    const resp = await fetch('/api/provenance');
    const data = await resp.json();
    State.provenanceData = data;
  } catch (err) {
    console.error('Erro ao carregar proveniencia:', err);
  }
}

function drawProvenanceGraph() {
  const canvas = document.getElementById('canvasProvenance');
  if (!canvas || !State.provenanceData) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const nodes = State.provenanceData.nodes;
  const edges = State.provenanceData.edges;

  // Layout estratificado por camadas
  const layerMap = {
    'SOURCE': 60,
    'EXPERIMENT': 180,
    'DATASET': 300,
    'MODEL': 460,
    'CLAIM': 620,
    'CONFLICT': 780,
    'HYPOTHESIS': 940,
  };

  const nodePos = {};
  const layerCounters = {};

  nodes.forEach(n => {
    const lx = layerMap[n.type] || 500;
    layerCounters[n.type] = (layerCounters[n.type] || 0) + 1;
    const ly = 60 + layerCounters[n.type] * 70;
    nodePos[n.id] = { x: lx, y: ly, node: n };
  });

  // Desenha Arestas
  ctx.lineWidth = 1.4;
  edges.forEach(e => {
    const p1 = nodePos[e.from];
    const p2 = nodePos[e.to];
    if (p1 && p2) {
      ctx.strokeStyle = e.relation.includes('REFUTES') ? '#ef4444' : '#334155';
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
  });

  // Desenha Nos
  nodes.forEach(n => {
    const pos = nodePos[n.id];
    if (!pos) return;

    ctx.fillStyle = n.type === 'CONFLICT' ? '#ef4444' : (n.type === 'MODEL' ? '#38bdf8' : '#1e293b');
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(pos.x - 55, pos.y - 18, 110, 36, 4);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#f8fafc';
    ctx.font = '9px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(n.type, pos.x, pos.y - 4);
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(n.id.substring(0, 14), pos.x, pos.y + 8);
  });
}

// ============================================================================
// Tab 5: Discriminator Matrix Heatmap
// ============================================================================
function drawDiscriminatorMatrix() {
  const canvas = document.getElementById('canvasDiscriminator');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const padLeft = 45;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 35;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const cols = 20;
  const rows = 15;
  const cellW = plotW / cols;
  const cellH = plotH / rows;

  for (let c = 0; c < cols; c++) {
    for (let r = 0; r < rows; r++) {
      const atp = 100 + (c / cols) * 2000;
      const load = (r / rows) * 6.0;

      // Calculo analitico de separabilidade |v1 - v2|
      const v1 = (103.92 * atp / (94.63 + atp)) * 0.0082;
      const v2 = v1 * Math.exp(-load * 0.1 / 4.10) * Math.max(0, 1 - Math.pow(load / 6.13, 2.05));
      const diff = Math.abs(v1 - v2);
      const norm = Math.min(1.0, diff / 0.6);

      // Cor: azul escuro para separabilidade baixa, vermelho intenso para alta
      const red = Math.floor(norm * 239);
      const green = Math.floor((1 - norm) * 185);
      const blue = Math.floor(norm * 68 + (1 - norm) * 248);

      ctx.fillStyle = `rgb(${red}, ${green}, ${blue})`;
      ctx.fillRect(padLeft + c * cellW, padTop + plotH - (r + 1) * cellH, cellW - 1, cellH - 1);
    }
  }

  // Destaque do Ponto Otimo: ATP = 1000 uM, Load = 2.5 pN
  const optX = padLeft + (900 / 2000) * plotW;
  const optY = padTop + plotH - (2.5 / 6.0) * plotH;

  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.arc(optX, optY, 8, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = '#ffffff';
  ctx.font = '10px monospace';
  ctx.textAlign = 'left';
  ctx.fillText('Otimo: [1000 μM, 2.5 pN]', optX + 12, optY + 3);

  // Eixos
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('Concentracao de ATP (μM)', padLeft + plotW / 2, h - 6);

  ctx.save();
  ctx.translate(14, padTop + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('Forca Contraria F_load (pN)', 0, 0);
  ctx.restore();
}
