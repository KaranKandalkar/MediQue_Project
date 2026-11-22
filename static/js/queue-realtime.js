/**
 * MediQueue - Real-time Queue Polling & Dynamic UI Interaction
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle
  const sidebarToggler = document.getElementById('sidebarToggler');
  const sidebar = document.querySelector('.app-sidebar');
  let backdrop = document.querySelector('.sidebar-backdrop');

  if (sidebarToggler && sidebar) {
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.className = 'sidebar-backdrop';
      document.body.appendChild(backdrop);
    }

    sidebarToggler.addEventListener('click', function () {
      sidebar.classList.toggle('show');
      backdrop.classList.toggle('show');
    });

    backdrop.addEventListener('click', function () {
      sidebar.classList.remove('show');
      backdrop.classList.remove('show');
    });
  }

  // 2. Department to Doctor cascading dropdown (in Booking and Token Forms)
  const deptSelect = document.getElementById('id_department_select') || document.getElementById('id_department_token');
  const docSelect = document.getElementById('id_doctor_select') || document.getElementById('id_doctor_token');

  if (deptSelect && docSelect) {
    deptSelect.addEventListener('change', function () {
      const deptId = this.value;
      if (!deptId) return;

      fetch(`/doctors/api/by-department/?department_id=${deptId}`)
        .then(response => response.json())
        .then(data => {
          docSelect.innerHTML = '<option value="">-- Select Doctor --</option>';
          data.doctors.forEach(doc => {
            const opt = document.createElement('option');
            opt.value = doc.id;
            opt.textContent = `${doc.name} (${doc.specialization}) - Room ${doc.room || 'TBD'}`;
            docSelect.appendChild(opt);
          });
        })
        .catch(err => console.error("Error loading doctors:", err));
    });
  }

  // 3. Quick Doctor Availability Toggle Buttons
  document.querySelectorAll('.btn-toggle-availability').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const docId = this.getAttribute('data-doctor-id');
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');

      fetch(`/doctors/${docId}/toggle-availability/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json'
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          window.location.reload();
        }
      })
      .catch(err => console.error("Error toggling availability:", err));
    });
  });

  // 4. Auto Polling for Live Public Lobby Display Screen (if on /queue/display/)
  const lobbyBoardContainer = document.getElementById('lobbyBoardContainer');
  if (lobbyBoardContainer) {
    setInterval(pollLobbyBoard, 6000);
  }

  // 5. Patient Live Token Tracker (if on patient dashboard or token detail)
  const tokenTracker = document.getElementById('patientLiveTokenTracker');
  if (tokenTracker) {
    const tokenId = tokenTracker.getAttribute('data-token-id');
    if (tokenId) {
      setInterval(() => pollPatientToken(tokenId), 6000);
    }
  }
});

function pollLobbyBoard() {
  fetch('/queue/api/lobby-board/')
    .then(res => res.json())
    .then(payload => {
      if (payload.status === 'success' && payload.data) {
        updateLobbyUI(payload.data, payload.updated_at);
      }
    })
    .catch(err => console.error("Lobby poll error:", err));
}

function updateLobbyUI(doctors, updatedAt) {
  const timeElem = document.getElementById('lobbyLastUpdated');
  if (timeElem && updatedAt) {
    timeElem.textContent = updatedAt;
  }

  doctors.forEach(doc => {
    const card = document.getElementById(`doc-display-card-${doc.doctor_id}`);
    if (card) {
      const curElem = card.querySelector('.display-cur-token');
      const statusElem = card.querySelector('.display-cur-status');
      const waitCountElem = card.querySelector('.display-wait-count');
      const nextListElem = card.querySelector('.display-next-list');
      const servingBox = card.querySelector('.display-serving-box');

      if (curElem) curElem.textContent = doc.current_token;
      if (statusElem) statusElem.textContent = doc.current_status;
      if (waitCountElem) waitCountElem.textContent = doc.waiting_count;

      if (servingBox) {
        if (doc.current_is_emergency) {
          servingBox.classList.add('emergency');
        } else {
          servingBox.classList.remove('emergency');
        }
      }

      if (nextListElem) {
        if (doc.next_tokens.length === 0) {
          nextListElem.innerHTML = '<span class="text-secondary small">No patients waiting</span>';
        } else {
          nextListElem.innerHTML = doc.next_tokens.map(t => 
            `<span class="badge ${t.is_emergency ? 'bg-danger text-white' : 'bg-secondary'} me-1 p-2 fs-6">
               ${t.token_number} ${t.is_emergency ? '<i class="bi bi-exclamation-triangle-fill ms-1"></i>' : ''}
             </span>`
          ).join(' ');
        }
      }
    }
  });
}

function pollPatientToken(tokenId) {
  fetch(`/queue/api/patient-token-status/?token_id=${tokenId}`)
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        const posElem = document.getElementById('tokenLivePosition');
        const waitElem = document.getElementById('tokenLiveWait');
        const servingElem = document.getElementById('tokenLiveCurrentServing');
        const statusBadge = document.getElementById('tokenLiveStatusBadge');

        if (posElem) posElem.textContent = data.position > 0 ? `#${data.position}` : 'Called / In Room';
        if (waitElem) waitElem.textContent = `~${data.estimated_wait_time} mins`;
        if (servingElem) servingElem.textContent = data.current_serving_token || 'None';
        if (statusBadge) statusBadge.textContent = data.token_status;

        // If called, alert the user
        if (data.token_status === 'Called to Room' || data.token_status === 'In Consultation') {
          const alertBox = document.getElementById('patientTokenAlert');
          if (alertBox) {
            alertBox.classList.remove('d-none');
            alertBox.innerHTML = `<strong>Attention:</strong> Your token is currently being called to Room ${data.room_number || ''}! Please proceed immediately.`;
          }
        }
      }
    })
    .catch(err => console.error("Patient token poll error:", err));
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
