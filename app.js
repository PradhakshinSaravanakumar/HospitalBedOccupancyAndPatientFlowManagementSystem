// SmartHospital BedIQ Platform - Full-Stack Clinical API Client Script

const API_BASE = ''; // Same origin

document.addEventListener('DOMContentLoaded', () => {
  initLiveClock();
  initNotificationBell();
  loadGlobalKPIs();
  
  const path = window.location.pathname;
  if (path.includes('patients.html')) {
    initPatientsPage();
  } else if (path.includes('beds.html')) {
    initBedsPage();
  } else if (path.includes('dashboard.html') || path.includes('overview.html')) {
    initDashboardPage();
  } else if (path.includes('alerts.html')) {
    initAlertsPage();
  } else if (path.includes('index.html') || path === '/' || path.endsWith('/')) {
    initLoginPage();
  }
});

// Real-time Clock Header Update
function initLiveClock() {
  const clockEl = document.querySelector('.datetime');
  if (clockEl) {
    const updateClock = () => {
      const now = new Date();
      const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
      clockEl.innerHTML = `🗓️ ${now.toLocaleDateString('en-US', options)}`;
    };
    updateClock();
    setInterval(updateClock, 1000);
  }
}

// Interactive Notification Bell & Dropdown
function initNotificationBell() {
  const notifContainer = document.querySelector('.notifications');
  if (!notifContainer) return;

  // Create dropdown container inside .notifications if not present
  let dropdown = notifContainer.querySelector('.notif-dropdown');
  if (!dropdown) {
    dropdown = document.createElement('div');
    dropdown.className = 'notif-dropdown';
    dropdown.innerHTML = `
      <div class="notif-dropdown-header">
        <span>Active Alerts &amp; Notifications</span>
        <span class="notif-count-pill" id="dropdownNotifCount">Loading...</span>
      </div>
      <div class="notif-dropdown-body" id="notifDropdownList">
        <div style="padding:16px;text-align:center;color:#888;font-size:0.85rem;">Loading alerts...</div>
      </div>
      <div class="notif-dropdown-footer">
        <a href="alerts.html" class="notif-view-all-link">Go to Full Alerts Page →</a>
      </div>
    `;
    notifContainer.appendChild(dropdown);
  }

  // Toggle dropdown on bell click
  notifContainer.addEventListener('click', (e) => {
    if (e.target.closest('.notif-resolve-btn') || e.target.closest('.notif-view-all-link')) {
      return;
    }
    e.stopPropagation();
    const isCurrentlyActive = dropdown.classList.contains('active');
    if (isCurrentlyActive) {
      dropdown.classList.remove('active');
    } else {
      dropdown.classList.add('active');
      loadNotificationsDropdown();
    }
  });

  // Close when clicking outside
  document.addEventListener('click', (e) => {
    if (!notifContainer.contains(e.target)) {
      dropdown.classList.remove('active');
    }
  });
}

async function loadNotificationsDropdown() {
  const listEl = document.getElementById('notifDropdownList');
  const countEl = document.getElementById('dropdownNotifCount');
  if (!listEl) return;

  try {
    const res = await fetch(`${API_BASE}/api/alerts`);
    const json = await res.json();
    if (json.success && json.data) {
      const activeAlerts = json.data.filter(a => a.is_resolved === 0 || a.is_resolved === false);
      if (countEl) countEl.textContent = `${activeAlerts.length} Active`;

      // Sync top header notif-badge
      const notifBadges = document.querySelectorAll('.notif-badge');
      notifBadges.forEach(b => b.textContent = activeAlerts.length);

      if (activeAlerts.length === 0) {
        listEl.innerHTML = `
          <div style="padding:24px;text-align:center;color:#38a169;font-size:0.85rem;">
            ✓ All caught up! No active alerts.
          </div>
        `;
        return;
      }

      listEl.innerHTML = '';
      activeAlerts.slice(0, 6).forEach(a => {
        let pillCls = 'blue-pill';
        if (a.severity === 'Critical' || a.severity === 'High') pillCls = 'red-pill';
        else if (a.severity === 'Medium') pillCls = 'orange-pill';
        else if (a.severity === 'Low') pillCls = 'green-pill';

        const item = document.createElement('div');
        item.className = 'notif-item';
        item.innerHTML = `
          <div class="notif-item-header">
            <span class="notif-item-title">${a.title}</span>
            <span class="pill ${pillCls}">${a.severity || 'Medium'}</span>
          </div>
          <div class="notif-item-msg">${a.message || ''}</div>
          <div class="notif-item-footer">
            <span style="color:#a0aec0;font-size:0.75rem;">${a.category || 'System'}</span>
            <button class="notif-resolve-btn" onclick="resolveNotificationFromDropdown(${a.id}, event)">Mark Resolved ✓</button>
          </div>
        `;
        listEl.appendChild(item);
      });
    }
  } catch (err) {
    listEl.innerHTML = '<div style="padding:16px;text-align:center;color:#e53e3e;font-size:0.85rem;">Failed to load alerts</div>';
  }
}

async function resolveNotificationFromDropdown(alertId, event) {
  if (event) event.stopPropagation();
  try {
    const res = await fetch(`${API_BASE}/api/alerts/${alertId}/resolve`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' }
    });
    const json = await res.json();
    if (json.success) {
      await loadNotificationsDropdown();
      await loadGlobalKPIs();
    }
  } catch (err) {
    console.error('Error resolving alert:', err);
  }
}

// Global KPI Loader (Updates badges and KPI cards across pages)
async function loadGlobalKPIs() {
  try {
    const res = await fetch(`${API_BASE}/api/kpis`);
    const json = await res.json();
    if (json.success) {
      const data = json.data;
      
      // Sidebar badges
      const patientBadge = document.querySelector('.menu-item .badge.blue');
      if (patientBadge) patientBadge.textContent = data.totalPatients;

      const alertBadge = document.querySelector('.menu-item .badge.red');
      if (alertBadge) alertBadge.textContent = data.activeAlerts;

      // Bed Management KPIs (beds.html)
      const kpiTotalBeds = document.getElementById('kpiTotalBeds');
      if (kpiTotalBeds) kpiTotalBeds.textContent = data.totalBeds;

      const kpiAvailableBeds = document.getElementById('kpiAvailableBeds');
      if (kpiAvailableBeds) kpiAvailableBeds.textContent = data.availableBeds;

      const kpiOccupiedBeds = document.getElementById('kpiOccupiedBeds');
      if (kpiOccupiedBeds) kpiOccupiedBeds.textContent = data.occupiedBeds;

      const kpiCleaningBeds = document.getElementById('kpiCleaningBeds');
      if (kpiCleaningBeds) kpiCleaningBeds.textContent = data.cleaningBeds;

      const kpiReservedBeds = document.getElementById('kpiReservedBeds');
      if (kpiReservedBeds) kpiReservedBeds.textContent = data.maintenanceBeds || 0;

      // Dashboard & Overview KPIs
      const kpiOccupancy = document.getElementById('kpiOccupancy');
      if (kpiOccupancy) kpiOccupancy.textContent = `${data.occupancyRate}%`;

      const kpiTotalPatients = document.getElementById('kpiTotalPatients');
      if (kpiTotalPatients) kpiTotalPatients.textContent = data.totalPatients;

      const kpiCritical = document.getElementById('kpiCritical');
      if (kpiCritical) kpiCritical.textContent = data.criticalPatients;

      const kpiStable = document.getElementById('kpiStable');
      if (kpiStable) {
        const stableCount = Math.max(0, data.totalPatients - data.criticalPatients);
        kpiStable.textContent = stableCount;
      }
    }
  } catch (err) {
    console.warn('Could not fetch global KPIs:', err);
  }
}

// -------------------------------------------------------------
// PATIENTS PAGE HANDLER & CLINICAL WORKFLOWS
// -------------------------------------------------------------
async function initPatientsPage() {
  await renderPatientsTable();
}

async function renderPatientsTable() {
  const tbody = document.getElementById('patientsTableBody');
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/api/patients`);
    const json = await res.json();
    if (json.success) {
      tbody.innerHTML = '';
      if (json.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:24px;color:#888;">No patients found in database.</td></tr>';
        return;
      }

      json.data.forEach(p => {
        const tr = document.createElement('tr');
        tr.dataset.id = p.id;
        tr.dataset.mrn = p.mrn;
        
        let pillClass = 'green-pill';
        if (p.condition === 'Critical') pillClass = 'red-pill';
        else if (p.condition === 'Guarded' || p.condition === 'Moderate') pillClass = 'orange-pill';
        else if (p.condition === 'Recovering') pillClass = 'purple-pill';
        
        const isDischarged = p.status === 'Discharged';
        const wardName = p.ward_name || 'General';
        const bedNum = isDischarged ? '<span class="fade-text">Released</span>' : (p.bed_number || 'Unassigned');
        const admittedDate = p.admission_date ? p.admission_date.split(' ')[0] : 'Today';
        const diagnosis = p.diagnosis || (p.condition + ' Care');

        // Clinical Actions based on status
        let actionsHtml = '';
        if (isDischarged) {
          actionsHtml = `
            <div class="table-actions">
              <span class="fade-text" style="font-size:0.75rem;margin-right:4px;">Discharged</span>
              <button class="action-btn delete-btn-table" onclick="deletePatientRow(this)" title="Delete Patient Record">🗑️</button>
            </div>
          `;
        } else {
          actionsHtml = `
            <div class="table-actions">
              <button class="discharge-btn" onclick="dischargePatient(${p.id}, '${escapeQuotes(p.name)}', '${escapeQuotes(p.bed_number || '')}')" title="Discharge Patient & Mark Bed for Cleaning">🚪 Discharge</button>
              <button class="shift-btn" onclick="openShiftPatientModal(${p.id}, '${escapeQuotes(p.name)}', ${p.ward_id || 1}, '${escapeQuotes(wardName)}', ${p.bed_id || 0}, '${escapeQuotes(p.bed_number || '')}')" title="Shift Patient to Different Ward">🔀 Shift</button>
              <button class="action-btn edit-btn" onclick="openEditPatientModal(this)" title="Edit Patient Info">✏️</button>
              <button class="action-btn delete-btn-table" onclick="deletePatientRow(this)" title="Delete Patient">🗑️</button>
            </div>
          `;
        }

        const statusPill = isDischarged
          ? `<span class="pill gray-pill status-text" style="background:#edf2f7;color:#718096;">Discharged</span>`
          : `<span class="pill ${pillClass} status-text">${p.condition}</span>`;

        tr.innerHTML = `
          <td class="bold-text blue-link patient-id">${p.mrn}</td>
          <td class="patient-name bold-text">${p.name}</td>
          <td class="patient-age">${p.age} / ${p.gender || 'Male'}</td>
          <td class="patient-ward">${wardName}</td>
          <td class="patient-bed">${bedNum}</td>
          <td class="patient-diagnosis">${diagnosis}</td>
          <td>${statusPill}</td>
          <td class="fade-text patient-admitted">${admittedDate}</td>
          <td class="patient-los">1d</td>
          <td>${actionsHtml}</td>
        `;
        tbody.appendChild(tr);
      });

      const countText = document.getElementById('patientCountText');
      if (countText) {
        const admittedCount = json.data.filter(p => p.status !== 'Discharged').length;
        countText.textContent = `${admittedCount} admitted patients (${json.data.length} total records)`;
      }
    }
  } catch (err) {
    console.error('Error fetching patients from MongoDB:', err);
  }
}

function escapeQuotes(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// DISCHARGE PATIENT ACTION
async function dischargePatient(patientId, patientName, bedNum) {
  const bedInfo = bedNum ? ` (Bed: ${bedNum})` : '';
  if (!confirm(`Are you sure you want to DISCHARGE patient ${patientName}${bedInfo}?\n\nThis will mark the patient as Discharged and transition their bed to the 'Cleaning' state.`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/patients/${patientId}/discharge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const json = await res.json();
    if (json.success) {
      alert(`✓ ${json.message}`);
      await renderPatientsTable();
      await loadGlobalKPIs();
    } else {
      alert(`Error: ${json.message || 'Could not discharge patient'}`);
    }
  } catch (err) {
    console.error('Discharge error:', err);
    alert('Failed to connect to backend server');
  }
}

// SHIFT / TRANSFER PATIENT MODAL HANDLERS
function openShiftPatientModal(patientId, name, currentWardId, currentWardName, currentBedId, currentBedNum) {
  let modal = document.getElementById('shiftModal');
  if (!modal) {
    modal = createShiftModalElement();
  }

  document.getElementById('shiftPatientId').value = patientId;
  document.getElementById('shiftPatientName').textContent = name || 'Patient';
  document.getElementById('shiftCurrentWard').textContent = currentWardName || 'General';
  document.getElementById('shiftCurrentBed').textContent = currentBedNum || 'Unassigned';

  const wardSelect = document.getElementById('shiftTargetWard');
  if (wardSelect) {
    loadAvailableBedsForShift(wardSelect.value);
  }

  modal.classList.add('active');
}

function closeShiftModal() {
  const modal = document.getElementById('shiftModal');
  if (modal) modal.classList.remove('active');
}

async function loadAvailableBedsForShift(wardId) {
  const bedSelect = document.getElementById('shiftTargetBed');
  if (!bedSelect) return;

  bedSelect.innerHTML = '<option value="">Loading available beds...</option>';
  try {
    const res = await fetch(`${API_BASE}/api/beds/available?ward_id=${wardId}`);
    const json = await res.json();
    if (json.success && json.data.length > 0) {
      bedSelect.innerHTML = '<option value="">-- Select an available bed --</option>';
      json.data.forEach(b => {
        bedSelect.innerHTML += `<option value="${b.id}" data-number="${b.bed_number}">${b.bed_number} (${b.bed_type || 'Standard'})</option>`;
      });
    } else {
      bedSelect.innerHTML = '<option value="">No available beds in this ward</option>';
    }
  } catch (err) {
    bedSelect.innerHTML = '<option value="">Error loading beds</option>';
  }
}

async function handleShiftPatient(event) {
  event.preventDefault();
  const patientId = document.getElementById('shiftPatientId').value;
  const wardSelect = document.getElementById('shiftTargetWard');
  const bedSelect = document.getElementById('shiftTargetBed');

  const newWardId = parseInt(wardSelect.value);
  const newWardName = wardSelect.options[wardSelect.selectedIndex].text;
  const newBedId = bedSelect.value ? parseInt(bedSelect.value) : null;
  const newBedNumber = bedSelect.selectedIndex >= 0 && bedSelect.value
    ? bedSelect.options[bedSelect.selectedIndex].dataset.number
    : null;

  if (!newBedId && !newBedNumber) {
    alert('Please select an available bed in the target ward.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/patients/${patientId}/transfer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ward_id: newWardId,
        ward_name: newWardName,
        bed_id: newBedId,
        bed_number: newBedNumber
      })
    });
    const json = await res.json();
    if (json.success) {
      alert(`✓ ${json.message}`);
      closeShiftModal();
      if (document.getElementById('patientsTableBody')) await renderPatientsTable();
      if (document.getElementById('bedsTableBody')) await renderBedsTable();
      await loadGlobalKPIs();
    } else {
      alert(`Error: ${json.message || 'Could not shift patient'}`);
    }
  } catch (err) {
    console.error('Shift error:', err);
    alert('Failed to connect to backend server');
  }
}

function createShiftModalElement() {
  const modalDiv = document.createElement('div');
  modalDiv.className = 'modal-overlay';
  modalDiv.id = 'shiftModal';
  modalDiv.innerHTML = `
    <div class="modal-card" style="max-width: 480px;">
      <div class="modal-header">
        <h2>Shift Patient to Different Ward</h2>
        <button type="button" class="modal-close-btn" onclick="closeShiftModal()">&times;</button>
      </div>
      <form id="shiftForm" onsubmit="handleShiftPatient(event)">
        <div class="modal-body">
          <div style="background:#f7fafc;padding:12px;border-radius:8px;border:1px solid #edf2f7;">
            <div>Patient: <strong id="shiftPatientName">-</strong></div>
            <div style="font-size:0.85rem;color:#718096;margin-top:4px;">Current: <span id="shiftCurrentWard">-</span> (Bed <span id="shiftCurrentBed">-</span>)</div>
          </div>
          <input type="hidden" id="shiftPatientId">
          
          <div class="form-group" style="margin-top:10px;">
            <label for="shiftTargetWard">Target Ward</label>
            <select id="shiftTargetWard" required onchange="loadAvailableBedsForShift(this.value)">
              <option value="1">ICU Ward</option>
              <option value="2">Emergency Ward</option>
              <option value="4">Cardiology Ward</option>
              <option value="6">Neurology Ward</option>
              <option value="7">Orthopedic Ward</option>
              <option value="5">Pediatrics Ward</option>
              <option value="8">Maternity Ward</option>
              <option value="3">General Surgery</option>
            </select>
          </div>
          <div class="form-group">
            <label for="shiftTargetBed">Target Bed (Available only)</label>
            <select id="shiftTargetBed" required>
              <option value="">Select an available bed...</option>
            </select>
            <small style="color:#718096;font-size:0.8rem;margin-top:4px;">* The previous bed will automatically move to <strong>Cleaning</strong> state.</small>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn-secondary" onclick="closeShiftModal()">Cancel</button>
          <button type="submit" class="btn-primary" id="confirmShiftBtn">🔀 Confirm Transfer</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(modalDiv);
  return modalDiv;
}

// -------------------------------------------------------------
// BEDS PAGE HANDLER & BED INVENTORY
// -------------------------------------------------------------
async function initBedsPage() {
  await renderBedsTable();
  await loadGlobalKPIs();
}

async function renderBedsTable() {
  const tbody = document.getElementById('bedsTableBody');
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/api/beds`);
    const json = await res.json();
    if (json.success && json.data) {
      tbody.innerHTML = '';
      if (json.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:24px;color:#888;">No beds configured in database.</td></tr>';
        return;
      }

      json.data.forEach(b => {
        const tr = document.createElement('tr');
        tr.dataset.id = b.id;
        
        let statusPillClass = 'green-pill';
        if (b.status === 'Occupied') statusPillClass = 'red-pill';
        else if (b.status === 'Cleaning') statusPillClass = 'orange-pill';
        else if (b.status === 'Maintenance' || b.status === 'Reserved') statusPillClass = 'blue-pill';

        let typePillClass = 'blue-pill';
        if ((b.ward_name && b.ward_name.includes('ICU')) || (b.bed_type && b.bed_type.includes('ICU'))) typePillClass = 'red-pill';
        else if (b.ward_name && b.ward_name.includes('Emergency')) typePillClass = 'orange-pill';

        // Assigned Patient
        let patientText = '<span class="patient-name fade-text">-</span>';
        if (b.status === 'Occupied') {
          const pName = b.patient_name || 'Assigned';
          const pMrn = b.mrn ? `${b.mrn} - ` : '';
          patientText = `<span class="patient-name bold-text" style="color:#2b6cb0;">${pMrn}${pName}</span>`;
        } else if (b.status === 'Cleaning') {
          patientText = '<span class="patient-name fade-text" style="color:#dd6b20;">🔄 Cleaning in progress</span>';
        }

        // Action Buttons per Bed
        let actionsHtml = '';
        if (b.status === 'Occupied') {
          actionsHtml = `
            <div class="table-actions">
              <button class="discharge-btn" onclick="dischargePatientFromBed(${b.id}, ${b.patient_id || 'null'}, '${escapeQuotes(b.patient_name || '')}', '${escapeQuotes(b.bed_number)}')" title="Discharge Patient (Bed becomes Cleaning)">🚪 Discharge</button>
              <button class="shift-btn" onclick="openShiftPatientModal(${b.patient_id || 'null'}, '${escapeQuotes(b.patient_name || '')}', ${b.ward_id || 1}, '${escapeQuotes(b.ward_name || '')}', ${b.id}, '${escapeQuotes(b.bed_number)}')" title="Shift Patient to Another Ward">🔀 Shift</button>
              <button class="action-btn delete-btn-table" onclick="deleteBedById(${b.id}, '${escapeQuotes(b.bed_number)}')" title="Delete Bed">🗑️</button>
            </div>
          `;
        } else if (b.status === 'Cleaning') {
          actionsHtml = `
            <div class="table-actions">
              <button class="clean-done-btn" onclick="markCleaningCompleted(${b.id}, '${escapeQuotes(b.bed_number)}')" title="Mark Cleaning Completed -> Bed becomes Available">✓ Cleaning Done</button>
              <button class="action-btn delete-btn-table" onclick="deleteBedById(${b.id}, '${escapeQuotes(b.bed_number)}')" title="Delete Bed">🗑️</button>
            </div>
          `;
        } else {
          // Available
          actionsHtml = `
            <div class="table-actions">
              <span style="font-size:0.75rem;color:#38a169;font-weight:600;padding:4px 6px;background:#f0fff4;border-radius:4px;">✓ Available</span>
              <button class="action-btn delete-btn-table" onclick="deleteBedById(${b.id}, '${escapeQuotes(b.bed_number)}')" title="Delete Bed">🗑️</button>
            </div>
          `;
        }

        const updatedTime = b.last_updated || 'Today';

        tr.innerHTML = `
          <td class="bold-text blue-link bed-id">${b.bed_number}</td>
          <td class="ward-name">${b.ward_name || 'General'}</td>
          <td><span class="pill ${typePillClass} bed-type">${b.bed_type || 'Standard'}</span></td>
          <td><span class="pill ${statusPillClass} status-text">${b.status}</span></td>
          <td>${patientText}</td>
          <td class="fade-text last-updated">${updatedTime}</td>
          <td>${actionsHtml}</td>
        `;
        tbody.appendChild(tr);
      });

      const bedsCountEl = document.getElementById('bedsCount');
      if (bedsCountEl) bedsCountEl.textContent = `${json.data.length} beds in MongoDB`;
    }
  } catch (err) {
    console.error('Error fetching beds from MongoDB:', err);
  }
}

// MARK CLEANING COMPLETED ACTION (Moves bed from Cleaning to Available)
async function markCleaningCompleted(bedId, bedNum) {
  try {
    const res = await fetch(`${API_BASE}/api/beds/${bedId}/cleaning-completed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const json = await res.json();
    if (json.success) {
      await renderBedsTable();
      await loadGlobalKPIs();
    } else {
      alert(`Error: ${json.message || 'Could not update bed'}`);
    }
  } catch (err) {
    console.error('Cleaning completed error:', err);
    alert('Failed to update bed status');
  }
}

// DISCHARGE PATIENT FROM BED ROW
async function dischargePatientFromBed(bedId, patientId, patientName, bedNum) {
  if (patientId) {
    await dischargePatient(patientId, patientName, bedNum);
    await renderBedsTable();
  } else {
    // If no patient ID linked, simply transition bed status to Cleaning
    if (confirm(`Move bed ${bedNum} to Cleaning state?`)) {
      await fetch(`${API_BASE}/api/beds/${bedId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Cleaning' })
      });
      await renderBedsTable();
      await loadGlobalKPIs();
    }
  }
}

async function deleteBedById(bedId, bedNum) {
  if (confirm(`Are you sure you want to delete bed ${bedNum}?`)) {
    try {
      await fetch(`${API_BASE}/api/beds/${bedId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Deleted' })
      });
      await renderBedsTable();
      await loadGlobalKPIs();
    } catch (err) {
      console.error('Delete bed error:', err);
    }
  }
}

// -------------------------------------------------------------
// LOGIN, ALERTS & WARD HANDLERS
// -------------------------------------------------------------
function initLoginPage() {
  const loginForm = document.getElementById('loginForm');
  if (!loginForm) return;

  loginForm.onsubmit = async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const json = await res.json();
      if (json.success) {
        localStorage.setItem('sh_user', JSON.stringify(json.user));
        window.location.href = 'overview.html';
      } else {
        alert(json.message || 'Login failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      window.location.href = 'overview.html';
    }
  };
}

async function initAlertsPage() {
  try {
    const res = await fetch(`${API_BASE}/api/alerts`);
    const json = await res.json();
    if (json.success && json.data.length > 0) {
      console.log('Loaded alerts from database:', json.data.length);
    }
  } catch (err) {
    console.error('Error fetching alerts:', err);
  }
}

async function initDashboardPage() {
  try {
    const res = await fetch(`${API_BASE}/api/wards`);
    const json = await res.json();
    if (json.success) {
      console.log('Loaded wards from database:', json.data.length);
    }
  } catch (err) {
    console.error('Error fetching wards:', err);
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('active');
}
