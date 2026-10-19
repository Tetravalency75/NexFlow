/**
 * NEXFlow — Team Responsibility Management System
 * File: frontend/js/meetings.js
 * Description: Interactive Meetings & Minutes, Action Item Accountability Tracking
 */

document.addEventListener('DOMContentLoaded', () => {
  initMeetingTabs();
  initActionItemsCheckboxes();
  initScheduleMeetingForm();
});

/* --------------------------------------------------------------------------
   1. Meetings Upcoming vs Past Tabs
   -------------------------------------------------------------------------- */
function initMeetingTabs() {
  const tabs = document.querySelectorAll('.meeting-tab-btn');
  const upcomingList = document.getElementById('meetings-upcoming-list');
  const pastList = document.getElementById('meetings-past-list');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const target = tab.getAttribute('data-target');
      if (target === 'upcoming') {
        if (upcomingList) upcomingList.style.display = 'flex';
        if (pastList) pastList.style.display = 'none';
      } else {
        if (upcomingList) upcomingList.style.display = 'none';
        if (pastList) pastList.style.display = 'flex';
      }
    });
  });
}

/* --------------------------------------------------------------------------
   2. Action Items Accountability Checkboxes
   -------------------------------------------------------------------------- */
function initActionItemsCheckboxes() {
  document.querySelectorAll('.action-checkbox').forEach(box => {
    box.addEventListener('change', () => {
      const entry = box.closest('.action-item-entry');
      const text = entry?.querySelector('.action-item-text');
      if (box.checked) {
        if (text) text.style.textDecoration = 'line-through';
        showToast('Action item completed by owner!', 'success', 2000);
      } else {
        if (text) text.style.textDecoration = 'none';
        showToast('Action item reopened', 'info', 1500);
      }
    });
  });
}

/* --------------------------------------------------------------------------
   3. Schedule Meeting Form Submission
   -------------------------------------------------------------------------- */
function initScheduleMeetingForm() {
  const form = document.getElementById('schedule-meeting-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const title = document.getElementById('meeting-input-title').value.trim();
    const date = document.getElementById('meeting-input-date').value;
    const time = document.getElementById('meeting-input-time').value;

    if (!title) {
      showToast('Please enter meeting title', 'warning');
      return;
    }

    closeModal('modal-schedule-meeting');
    form.reset();
    showToast(`Meeting "${title}" scheduled for ${date} at ${time}! Calendar invites sent.`, 'success');
  });
}
