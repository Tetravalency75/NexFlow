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

  let isSubmitting = false;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const titleInput = document.getElementById('task-input-title');
    const title = titleInput ? titleInput.value.trim() : '';

    if (!title) {
      showToast('Please enter a task title', 'warning');
      return;
    }

    const assigneeSelect = document.getElementById('task-input-assignee');
    if (!assigneeSelect || !assigneeSelect.value) {
      showToast('Please select a valid assignee from the team', 'warning');
      return;
    }

    isSubmitting = true;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.innerHTML : 'Create & Assign';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>Saving...</span>';
    }

    try {
      const formData = new FormData(form);
      const actionUrl = form.getAttribute('action') || '/tasks/create/';

      const response = await fetch(actionUrl, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: formData,
      });

      const data = await response.json().catch(() => null);

      if (response.ok && data && data.success) {
        showToast(`Task "${data.task ? data.task.title : title}" created and saved to database!`, 'success');
        if (typeof closeModal === 'function') {
          closeModal('modal-new-task');
        }
        form.reset();

        // Refresh page so all dashboard/Kanban database queries reflect the new task
        setTimeout(() => {
          window.location.reload();
        }, 600);
      } else {
        // Handle backend error details
        let errorMsg = 'Failed to save task to database.';
        if (data && data.error) {
          errorMsg = data.error;
        } else if (data && data.errors) {
          const fieldErrors = Object.entries(data.errors)
            .map(([field, errs]) => `${field}: ${Array.isArray(errs) ? errs.join(', ') : errs}`)
            .join(' | ');
          errorMsg = `Validation error: ${fieldErrors}`;
        }
        showToast(errorMsg, 'danger', 4000);
      }
    } catch (err) {
      console.error('Task creation network error:', err);
      showToast('Network error while saving task to server. Please try again.', 'danger');
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
      }
    }
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
