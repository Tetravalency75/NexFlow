/**
 * NEXFlow — Team Responsibility Management System
 * File: frontend/js/matrix.js
 * Description: Interactive RACI Responsibility Matrix Grid interactions,
 *              click-to-cycle RACI roles, and live workload updates.
 */

document.addEventListener('DOMContentLoaded', () => {
  initRaciMatrixCells();
  initAddMemberForm();
});

/* --------------------------------------------------------------------------
   1. Interactive RACI Grid Role Cycler
   -------------------------------------------------------------------------- */
function initRaciMatrixCells() {
  const cells = document.querySelectorAll('.matrix-cell');

  cells.forEach(cell => {
    cell.addEventListener('click', () => {
      const currentRole = cell.getAttribute('data-raci-role') || '';
      let nextRole = '';

      // Cycle order: None -> R -> A -> C -> I -> None
      if (currentRole === '') nextRole = 'R';
      else if (currentRole === 'R') nextRole = 'A';
      else if (currentRole === 'A') nextRole = 'C';
      else if (currentRole === 'C') nextRole = 'I';
      else if (currentRole === 'I') nextRole = '';

      updateCellRole(cell, nextRole);
      
      const memberName = cell.getAttribute('data-member') || 'Member';
      const deliverable = cell.closest('tr')?.querySelector('.deliverable-title')?.textContent.trim() || 'Deliverable';
      
      if (nextRole) {
        showToast(`${memberName} assigned as ${getRaciFullName(nextRole)} for "${deliverable}"`, 'info', 2000);
      } else {
        showToast(`Role cleared for ${memberName}`, 'info', 1500);
      }

      updateMatrixSummaryStats();
    });
  });
}

function updateCellRole(cell, role) {
  cell.setAttribute('data-raci-role', role);

  if (!role) {
    cell.innerHTML = `<span class="matrix-role-empty">—</span>`;
    return;
  }

  let badgeClass = 'badge-raci-r';
  if (role === 'A') badgeClass = 'badge-raci-a';
  else if (role === 'C') badgeClass = 'badge-raci-c';
  else if (role === 'I') badgeClass = 'badge-raci-i';

  cell.innerHTML = `<span class="matrix-role-badge ${badgeClass}">${role}</span>`;
}

function getRaciFullName(roleKey) {
  switch (roleKey) {
    case 'R': return 'Responsible (R)';
    case 'A': return 'Accountable (A)';
    case 'C': return 'Consulted (C)';
    case 'I': return 'Informed (I)';
    default: return '';
  }
}

function updateMatrixSummaryStats() {
  let countR = 0, countA = 0, countC = 0, countI = 0;

  document.querySelectorAll('.matrix-cell').forEach(cell => {
    const role = cell.getAttribute('data-raci-role');
    if (role === 'R') countR++;
    else if (role === 'A') countA++;
    else if (role === 'C') countC++;
    else if (role === 'I') countI++;
  });

  const statR = document.getElementById('matrix-stat-r');
  const statA = document.getElementById('matrix-stat-a');
  const statC = document.getElementById('matrix-stat-c');
  const statI = document.getElementById('matrix-stat-i');

  if (statR) statR.textContent = countR;
  if (statA) statA.textContent = countA;
  if (statC) statC.textContent = countC;
  if (statI) statI.textContent = countI;
}

/* --------------------------------------------------------------------------
   2. Add Member Form Submission
   -------------------------------------------------------------------------- */
function initAddMemberForm() {
  const form = document.getElementById('add-member-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('member-input-name').value.trim();
    const role = document.getElementById('member-input-role').value.trim();

    if (!name) {
      showToast('Please enter member name', 'warning');
      return;
    }

    closeModal('modal-add-member');
    form.reset();
    showToast(`Team member "${name}" (${role}) invited successfully!`, 'success');
  });
}
