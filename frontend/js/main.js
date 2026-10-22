/**
 * NEXFlow — Team Responsibility Management System
 * File: frontend/js/main.js
 * Description: Core global interactions (Sidebar, Theme, Dropdowns, Modals, Toasts, User Roles, DatePicker)
 * Vanilla JavaScript (ES6+), zero external dependencies.
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSidebar();
  initDropdowns();
  initModals();
  initSearch();
  initActiveNavLink();
  initUserSession();
  initDatePickerHelper();
  initSettingsTabs();
});

/* --------------------------------------------------------------------------
   1. Theme Management (Light / Dark Mode)
   -------------------------------------------------------------------------- */
function initTheme() {
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const storedTheme = localStorage.getItem('nexflow-theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  // Set initial theme
  const initialTheme = storedTheme || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', initialTheme);
  updateThemeIcon(initialTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('nexflow-theme', newTheme);
      updateThemeIcon(newTheme);
      
      showToast(`Switched to ${newTheme} mode`, 'info', 2000);
    });
  }
}

function updateThemeIcon(theme) {
  const iconWrap = document.querySelector('#theme-toggle-btn .theme-icon');
  if (!iconWrap) return;

  if (theme === 'dark') {
    // Sun icon for switching back to light
    iconWrap.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
    `;
  } else {
    // Moon icon for switching to dark
    iconWrap.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    `;
  }
}

/* --------------------------------------------------------------------------
   2. Responsive Sidebar Management (Desktop Collapse & Mobile Drawer)
   -------------------------------------------------------------------------- */
function initSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  const sidebarCollapseBtn = document.getElementById('sidebar-collapse-btn');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const backdrop = document.getElementById('sidebar-backdrop');

  if (!sidebar) return;

  function toggleSidebarAction() {
    if (window.innerWidth <= 768) {
      sidebar.classList.toggle('mobile-open');
      if (backdrop) backdrop.classList.toggle('active', sidebar.classList.contains('mobile-open'));
    } else if (window.innerWidth <= 1024) {
      sidebar.classList.toggle('tablet-expanded');
      if (backdrop) backdrop.classList.toggle('active', sidebar.classList.contains('tablet-expanded'));
    } else {
      sidebar.classList.toggle('collapsed');
      const isCollapsed = sidebar.classList.contains('collapsed');
      localStorage.setItem('nexflow-sidebar-collapsed', isCollapsed ? 'true' : 'false');
    }
  }

  // Bind sidebar toggle button in header
  if (sidebarCollapseBtn) {
    sidebarCollapseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSidebarAction();
    });
  }

  // Fallback for mobile menu button if rendered separately
  if (mobileMenuBtn && mobileMenuBtn !== sidebarCollapseBtn) {
    mobileMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSidebarAction();
    });
  }

  // Restore desktop collapsed state before clearing preload class
  if (window.innerWidth > 1024 && localStorage.getItem('nexflow-sidebar-collapsed') === 'true') {
    sidebar.classList.add('collapsed');
  }

  // Clean up preload flag after state is fully restored
  document.documentElement.classList.remove('sidebar-collapsed-preload');

  // Backdrop click closes mobile & tablet expanded sidebar
  if (backdrop) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('mobile-open');
      sidebar.classList.remove('tablet-expanded');
      backdrop.classList.remove('active');
    });
  }

  // Auto-close mobile/tablet drawer on link click
  sidebar.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 1024) {
        sidebar.classList.remove('mobile-open');
        sidebar.classList.remove('tablet-expanded');
        if (backdrop) backdrop.classList.remove('active');
      }
    });
  });

  // Window resize cleanup
  window.addEventListener('resize', () => {
    if (window.innerWidth > 1024) {
      sidebar.classList.remove('mobile-open');
      sidebar.classList.remove('tablet-expanded');
      if (backdrop) backdrop.classList.remove('active');
    } else if (window.innerWidth > 768) {
      sidebar.classList.remove('mobile-open');
    }
  });
}

/* --------------------------------------------------------------------------
   3. Dropdowns Management (User Menu, Notifications, Quick Actions)
   -------------------------------------------------------------------------- */
function initDropdowns() {
  const dropdownTriggers = document.querySelectorAll('[data-dropdown-target]');

  dropdownTriggers.forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const targetId = trigger.getAttribute('data-dropdown-target');
      const targetMenu = document.getElementById(targetId);

      // Close other open dropdowns first
      document.querySelectorAll('.dropdown-menu.active').forEach(menu => {
        if (menu !== targetMenu) menu.classList.remove('active');
      });

      if (targetMenu) {
        targetMenu.classList.toggle('active');
      }
    });
  });

  // Close dropdowns when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown-menu') && !e.target.closest('[data-dropdown-target]')) {
      document.querySelectorAll('.dropdown-menu.active').forEach(menu => {
        menu.classList.remove('active');
      });
    }
  });

  // Auto-close dropdown menu when a dropdown-item is selected
  document.querySelectorAll('.dropdown-menu .dropdown-item').forEach(item => {
    item.addEventListener('click', () => {
      const menu = item.closest('.dropdown-menu');
      if (menu) menu.classList.remove('active');
    });
  });
}

/* --------------------------------------------------------------------------
   4. Modals Management (Open, Close, ESC Key, Backdrop Click)
   -------------------------------------------------------------------------- */
function initModals() {
  // Triggers with [data-modal-open="modalId"]
  document.querySelectorAll('[data-modal-open]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-modal-open');
      openModal(modalId);
    });
  });

  // Close buttons with [data-modal-close]
  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-backdrop');
      if (modal) closeModal(modal.id);
    });
  });

  // Backdrop click to close
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });

  // ESC key to close active modal (preserves date inputs, selects & textareas)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (document.activeElement && (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName))) {
        document.activeElement.blur();
        return;
      }
      const activeModal = document.querySelector('.modal-backdrop.active');
      if (activeModal) closeModal(activeModal.id);
    }
  });
}

window.openModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
};

window.closeModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
};

/* --------------------------------------------------------------------------
   5. Search Shortcut (Ctrl + K / Cmd + K)
   -------------------------------------------------------------------------- */
function initSearch() {
  const searchInput = document.getElementById('global-search-input');
  
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (searchInput) {
        searchInput.focus();
        showToast('Quick search activated', 'info', 1500);
      }
    }
  });

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      window.dispatchEvent(new CustomEvent('nexflow-search', { detail: { query } }));
    });
  }
}

/* --------------------------------------------------------------------------
   6. Active Navigation Link Detection (Sidebar links only)
   -------------------------------------------------------------------------- */
function initActiveNavLink() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href && currentPath.endsWith(href) && href !== '#') {
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
    }
  });
}

/* --------------------------------------------------------------------------
   7. Settings Section Navigation Tabs
   -------------------------------------------------------------------------- */
function initSettingsTabs() {
  const settingsLinks = document.querySelectorAll('.settings-nav .nav-link');
  if (!settingsLinks.length) return;

  function activateTabByHash(hash) {
    if (!hash || !hash.startsWith('#')) return;
    const targetLink = document.querySelector(`.settings-nav .nav-link[href="${hash}"]`);
    const targetCard = document.getElementById(hash.substring(1));
    if (targetLink) {
      settingsLinks.forEach(l => l.classList.remove('active'));
      targetLink.classList.add('active');
    }
    if (targetCard) {
      setTimeout(() => {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 50);
    }
  }

  settingsLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const href = link.getAttribute('href');
      activateTabByHash(href);
    });
  });

  if (window.location.hash) {
    activateTabByHash(window.location.hash);
  }
}

/* --------------------------------------------------------------------------
   8. Safe Date & Time Picker Interaction Helper
   -------------------------------------------------------------------------- */
function initDatePickerHelper() {
  document.querySelectorAll('input[type="date"], input[type="time"]').forEach(dateInput => {
    dateInput.addEventListener('click', function(e) {
      if (typeof this.showPicker === 'function') {
        try {
          this.showPicker();
        } catch (err) {
          // Fallback if picker is already showing or not allowed
        }
      }
    });
  });
}

/* --------------------------------------------------------------------------
   9. User Role Management & Session Persistence (Lead to Member switching)
   -------------------------------------------------------------------------- */
const NEXFLOW_DEFAULT_USERS = {
  'alex.morgan@nexflow.io': {
    name: 'Alex Morgan',
    email: 'alex.morgan@nexflow.io',
    role: 'Lead',
    roleTitle: 'Team Lead',
    avatar: '../images/avatar-1.svg'
  },
  'sarah.chen@nexflow.io': {
    name: 'Sarah Chen',
    email: 'sarah.chen@nexflow.io',
    role: 'Member',
    roleTitle: 'Team Member',
    avatar: '../images/avatar-2.svg'
  }
};

window.getCurrentUser = function() {
  try {
    const stored = localStorage.getItem('nexflow_user');
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (err) {
    console.error('Error reading nexflow_user from localStorage', err);
  }
  return NEXFLOW_DEFAULT_USERS['alex.morgan@nexflow.io'];
};

window.setCurrentUser = function(user) {
  try {
    localStorage.setItem('nexflow_user', JSON.stringify(user));
  } catch (err) {
    console.error('Error writing nexflow_user to localStorage', err);
  }
  applyUserSession(user);
};

window.switchUserRole = function(role) {
  const user = window.getCurrentUser();
  user.role = role;
  user.roleTitle = role === 'Lead' ? 'Team Lead' : 'Team Member';
  window.setCurrentUser(user);
  showToast(`Switched active role to ${user.roleTitle}`, 'success', 2500);
};

window.toggleUserRole = function() {
  const user = window.getCurrentUser();
  const nextRole = user.role === 'Lead' ? 'Member' : 'Lead';
  window.switchUserRole(nextRole);
};

function applyUserSession(user) {
  if (!user) user = window.getCurrentUser();

  // Update profile name, role badge, avatar in headers
  document.querySelectorAll('.user-name').forEach(el => {
    el.textContent = user.name;
  });
  document.querySelectorAll('.user-role-badge').forEach(el => {
    el.textContent = user.roleTitle;
  });
  document.querySelectorAll('.user-avatar').forEach(img => {
    if (user.avatar) img.src = user.avatar;
  });

  // Update team role pill in sidebar footer
  document.querySelectorAll('.team-role').forEach(el => {
    el.textContent = `${user.name} (${user.role})`;
  });

  // Update quick role toggle text in user dropdown
  document.querySelectorAll('.role-toggle-text').forEach(el => {
    el.textContent = user.role === 'Lead' ? 'Switch to Member Role' : 'Switch to Lead Role';
  });

  // Role-specific UI permissions
  document.querySelectorAll('[data-role-required="Lead"]').forEach(el => {
    if (user.role === 'Member') {
      el.style.display = 'none';
    } else {
      el.style.display = '';
    }
  });

  // Matrix table readonly state for Members
  const matrixTable = document.querySelector('.matrix-table');
  if (matrixTable) {
    if (user.role === 'Member') {
      matrixTable.classList.add('role-member-readonly');
    } else {
      matrixTable.classList.remove('role-member-readonly');
    }
  }

  // Member-specific notification indicator
  const memberIndicator = document.getElementById('role-indicator-banner');
  if (memberIndicator) {
    if (user.role === 'Member') {
      memberIndicator.style.display = 'flex';
      memberIndicator.textContent = 'Viewing as Team Member (Standard contributor permissions)';
    } else {
      memberIndicator.style.display = 'none';
    }
  }

  // Populate profile inputs in Settings if active on settings page
  const profileNameInput = document.getElementById('profile-name-input');
  const profileEmailInput = document.getElementById('profile-email-input');
  const profileRoleSelect = document.getElementById('profile-role-select');

  if (profileNameInput) profileNameInput.value = user.name;
  if (profileEmailInput) profileEmailInput.value = user.email;
  if (profileRoleSelect) profileRoleSelect.value = user.role;
}

function initUserSession() {
  const user = window.getCurrentUser();
  applyUserSession(user);
}

/* --------------------------------------------------------------------------
   10. Global Toast Notification Helper
   -------------------------------------------------------------------------- */
window.showToast = function(message, type = 'info', duration = 3000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let iconSvg = '';
  if (type === 'success') {
    iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
  } else if (type === 'danger') {
    iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
  } else if (type === 'warning') {
    iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
  } else {
    iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
  }

  toast.innerHTML = `
    <span class="toast-icon">${iconSvg}</span>
    <span class="toast-message" style="flex:1;">${message}</span>
    <button class="toast-close-btn" style="color:var(--text-muted);font-size:16px;line-height:1;cursor:pointer;">&times;</button>
  `;

  const closeBtn = toast.querySelector('.toast-close-btn');
  closeBtn.addEventListener('click', () => {
    toast.remove();
  });

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
};
