(() => {
  const emailEl = document.getElementById('email');
  const pwdEl = document.getElementById('password');
  const btn = document.getElementById('loginBtn');
  const err = document.getElementById('error');

  function showError(msg) {
    err.textContent = msg || 'Login failed';
    err.style.display = 'block';
  }

  async function login() {
    err.style.display = 'none';
    const email = String(emailEl.value || '').trim();
    const password = String(pwdEl.value || '');
    if (!email || !password) {
      showError('Please enter email and password.');
      return;
    }
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        showError(data.error || 'Invalid credentials');
        return;
      }
      // Redirect by role after successful login
      try {
        const meRes = await fetch('/api/me', { credentials: 'include' });
        if (meRes.ok) {
          const me = await meRes.json();
          if (me.role === 'admin') {
            window.location.href = '/dashboard.html';
          } else {
            window.location.href = '/home.html';
          }
          return;
        }
      } catch (_) {}
      // Fallback
      window.location.href = '/home.html';
    } catch (e) {
      showError(String(e));
    }
  }

  btn.addEventListener('click', login);
  pwdEl.addEventListener('keydown', (e) => { if (e.key === 'Enter') login(); });
})();


