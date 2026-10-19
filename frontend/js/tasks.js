/**
 * NEXFlow — Team Responsibility Management System
 * File: frontend/js/tasks.js
 * Description: Interactive Task Management, Kanban Board Drag & Drop, Filtering,
 *              and New Responsibility Assignment.
 */

document.addEventListener('DOMContentLoaded', () => {
  initViewSwitcher();
  initKanbanDragAndDrop();
  initTaskCheckboxes();
  initNewTaskForm();
  initTaskFilters();
});

/* --------------------------------------------------------------------------
   1. Board vs List View Switcher
   -------------------------------------------------------------------------- */
function initViewSwitcher() {
  const boardBtn = document.getElementById('view-board-btn');
  const listBtn = document.getElementById('view-list-btn');
  const kanbanBoard = document.getElementById('kanban-board');
  const listView = document.getElementById('tasks-list-view');

  if (!boardBtn || !listBtn) return;

  boardBtn.addEventListener('click', () => {
    boardBtn.classList.add('active');
    listBtn.classList.remove('active');
    if (kanbanBoard) kanbanBoard.classList.remove('hidden');
    if (listView) listView.classList.remove('active');
  });

  listBtn.addEventListener('click', () => {
    listBtn.classList.add('active');
    boardBtn.classList.remove('active');
    if (kanbanBoard) kanbanBoard.classList.add('hidden');
    if (listView) listView.classList.add('active');
  });
}

/* --------------------------------------------------------------------------
   2. HTML5 Drag and Drop for Kanban Columns
   -------------------------------------------------------------------------- */
function initKanbanDragAndDrop() {
  const cards = document.querySelectorAll('.task-card');
  const cardLists = document.querySelectorAll('.kanban-card-list');

  cards.forEach(card => {
    card.setAttribute('draggable', 'true');

    card.addEventListener('dragstart', (e) => {
      card.classList.add('dragging');
      e.dataTransfer.setData('text/plain', card.id || 'card');
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      updateColumnCounters();
    });
  });

  cardLists.forEach(list => {
    list.addEventListener('dragover', (e) => {
      e.preventDefault();
      const afterElement = getDragAfterElement(list, e.clientY);
      const draggingCard = document.querySelector('.dragging');
      if (draggingCard) {
        if (afterElement == null) {
          list.appendChild(draggingCard);
        } else {
          list.insertBefore(draggingCard, afterElement);
        }
      }
    });

    list.addEventListener('drop', (e) => {
      e.preventDefault();
      const colTitle = list.closest('.kanban-column').querySelector('.kanban-col-title').textContent.trim();
      showToast(`Task moved to ${colTitle}`, 'success', 2000);
      updateColumnCounters();
    });
  });
}

function getDragAfterElement(container, y) {
  const draggableElements = [...container.querySelectorAll('.task-card:not(.dragging)')];

  return draggableElements.reduce((closest, child) => {
    const box = child.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > closest.offset) {
      return { offset: offset, element: child };
    } else {
      return closest;
    }
  }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function updateColumnCounters() {
  document.querySelectorAll('.kanban-column').forEach(column => {
    const count = column.querySelectorAll('.task-card').length;
    const counterBadge = column.querySelector('.kanban-col-count');
    if (counterBadge) counterBadge.textContent = count;
  });
}

/* --------------------------------------------------------------------------
   3. Interactive Task Checkboxes
   -------------------------------------------------------------------------- */
function initTaskCheckboxes() {
  document.querySelectorAll('.task-checkbox-custom').forEach(box => {
    box.addEventListener('click', (e) => {
      e.stopPropagation();
      box.classList.toggle('checked');
      const isCompleted = box.classList.contains('checked');
      const row = box.closest('.task-item-row');
      
      if (row) {
        const title = row.querySelector('.task-row-title');
        if (isCompleted) {
          title.style.textDecoration = 'line-through';
          title.style.color = 'var(--text-muted)';
          showToast('Responsibility marked completed!', 'success', 2000);
        } else {
          title.style.textDecoration = 'none';
          title.style.color = 'var(--text-primary)';
          showToast('Task reopened', 'info', 1500);
        }
      }
    });
  });
}

/* --------------------------------------------------------------------------
   4. New Task Modal & Form Submission
   -------------------------------------------------------------------------- */
function initNewTaskForm() {
  const form = document.getElementById('new-task-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const title = document.getElementById('task-input-title').value.trim();
    const raciRole = document.getElementById('task-input-raci').value;
    const priority = document.getElementById('task-input-priority').value;
    const assignee = document.getElementById('task-input-assignee').value;
    const dueDate = document.getElementById('task-input-due').value;

    if (!title) {
      showToast('Please enter a task title', 'warning');
      return;
    }

    // Determine RACI badge classes
    let raciClass = 'badge-raci-r';
    let raciLabel = 'R - Responsible';
    if (raciRole === 'A') { raciClass = 'badge-raci-a'; raciLabel = 'A - Accountable'; }
    else if (raciRole === 'C') { raciClass = 'badge-raci-c'; raciLabel = 'C - Consulted'; }
    else if (raciRole === 'I') { raciClass = 'badge-raci-i'; raciLabel = 'I - Informed'; }

    // Create New Task Card in To Do Column
    const newCard = document.createElement('div');
    newCard.className = 'task-card';
    newCard.setAttribute('draggable', 'true');
    newCard.innerHTML = `
      <div class="task-card-tags">
        <span class="badge ${raciClass}">${raciLabel}</span>
        <span class="badge badge-${priority.toLowerCase()}">${priority}</span>
      </div>
      <h4 class="task-card-title">${title}</h4>
      <p class="task-card-desc">Assigned to ${assignee}. Added to current sprint workload.</p>
      <div class="task-card-footer">
        <span class="task-date">📅 ${dueDate || 'Tomorrow'}</span>
        <div class="avatar-stack">
          <img src="../images/avatar-1.svg" class="avatar-item" alt="Assignee">
        </div>
      </div>
    `;

    // Append to "To Do" or "Backlog" column
    const backlogCol = document.querySelector('.col-backlog .kanban-card-list');
    if (backlogCol) {
      backlogCol.prepend(newCard);
    }

    // Rebind drag & drop
    initKanbanDragAndDrop();
    updateColumnCounters();

    // Close modal & reset form
    closeModal('modal-new-task');
    form.reset();
    showToast(`Task "${title}" created and assigned!`, 'success');
  });
}

/* --------------------------------------------------------------------------
   5. Task Filters (Priority & RACI Role)
   -------------------------------------------------------------------------- */
function initTaskFilters() {
  const filterPriority = document.getElementById('filter-priority');
  const filterRaci = document.getElementById('filter-raci');

  function applyFilters() {
    const priorityVal = filterPriority ? filterPriority.value.toLowerCase() : 'all';
    const raciVal = filterRaci ? filterRaci.value.toLowerCase() : 'all';

    document.querySelectorAll('.task-card').forEach(card => {
      const cardPriority = card.querySelector('.badge-priority, [class*="badge-urgent"], [class*="badge-high"], [class*="badge-medium"], [class*="badge-low"]')?.textContent.toLowerCase() || '';
      const cardRaci = card.querySelector('[class*="badge-raci"]')?.textContent.toLowerCase() || '';

      const matchPriority = priorityVal === 'all' || cardPriority.includes(priorityVal);
      const matchRaci = raciVal === 'all' || cardRaci.startsWith(raciVal);

      if (matchPriority && matchRaci) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });
  }

  if (filterPriority) filterPriority.addEventListener('change', applyFilters);
  if (filterRaci) filterRaci.addEventListener('change', applyFilters);
}
