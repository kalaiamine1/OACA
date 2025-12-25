// Shared Header Component for OACA
// This file provides a consistent header across all pages

(function() {
  'use strict';

  // Get current page to highlight active nav link
  function getCurrentPage() {
    const path = window.location.pathname;
    if (path === '/' || path === '/home' || path.endsWith('/home.html')) return 'home';
    if (path.endsWith('/about.html')) return 'about';
    return '';
  }

  // Render header HTML
  function renderHeader() {
    const currentPage = getCurrentPage();
    const headerHTML = `
      <header class="header">
        <nav class="nav-container">
          <a href="/home" class="logo">
            <img src="/oaca.png" alt="OACA Logo" class="logo-icon">
            <span class="logo-text">OACA</span>
          </a>
          <div class="nav-links" id="mainNavLinks">
            <a href="/home" class="nav-link ${currentPage === 'home' ? 'active' : ''}">ACCUEIL</a>
            <a href="/about.html" class="nav-link ${currentPage === 'about' ? 'active' : ''}">A PROPOS</a>
            <a href="#footer" class="nav-link">CONTACT</a>
          </div>
          <div class="auth-buttons" id="authArea" style="visibility:hidden"></div>
        </nav>
      </header>
    `;
    
    // Insert header at the beginning of body (after background airplanes if they exist)
    const headerPlaceholder = document.getElementById('header-placeholder');
    if (headerPlaceholder) {
      headerPlaceholder.innerHTML = headerHTML;
    } else {
      // Fallback: insert after body opens
      const body = document.body;
      const firstElement = body.firstElementChild;
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = headerHTML;
      body.insertBefore(tempDiv.firstElementChild, firstElement);
    }
  }

  // Initialize authentication UI
  async function initAuth() {
    try {
      const res = await fetch('/api/me', { credentials: 'include' });
      const auth = document.getElementById('authArea');
      if (!auth) return;

      if (res.ok) {
        const me = await res.json();
        const initials = (me.email || 'U').slice(0, 1).toUpperCase();
        
        // Check if user has remaining attempts and show Quiz link
        try {
          const attRes = await fetch(`/api/user-attempts/${encodeURIComponent(me.email)}`, { credentials: 'include' });
          if (attRes.ok) {
            const att = await attRes.json();
            const remaining = att.remaining_attempts !== undefined ? att.remaining_attempts : Math.max(0, 3 - (att.attempts_used || 0));
            const hasPassed = att.passed === true;
            
            // Show Quiz link if user has attempts remaining AND hasn't passed
            // Once passed, quiz is no longer available (removed from header)
            if (remaining > 0 && !hasPassed) {
              const nav = document.getElementById('mainNavLinks');
              if (nav && !nav.querySelector('#quizNavLink')) {
                const a = document.createElement('a');
                a.className = 'nav-link';
                a.id = 'quizNavLink';
                a.textContent = 'QUIZ';
                a.href = '/quiz_guide.html';
                nav.appendChild(a);
              }
            }
          }
        } catch (_) {
          // If attempt check fails, don't show quiz link for safety
        }
        
        // Add Test History link even if no assignments check (for users who completed tests)
        try {
          const nav = document.getElementById('mainNavLinks');
          if (nav && !nav.querySelector('#testHistoryNavLink')) {
            const historyLink = document.createElement('a');
            historyLink.className = 'nav-link';
            historyLink.id = 'testHistoryNavLink';
            historyLink.textContent = 'TEST HISTORY';
            historyLink.href = '/testhistory';
            nav.appendChild(historyLink);
          }
        } catch (_) {}

        // Render authenticated user UI
        auth.innerHTML = `
          <div class="inbox-wrap">
            <button class="inbox-btn" id="inboxBtn">🔔</button>
            <div class="inbox-list" id="inboxList"></div>
          </div>
          <div class="avatar-wrap">
            <button class="avatar-btn" id="avatarBtn">${initials}</button>
            <div class="avatar-menu" id="avatarMenu">
              <button id="openProfile">Profile</button>
              <button id="resetPwd">Reset Password</button>
              <button id="logoutBtn">Logout</button>
            </div>
          </div>
        `;
        auth.style.visibility = 'visible';
        
        // If user has avatar, replace initials with image
        if (me.avatar_url) {
          const avatarBtn = document.getElementById('avatarBtn');
          if (avatarBtn) {
            avatarBtn.style.backgroundImage = `url('${me.avatar_url}')`;
            avatarBtn.style.backgroundSize = 'cover';
            avatarBtn.style.backgroundPosition = 'center';
            avatarBtn.textContent = '';
          }
        }

        // Setup logout
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
          logoutBtn.addEventListener('click', async () => {
            try {
              await fetch('/api/logout', { method: 'POST', credentials: 'include' });
            } finally {
              window.location.href = '/home';
            }
          });
        }

        // Setup avatar dropdown
        const avatarBtn = document.getElementById('avatarBtn');
        const menu = document.getElementById('avatarMenu');
        const avatarWrap = document.querySelector('.avatar-wrap');
        if (avatarBtn && menu && avatarWrap) {
          let hideTimer = null;
          const showMenu = () => {
            if (hideTimer) {
              clearTimeout(hideTimer);
              hideTimer = null;
            }
            menu.style.display = 'flex';
          };
          const scheduleHide = () => {
            if (hideTimer) clearTimeout(hideTimer);
            hideTimer = setTimeout(() => {
              menu.style.display = 'none';
            }, 180);
          };
          avatarWrap.addEventListener('mouseenter', showMenu);
          avatarWrap.addEventListener('mouseleave', scheduleHide);
          menu.addEventListener('mouseenter', showMenu);
          menu.addEventListener('mouseleave', scheduleHide);
        }

        // Setup profile modal trigger
        const openProfile = document.getElementById('openProfile');
        if (openProfile) {
          openProfile.addEventListener('click', () => {
            const event = new CustomEvent('openProfileModal');
            window.dispatchEvent(event);
          });
        }

        // Setup password change modal trigger
        const resetPwd = document.getElementById('resetPwd');
        if (resetPwd) {
          resetPwd.addEventListener('click', () => {
            const event = new CustomEvent('openChangePwdModal');
            window.dispatchEvent(event);
          });
        }

        // Setup notifications inbox
        const inboxBtn = document.getElementById('inboxBtn');
        const inboxList = document.getElementById('inboxList');
        if (inboxBtn && inboxList) {
          inboxBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (inboxList.style.display === 'flex') {
              inboxList.style.display = 'none';
              return;
            }
            try {
              const resN = await fetch('/api/notifications', { credentials: 'include' });
              const rows = resN.ok ? await resN.json() : [];
              const header = '<div class="inbox-header"><div class="inbox-title">Notifications</div></div>';
              if (!rows.length) {
                inboxList.innerHTML = header + '<div class="inbox-item"><div class="message">No notifications</div></div>';
              } else {
                inboxList.innerHTML = header + rows.map(n => {
                  const clickable = (n.type === 'quiz_assignment' && n.assignment_id);
                  const body = `<div class="inbox-item ${n.read ? '' : 'unread'}" ${clickable ? `data-assignment-id="${n.assignment_id}"` : ''}><div class="title">${n.title || 'Notification'}</div><div class="message">${n.message || ''}</div><div class="time">${(n.created_at || '').toString()}</div></div>`;
                  return body;
                }).join('');
                
                // Attach click handlers to quiz_assignment items
                Array.from(inboxList.querySelectorAll('.inbox-item[data-assignment-id]')).forEach(el => {
                  el.addEventListener('click', () => {
                    const id = el.getAttribute('data-assignment-id');
                    if (id) window.location.href = `/quiz_guide.html?assignment_id=${encodeURIComponent(id)}`;
                  });
                });
              }
              inboxList.style.display = 'flex';
              await fetch('/api/notifications/read', { method: 'POST', credentials: 'include' });
            } catch (_) {
              inboxList.innerHTML = '<div class="inbox-item">Failed to load</div>';
              inboxList.style.display = 'flex';
            }
          });
          document.addEventListener('click', () => {
            inboxList.style.display = 'none';
          });
        }
      } else {
        // Not authenticated - show login/signup buttons
        auth.innerHTML = `
          <a href="/login" class="btn btn-secondary">Login</a>
          <a href="/signup" class="btn btn-primary">Sign Up</a>
        `;
        auth.style.visibility = 'visible';
      }
    } catch (_) {
      // Error - show login/signup as fallback
      const auth = document.getElementById('authArea');
      if (auth) {
        auth.innerHTML = `
          <a href="/login" class="btn btn-secondary">Login</a>
          <a href="/signup" class="btn btn-primary">Sign Up</a>
        `;
        auth.style.visibility = 'visible';
      }
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      renderHeader();
      initAuth();
    });
  } else {
    renderHeader();
    initAuth();
  }
})();

