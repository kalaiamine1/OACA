// Protect page: redirect to login if not authenticated
;(async () => {
  try {
    const res = await fetch("/api/me", { credentials: "include" })
    if (!res.ok) {
      window.location.href = "/login.html"
      return
    }
    const me = await res.json()
    // Set label immediately if element exists
    const who = document.getElementById("who")
    if (who) {
      who.textContent = `${me.email} (${me.role})`
    } else {
      document.addEventListener("DOMContentLoaded", () => {
        const w2 = document.getElementById("who")
        if (w2) w2.textContent = `${me.email} (${me.role})`
      })
    }
    // Initialize tabs right away
    setupTabs(me.role)
    // If user has no attempts left, hide Quiz tab from header
    try {
      if (me.role !== "admin") {
        const attRes = await fetch(`/api/user-attempts/${encodeURIComponent(me.email)}`, { credentials: "include" })
        if (attRes.ok) {
          const att = await attRes.json()
          const remaining =
            typeof att.remaining_attempts === "number"
              ? att.remaining_attempts
              : Math.max(0, 3 - (att.attempts_used || 0))
          if (remaining <= 0) {
            const tabQuiz = document.getElementById("tab-quiz")
            const sectionQuiz = document.getElementById("section-quiz")
            if (tabQuiz) tabQuiz.style.display = "none"
            if (sectionQuiz) sectionQuiz.style.display = "none"
            // Optionally show report tab instead
            const tabReport = document.getElementById("tab-report")
            if (tabReport) tabReport.classList.remove("disabled")
            const secReport = document.getElementById("section-report")
            if (secReport) secReport.classList.add("active")
            if (tabReport) tabReport.classList.add("active")
          }
        }
      }
    } catch (_) {}
  } catch (e) {
    window.location.href = "/login.html"
  }
})()

function setupTabs(role) {
  const tabs = {
    users: document.getElementById("tab-users"),
    questions: document.getElementById("tab-questions"),
    sections: document.getElementById("tab-sections"),
    quiz: document.getElementById("tab-quiz"),
    assignments: document.getElementById("tab-assignments"),
    report: document.getElementById("tab-report"),
  }
  const sections = {
    users: document.getElementById("section-users"),
    questions: document.getElementById("section-questions"),
    sections: document.getElementById("section-sections"),
    quiz: document.getElementById("section-quiz"),
    assignments: document.getElementById("section-assignments"),
    report: document.getElementById("section-report"),
  }

  if (!tabs.users || !sections.users) return

  // Limit access for non-admins
  if (role !== "admin") {
    tabs.users.classList.add("disabled")
    tabs.questions.classList.add("disabled")
    tabs.sections.classList.add("disabled")
    tabs.report.classList.add("disabled")
  }

  function activate(name) {
    for (const key of Object.keys(sections)) {
      sections[key].classList.toggle("active", key === name)
      tabs[key].classList.toggle("active", key === name)
    }

    // Special handling for users tab - show airport selection modal if no airport is selected
    if (name === "users" && role === "admin") {
      // Check if an airport is already selected
      const selectedAirport = sessionStorage.getItem('selectedAirport')
      if (!selectedAirport) {
        setTimeout(() => showAirportSelectionModal(), 100) // Small delay to ensure UI is rendered
      }
    }
  }

  // Default active tab
  activate(role === "admin" ? "users" : "quiz")

  tabs.users.addEventListener("click", () => activate("users"))
  tabs.questions.addEventListener("click", () => activate("questions"))
  tabs.sections.addEventListener("click", () => activate("sections"))
  tabs.quiz.addEventListener("click", () => activate("quiz"))
  tabs.assignments.addEventListener("click", () => activate("assignments"))
  tabs.report.addEventListener("click", () => activate("report"))
}

function showToast(message, type) {
  const el = document.getElementById("toast")
  if (!el) return
  el.className = ""
  el.classList.add(type === "error" ? "error" : "success")
  el.id = "toast"
  el.textContent = message || ""
  el.style.display = "block"
  clearTimeout(window.__toastTimer)
  window.__toastTimer = setTimeout(() => {
    el.style.display = "none"
  }, 2600)
}

async function logout() {
  try {
    await fetch("/api/logout", { method: "POST", credentials: "include" })
  } finally {
    window.location.href = "/login.html"
  }
}

// Create user and send welcome email with credentials
async function createUser() {
  const emailEl = document.getElementById("newUserEmail")
  const roleEl = document.getElementById("newUserRole")
  const airportEl = document.getElementById("newUserAirport")
  const btn = document.querySelector("#section-users .form-section .form-actions-container .btn")

  const email = (emailEl?.value || "").trim().toLowerCase()
  const role = (roleEl?.value || "user").trim()
  const airport = (airportEl?.value || "").trim()

  // basic validation
  const emailOk = /.+@.+\..+/.test(email)
  if (!emailOk) {
    showToast("Valid email is required", "error")
    return
  }

  const prev = btn ? btn.textContent : ""
  if (btn) { btn.disabled = true; btn.textContent = "Creating..." }
  try {
    const res = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, role, airport })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      showToast(data.error || "Failed to create user", "error")
      return
    }
    showToast(data.message || "User created", "success")
    // clear inputs
    if (emailEl) emailEl.value = ""
    if (roleEl) roleEl.value = "user"
    if (airportEl) airportEl.value = ""
    // refresh user lists and assignment candidates
    try { await loadUsers() } catch(_) {}
    try { await loadUsersForAssign() } catch(_) {}
  } catch (e) {
    showToast(String(e), "error")
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = prev || "Create User & Send Email" }
  }
}

// Create user for a specific airport
async function createUserForAirport(airportName) {
  const safeId = airportName.replace(/[^a-zA-Z0-9]/g, '_')
  const emailEl = document.getElementById(`email-${safeId}`)
  const matriculeEl = document.getElementById(`matricule-${safeId}`)
  const roleEl = document.getElementById(`role-${safeId}`)
  const btn = document.querySelector(`#email-${safeId}`).closest('.airport-section').querySelector('.airport-create-btn')

  const email = (emailEl?.value || "").trim().toLowerCase()
  const matricule = (matriculeEl?.value || "").trim().toUpperCase()
  const role = (roleEl?.value || "user").trim()

  // basic validation
  const emailOk = /.+@.+\..+/.test(email)
  if (!emailOk) {
    showToast("Valid email is required", "error")
    return
  }

  // matricule validation if provided
  if (matricule && (matricule.length !== 8 || !/^[A-Z0-9]{8}$/.test(matricule))) {
    showToast("Matricule must be exactly 8 characters containing only uppercase letters and digits", "error")
    return
  }

  const prev = btn ? btn.textContent : ""
  if (btn) {
    btn.disabled = true
    btn.textContent = "Creating..."
  }

  try {
    const payload = { email, role, airport: airportName }
    if (matricule) {
      payload.matricule = matricule
    }

    const res = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload)
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      showToast(data.error || "Failed to create user", "error")
      return
    }
    showToast(data.message || "User created", "success")
    // clear inputs
    if (emailEl) emailEl.value = ""
    if (matriculeEl) matriculeEl.value = ""
    if (roleEl) roleEl.value = "user"
    // refresh selected airport section and assignment candidates
    const selectedAirport = sessionStorage.getItem('selectedAirport')
    if (selectedAirport) {
      try { await loadSelectedAirportSection(selectedAirport) } catch(_) {}
    }
    try { await loadUsersForAssign() } catch(_) {}
  } catch (e) {
    showToast(String(e), "error")
  } finally {
    if (btn) {
      btn.disabled = false
      btn.textContent = prev || "Create User & Send Email"
    }
  }
}

// Admin panels logic
// Setup assignment report modal close handler
function setupAssignmentReportModal() {
  const modal = document.getElementById("assignmentReportModal")
  const closeBtn = document.getElementById("closeAssignmentReport")
  
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      if (modal) modal.classList.remove("active")
    })
  }
  
  // Close modal when clicking on backdrop
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("active")
      }
    })
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  // Setup assignment report modal
  setupAssignmentReportModal()
  const meRes = await fetch("/api/me", { credentials: "include" })
  if (meRes.ok) {
    const me = await meRes.json()
    if (me.role === "admin") {
      document.getElementById("adminPanel").style.display = ""
      document.getElementById("questionPanel").style.display = ""
      document.getElementById("scoresPanel").style.display = ""
      // Initialize quiz creation controls
      try {
        await loadUsersForAssign()
        updateCreateAssignState()
        loadAssignments()
        if (!window.__assignmentsAutoTimer) {
          window.__assignmentsAutoTimer = setInterval(() => {
            try { loadAssignments() } catch (_) {}
          }, 15000)
        }
      } catch (e) {}
      await loadAirportsInto("assignAirportFilter")
      await loadAirportsInto("assignmentsAirportFilter")
      // Load airport selector for reports and initialize analytics
      await loadAirportsInto("reportAirportSelect")
      try { loadAnalyticsChart() } catch (_) {}
      const analyticsPanel = document.getElementById("analyticsPanel")
      if (analyticsPanel) analyticsPanel.style.display = ""

      // Check if airport was previously selected and restore it
      const selectedAirport = sessionStorage.getItem('selectedAirport')
      if (selectedAirport) {
        selectAirport(selectedAirport)
      }

      // Initialize quiz assignment data
      loadUsersForAssign()
      loadAirportsForAssign()

      loadScores()
      // Initialize question management
      loadSections()
      // Populate the Questions-area section selector too
      populateSectionDropdown("questionSectionFilter")
      loadQuestions()

      // Add event listeners for airport modal
      const airportModalClose = document.getElementById("airportModalClose")
      if (airportModalClose) {
        airportModalClose.addEventListener("click", hideAirportSelectionModal)
      }

      const airportModal = document.getElementById("airportSelectionModal")
      if (airportModal) {
        airportModal.addEventListener("click", (e) => {
          if (e.target === airportModal) {
            hideAirportSelectionModal()
          }
        })
      }
    }
  }
})

async function loadAirportsInto(selectId) {
  const sel = document.getElementById(selectId)
  if (!sel) return
  sel.innerHTML = ""
  const first = document.createElement("option")
  first.value = ""
  first.textContent = /filter/i.test(selectId) ? "All airports" : "Select an airport..."
  sel.appendChild(first)
  try {
    const res = await fetch("/api/airports", { credentials: "include" })
    if (!res.ok) return
    const airports = await res.json()
    airports.forEach((a) => {
      const opt = document.createElement("option")
      opt.value = a
      opt.textContent = a
      sel.appendChild(opt)
    })
  } catch (_) {}
}

async function loadAirportSections() {
  const container = document.getElementById("airportSections")
  if (!container) return

  // Show loading state
  container.innerHTML = '<div class="airport-loading">Loading airports...</div>'

  try {
    // Load airports and users in parallel
    const [airportsRes, usersRes] = await Promise.all([
      fetch("/api/airports", { credentials: "include" }),
      fetch("/api/users", { credentials: "include" })
    ])

    if (!airportsRes.ok || !usersRes.ok) {
      container.innerHTML = '<div class="airport-loading">Failed to load data</div>'
      return
    }

    const airports = await airportsRes.json()
    const users = await usersRes.json()

    // Group users by airport
    const usersByAirport = {}
    users.forEach(user => {
      const airport = user.airport || "Unassigned"
      if (!usersByAirport[airport]) {
        usersByAirport[airport] = []
      }
      usersByAirport[airport].push(user)
    })

    // Create airport sections
    container.innerHTML = ""
    airports.forEach(airport => {
      const section = createAirportSection(airport, usersByAirport[airport] || [])
      container.appendChild(section)
    })

  } catch (error) {
    console.error("Error loading airport sections:", error)
    container.innerHTML = '<div class="airport-loading">Error loading airports</div>'
  }
}

function createAirportSection(airportName, users) {
  const section = document.createElement("div")
  section.className = "airport-section"

  // Get airport code for icon (last part in parentheses)
  const codeMatch = airportName.match(/\((\w+)\)$/)
  const code = codeMatch ? codeMatch[1] : "✈"

  section.innerHTML = `
    <div class="airport-header">
      <div class="airport-icon">${code}</div>
      <h3 class="airport-name">${airportName}</h3>
    </div>

    <div class="airport-users">
      <h4>Current Users (${users.length})</h4>
      <div class="airport-users-list">
        ${users.length === 0 ?
          '<div style="color: var(--muted); font-style: italic; padding: 12px; text-align: center;">No users assigned yet</div>' :
          users.map(user => `
            <div class="airport-user-item">
              <div>
                <div class="airport-user-email">${user.email}</div>
                <div class="airport-user-role">${user.role.toUpperCase()}</div>
              </div>
              <div class="airport-user-actions">
                <button class="btn secondary" onclick="openEditUserModal('${user.email}', '${user.role}', '${(user.airport || "").replace(/'/g, "'")}', '${(user.matricule || "").replace(/'/g, "'")}')">Edit</button>
                <button class="btn secondary" style="background: var(--danger); border-color: var(--danger);" onclick="deleteUser('${user.email}')">Delete</button>
              </div>
            </div>
          `).join('')
        }
      </div>
    </div>

    <div class="airport-create-form">
      <h4>Add New User</h4>
      <div class="airport-form-grid">
        <div class="airport-form-group">
          <label>Email Address</label>
          <input type="email" id="email-${airportName.replace(/[^a-zA-Z0-9]/g, '_')}" placeholder="user@example.com" required>
        </div>
        <div class="airport-form-group">
          <label>Matricule <span style="font-size: 12px; color: #666;">(optional - leave empty for auto-generate)</span></label>
          <input type="text" id="matricule-${airportName.replace(/[^a-zA-Z0-9]/g, '_')}" placeholder="ABC12345" maxlength="8" pattern="[A-Z0-9]{8}" title="8 characters: uppercase letters and digits only">
        </div>
        <div class="airport-form-group">
          <label>Role</label>
          <select id="role-${airportName.replace(/[^a-zA-Z0-9]/g, '_')}">
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>
      <button class="airport-create-btn" onclick="createUserForAirport('${airportName.replace(/'/g, "\\'")}')">
        Create User & Send Email
      </button>
    </div>
  `

  return section
}

async function showAirportSelectionModal() {
  const modal = document.getElementById("airportSelectionModal")
  const optionsContainer = document.getElementById("airportOptions")

  if (!modal || !optionsContainer) return

  // Clear previous options
  optionsContainer.innerHTML = '<div class="airport-loading">Loading airports...</div>'

  try {
    const res = await fetch("/api/airports", { credentials: "include" })
    if (!res.ok) {
      optionsContainer.innerHTML = '<div style="color: var(--danger); text-align: center; padding: 20px;">Failed to load airports</div>'
      return
    }

    const airports = await res.json()

    // Create airport option cards
    optionsContainer.innerHTML = ""
    airports.forEach(airport => {
      const optionCard = document.createElement("div")
      optionCard.className = "airport-option-card"
      optionCard.onclick = () => selectAirport(airport)

      // Get airport code for icon
      const codeMatch = airport.match(/\((\w+)\)$/)
      const code = codeMatch ? codeMatch[1] : "✈"

      optionCard.innerHTML = `
        <div class="airport-option-icon">${code}</div>
        <div class="airport-option-name">${airport}</div>
      `

      optionsContainer.appendChild(optionCard)
    })

  } catch (error) {
    console.error("Error loading airports for modal:", error)
    optionsContainer.innerHTML = '<div style="color: var(--danger); text-align: center; padding: 20px;">Error loading airports</div>'
  }

  // Show modal
  modal.classList.add("active")
}

function hideAirportSelectionModal() {
  const modal = document.getElementById("airportSelectionModal")
  if (modal) {
    modal.classList.remove("active")
  }
}

async function selectAirport(airportName) {
  // Store selected airport in session storage
  sessionStorage.setItem('selectedAirport', airportName)

  // Hide modal
  hideAirportSelectionModal()

  // Load and display the selected airport's data
  await loadSelectedAirportSection(airportName)

  // Update UI elements
  const descriptionEl = document.getElementById("airportDescription")
  const changeBtn = document.getElementById("changeAirportBtn")
  const contentEl = document.getElementById("airportManagementContent")

  if (descriptionEl) {
    descriptionEl.textContent = `Managing users for: ${airportName}`
  }

  if (changeBtn) {
    changeBtn.style.display = "block"
  }

  if (contentEl) {
    contentEl.style.display = "block"
  }
}

async function loadSelectedAirportSection(airportName) {
  const container = document.getElementById("selectedAirportSection")
  if (!container) return

  // Show loading state
  container.innerHTML = '<div class="airport-loading">Loading airport data...</div>'

  try {
    // Load users for this airport
    const usersRes = await fetch("/api/users", { credentials: "include" })
    if (!usersRes.ok) {
      container.innerHTML = '<div style="color: var(--danger); text-align: center; padding: 20px;">Failed to load users</div>'
      return
    }

    const users = await usersRes.json()
    const airportUsers = users.filter(user => (user.airport || "") === airportName)

    // Create the airport section
    const section = createAirportSection(airportName, airportUsers)
    container.innerHTML = ""
    container.appendChild(section)

  } catch (error) {
    console.error("Error loading selected airport section:", error)
    container.innerHTML = '<div style="color: var(--danger); text-align: center; padding: 20px;">Error loading airport data</div>'
  }
}

// Assignment mode: 'individual' or 'airport'
window.__assignmentMode = 'individual'

// Selected airports for assignment
window.__assignSelectedAirports = new Set()

async function loadUsersForAssign() {
  try {
    const res = await fetch("/api/users", { credentials: "include" })
    if (!res.ok) return
    window.__assignUsers = await res.json()
    // Initialize or prune the selection set
    if (!window.__assignSelected) window.__assignSelected = new Set()
    const existingEmails = new Set((window.__assignUsers || []).map((u) => u.email))
    for (const e of Array.from(window.__assignSelected)) {
      if (!existingEmails.has(e)) window.__assignSelected.delete(e)
    }
    renderAssignUsers()
    updateCreateAssignState()
  } catch (_) {}
}

// Load airports for assignment
async function loadAirportsForAssign() {
  try {
    const res = await fetch("/api/airports", { credentials: "include" })
    if (!res.ok) return
    window.__assignAirports = await res.json()
    renderAssignAirports()
    updateCreateAssignState()
  } catch (_) {}
}

function renderAssignUsers() {
  const list = document.getElementById("assignUserList")
  if (!list) return
  const q = (document.getElementById("assignUserSearch")?.value || "").trim().toLowerCase()
  const airportFilter = (document.getElementById("assignAirportFilter")?.value || "").trim()
  const users = Array.isArray(window.__assignUsers) ? window.__assignUsers : []
  let filtered = users
  if (airportFilter) filtered = filtered.filter((u) => (u.airport || "") === airportFilter)
  if (q)
    filtered = filtered.filter((u) => (u.email || "").toLowerCase().includes(q) || (u.matricule || "").toLowerCase().includes(q))
  if (!filtered.length) {
    list.innerHTML = '<div class="muted" style="padding:8px;">No candidates</div>'
    return
  }
  const selected = window.__assignSelected || new Set()
  list.innerHTML = filtered
    .map((u) => {
      const id = `assign_${(u.email || "").replace(/[^a-z0-9]/gi, "_")}`
      const meta = [
        u.matricule ? `<span class=\"user-matricule\">${u.matricule}</span>` : "",
        u.airport ? `<span class=\"user-matricule\">${u.airport}</span>` : "",
      ]
        .filter(Boolean)
        .join(" ")
      const checked = selected.has(u.email) ? "checked" : ""
      return `<label for="${id}" style="display:flex; align-items:center; gap:10px; padding:8px; border-bottom:1px solid var(--glass-border); cursor:pointer;">
      <input type="checkbox" name="assignUserCheckbox" id="${id}" value="${u.email}" ${checked} onchange="toggleAssignSelection(this)">
      <div class="user-info"><div class="user-email">${u.email}</div><div class="user-details">${meta}</div></div>
    </label>`
    })
    .join("")
}

function toggleAssignSelection(el) {
  if (!window.__assignSelected) window.__assignSelected = new Set()
  const email = String(el.value || "").toLowerCase()
  if (el.checked) window.__assignSelected.add(email)
  else window.__assignSelected.delete(email)
  updateCreateAssignState()
}

function toggleAirportSelection(el) {
  if (!window.__assignSelectedAirports) window.__assignSelectedAirports = new Set()
  const airport = String(el.value || "")
  if (el.checked) window.__assignSelectedAirports.add(airport)
  else window.__assignSelectedAirports.delete(airport)
  updateCreateAssignState()
}

function renderAssignAirports() {
  const list = document.getElementById("assignAirportList")
  if (!list) return

  const airports = Array.isArray(window.__assignAirports) ? window.__assignAirports : []
  const selected = window.__assignSelectedAirports || new Set()

  if (!airports.length) {
    list.innerHTML = '<div class="muted" style="padding:8px;">No airports available</div>'
    return
  }

  // Group users by airport to show counts
  const userCounts = {}
  if (window.__assignUsers) {
    window.__assignUsers.forEach(user => {
      const airport = user.airport || "Unassigned"
      userCounts[airport] = (userCounts[airport] || 0) + 1
    })
  }

  list.innerHTML = airports
    .map((airport) => {
      const id = `airport_${airport.replace(/[^a-z0-9]/gi, "_")}`
      const count = userCounts[airport] || 0
      const checked = selected.has(airport) ? "checked" : ""
      const codeMatch = airport.match(/\((\w+)\)$/)
      const code = codeMatch ? codeMatch[1] : "✈"

      return `<label for="${id}" class="airport-assign-item ${checked ? 'selected' : ''}">
      <input type="checkbox" name="assignAirportCheckbox" id="${id}" value="${airport}" ${checked} onchange="toggleAirportSelection(this)" class="airport-assign-checkbox">
      <div class="airport-assign-icon">${code}</div>
      <div class="airport-assign-info">
        <div class="airport-assign-name">${airport}</div>
        <div class="airport-assign-count">${count} user${count !== 1 ? 's' : ''}</div>
      </div>
    </label>`
    })
    .join("")
}

function setAssignmentMode(mode) {
  window.__assignmentMode = mode

  // Update tab buttons
  const individualTab = document.getElementById("modeIndividual")
  const airportTab = document.getElementById("modeAirport")
  const individualSection = document.getElementById("individualModeSection")
  const airportSection = document.getElementById("airportModeSection")

  if (individualTab) individualTab.classList.toggle("active", mode === "individual")
  if (airportTab) airportTab.classList.toggle("active", mode === "airport")

  if (individualSection) individualSection.style.display = mode === "individual" ? "block" : "none"
  if (airportSection) airportSection.style.display = mode === "airport" ? "block" : "none"

  // Load appropriate data
  if (mode === "individual") {
    loadUsersForAssign()
  } else if (mode === "airport") {
    loadAirportsForAssign()
  }

  updateCreateAssignState()
}

function updateCreateAssignState() {
  const btn = document.getElementById("createBtn")
  const info = document.getElementById("assignInfo")

  let count = 0
  let err = ""

  if (window.__assignmentMode === "individual") {
    count = window.__assignSelected ? window.__assignSelected.size : 0
    err = count ? "" : "Select one or more candidates."
  } else if (window.__assignmentMode === "airport") {
    count = window.__assignSelectedAirports ? window.__assignSelectedAirports.size : 0
    err = count ? "" : "Select one or more airports."
  }

  if (btn) btn.disabled = Boolean(err)
  if (info) info.textContent = err || `${count} ${window.__assignmentMode === "individual" ? "user" : "airport"}${count !== 1 ? "s" : ""} selected`
}

async function createAssignment() {
  const info = document.getElementById("assignInfo")
  const okBox = document.getElementById("assignSuccess")
  const errBox = document.getElementById("assignError")
  if (info) info.textContent = ""
  if (okBox) {
    okBox.style.display = "none"
    okBox.textContent = ""
  }
  if (errBox) {
    errBox.style.display = "none"
    errBox.textContent = ""
  }

  const btn = document.getElementById("createBtn") || document.querySelector("button.btn")
  const prev = btn.textContent
  btn.textContent = "Creating..."
  btn.disabled = true

  let emails = []
  let assignmentType = ""

  // Determine assignment type and collect emails
  if (window.__assignmentMode === "individual") {
    emails = Array.from(window.__assignSelected || [])
    assignmentType = "individual users"
    if (!emails.length) {
      if (info) info.textContent = "Select at least one candidate."
      btn.textContent = prev
      btn.disabled = false
      return
    }
  } else if (window.__assignmentMode === "airport") {
    const selectedAirports = Array.from(window.__assignSelectedAirports || [])
    assignmentType = "airports"
    if (!selectedAirports.length) {
      if (info) info.textContent = "Select at least one airport."
      btn.textContent = prev
      btn.disabled = false
      return
    }

    // Get all users from selected airports
    const users = window.__assignUsers || []
    emails = users
      .filter(user => selectedAirports.includes(user.airport))
      .map(user => user.email)

    if (!emails.length) {
      if (errBox) {
        errBox.textContent = "No users found in selected airports."
        errBox.style.display = "block"
      }
      btn.textContent = prev
      btn.disabled = false
      return
    }
  }

  let ok = 0,
    fail = 0
  const errors = []
  // Get number of questions from input (default 60, max 60)
  const questionCountInput = document.getElementById("assignQuestionCount")
  const questionCount = questionCountInput ? Math.min(Math.max(parseInt(questionCountInput.value) || 60, 1), 60) : 60

  try {
    for (const email of emails) {
      try {
        const res = await fetch("/api/quiz-assignments", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ email, total: questionCount }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || "Failed")
        else {
          ok++
        }
      } catch (e) {
        fail++
        errors.push(`${email}: ${e.message || e}`)
      }
    }

    if (okBox && ok) {
      const targetDesc = window.__assignmentMode === "airport" ?
        `${Array.from(window.__assignSelectedAirports).join(", ")}` :
        `${ok} user${ok > 1 ? "s" : ""}`
      okBox.textContent = `Created ${ok} quiz${ok > 1 ? "zes" : ""} successfully for ${targetDesc}.`
      okBox.style.display = "block"
    }
    if (errBox && fail) {
      errBox.textContent = `Failed for ${fail}: ${errors.slice(0, 3).join("; ")}${errors.length > 3 ? " ..." : ""}`
      errBox.style.display = "block"
    }
    if (info) info.textContent = `${ok} succeeded, ${fail} failed`

    // Clear selections after successful creation
    if (ok > 0) {
      if (window.__assignmentMode === "individual") {
        window.__assignSelected.clear()
        renderAssignUsers()
      } else {
        window.__assignSelectedAirports.clear()
        renderAssignAirports()
      }
      updateCreateAssignState()
    }

    loadAssignments()
  } finally {
    btn.textContent = prev
    btn.disabled = false
  }
}

async function loadUsers() {
  const ul = document.getElementById("usersList")
  ul.innerHTML = ""
  const airportFilter = document.getElementById("filterAirport")
  const selectedAirport = airportFilter ? airportFilter.value : ""
  const userSearch = (document.getElementById("userSearch")?.value || "").trim().toLowerCase()

  try {
    const res = await fetch("/api/users", { credentials: "include" })
    if (!res.ok) {
      console.error("Failed to load users:", res.status)
      ul.innerHTML = '<li style="color: var(--danger); text-align: center; padding: 20px;">Failed to load users</li>'
      return
    }

    let users = await res.json()
    if (selectedAirport) users = users.filter((u) => (u.airport || "") === selectedAirport)
    if (userSearch) {
      users = users.filter((u) => {
        const email = (u.email || "").toLowerCase()
        const mat = (u.matricule || "").toLowerCase()
        return email.includes(userSearch) || mat.includes(userSearch)
      })
    }

    if (!users || users.length === 0) {
      ul.innerHTML = '<li style="color: var(--muted); text-align: center; padding: 20px;">No users found</li>'
      return
    }

    for (const u of users) {
      const li = document.createElement("li")
      const createdDate = u.created_at ? new Date(u.created_at).toLocaleDateString() : "Unknown"
      li.innerHTML = `
        <div class="user-info">
          <div class="user-email">${u.email}</div>
          <div class="user-details">
            <span class="user-role">${u.role.toUpperCase()}</span>
            ${u.matricule ? `<span class=\"user-matricule\">Matricule: ${u.matricule}</span>` : ""}
            ${u.airport ? `<span class=\"user-matricule\">${u.airport}</span>` : ""}
            <span class="user-created" style="color: var(--muted); font-size: 12px;">Created: ${createdDate}</span>
          </div>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn secondary" onclick="openEditUserModal('${u.email}', '${u.role}', '${(u.airport || "").replace(/'/g, "'")}', '${(u.matricule || "").replace(/'/g, "'")}')">Edit</button>
          <button class="btn secondary" style="background: var(--danger); border-color: var(--danger);" onclick="deleteUser('${u.email}')">Delete</button>
        </div>
      `
      ul.appendChild(li)
    }
  } catch (error) {
    console.error("Error loading users:", error)
    ul.innerHTML = '<li style="color: var(--danger); text-align: center; padding: 20px;">Error loading users</li>'
  }
}

async function deleteUser(email) {
  if (!confirm(`Delete user ${email}? This cannot be undone.`)) return
  try {
    const res = await fetch(`/api/users/${encodeURIComponent(email)}`, { method: "DELETE", credentials: "include" })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      showToast(data.error || "Failed to delete user", "error")
      return
    }
    showToast("User deleted", "success")
    // Refresh selected airport section if one is selected
    const selectedAirport = sessionStorage.getItem('selectedAirport')
    if (selectedAirport) {
      loadSelectedAirportSection(selectedAirport)
    }
    loadUsersForAssign()
  } catch (e) {
    showToast(String(e), "error")
  }
}

async function loadScores() {
  const ul = document.getElementById("scoresList")
  ul.innerHTML = ""
  // Fetch scores and violations in parallel
  const [resScores, resViol] = await Promise.all([
    fetch("/api/scores", { credentials: "include" }),
    fetch("/api/violation-reports", { credentials: "include" }),
  ])
  if (!resScores.ok) return
  const scores = await resScores.json()
  const violData = resViol.ok ? await resViol.json() : { reports: [] }
  const reports = Array.isArray(violData.reports) ? violData.reports : []
  // Map latest termination per email (including assignments with violation logs)
  const latestTerminatedByEmail = {}
  for (const r of reports) {
    const key = r.email
    const ts = r.terminated_at
      ? new Date(r.terminated_at).getTime()
      : r.finished_at
        ? new Date(r.finished_at).getTime()
        : 0
    const isTerminated =
      Boolean(r.terminated) ||
      (Array.isArray(r.violations) &&
        r.violations.some(
          (v) =>
            (v.type || "").toString().toUpperCase().includes("FACE") ||
            (v.type || "") === "NO_FACE" ||
            (v.type || "").toString().toUpperCase().includes("MULTIPLE"),
        ))
    if (!isTerminated) continue
    const prev = latestTerminatedByEmail[key]
    const reason =
      r.termination_reason || (Array.isArray(r.violations) && r.violations.length ? r.violations[0].type : "VIOLATION")
    if (!prev || ts > prev.ts) {
      latestTerminatedByEmail[key] = { ts, reason }
    }
  }
  // Build set of emails with scores
  const rowsByEmail = new Map()
  for (const s of scores) rowsByEmail.set(s.email, s)
  // Ensure rejected-only users without score are listed
  for (const email of Object.keys(latestTerminatedByEmail)) {
    if (!rowsByEmail.has(email))
      rowsByEmail.set(email, { email, category: "All", correct: 0, total_with_keys: 0, attempted: 0 })
  }
  for (const s of Array.from(rowsByEmail.values())) {
    const li = document.createElement("li")
    li.style.display = "grid"
    li.style.gridTemplateColumns = "1fr auto"
    li.style.alignItems = "center"
    const left = document.createElement("div")
    left.className = "list-col"
    const rejected = latestTerminatedByEmail[s.email]
    const badge = rejected
      ? `<span style="margin-left:6px; color:#ef4444; font-weight:700;">REJECTED — ${String(rejected.reason).replace(/_/g, " ")}</span>`
      : ""
    left.innerHTML = `<div style="font-weight:700;">${s.email} ${badge}</div><div class="dim">${s.category || "All"} — ${s.correct || 0}/${s.total_with_keys || 0} (attempted ${s.attempted || 0})</div>`
    const right = document.createElement("div")
    const viewBtn = document.createElement("button")
    viewBtn.className = "btn secondary"
    viewBtn.textContent = "View report"
    viewBtn.addEventListener("click", async () => {
      await loadLatestAssignmentReportFor(s.email)
    })
    right.appendChild(viewBtn)
    li.appendChild(left)
    li.appendChild(right)
    ul.appendChild(li)
  }
}

async function loadLatestAssignmentReportFor(email) {
  try {
    // fetch all assignments and pick most recent finished for this user
    const res = await fetch("/api/quiz-assignments", { credentials: "include" })
    if (!res.ok) {
      showToast("Failed to load assignments", "error")
      return
    }
    const rows = await res.json()
    const list = Array.isArray(rows) ? rows.filter((r) => r.email === email && r.finished_at) : []
    if (!list.length) {
      showToast("No finished assignment found for user", "error")
      return
    }
    // pick latest by finished_at
    list.sort((a, b) => new Date(b.finished_at).getTime() - new Date(a.finished_at).getTime())
    const a = list[0]
    await renderAssignmentReport(a)
  } catch (_) {
    showToast("Failed to load report", "error")
  }
}

async function renderAssignmentReport(a) {
  // Open modal instead of panel
  const modal = document.getElementById("assignmentReportModal")
  if (modal) modal.classList.add("active")
  
  const meta = document.getElementById("assignmentMeta")
  if (meta) {
    const email = a.email || "Unknown"
    const finishedDate = a.finished_at ? new Date(a.finished_at).toLocaleString() : "Not finished"
    const score = typeof a.score === "number" ? `${a.score}/${a.total_with_keys}` : "n/a"
    const attempted = a.attempted || 0
    const isTerminated = a.terminated || false
    const terminationReason = a.termination_reason || ""
    const terminationMessage = a.termination_message || ""
    
    let statusHtml = ""
    if (isTerminated) {
      statusHtml = `
        <div style="margin-top: 12px; padding: 12px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 18px;">❌</span>
            <span style="font-weight: 700; color: #dc2626; font-size: 14px;">REJECTED</span>
          </div>
          ${terminationReason ? `<div style="color: #991b1b; font-size: 13px; margin-bottom: 4px;"><strong>Reason:</strong> ${terminationReason.replace(/_/g, ' ')}</div>` : ''}
          ${terminationMessage ? `<div style="color: #991b1b; font-size: 13px;"><strong>Message:</strong> ${terminationMessage}</div>` : ''}
        </div>
      `
    }
    
    meta.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-weight: 600; color: var(--text);">📧 Email:</span>
          <span style="color: var(--muted);">${email}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-weight: 600; color: var(--text);">📅 Finished:</span>
          <span style="color: var(--muted);">${finishedDate}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-weight: 600; color: var(--text);">📊 Score:</span>
          <span style="color: var(--muted);">${score}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-weight: 600; color: var(--text);">✏️ Attempted:</span>
          <span style="color: var(--muted);">${attempted} questions</span>
        </div>
        ${statusHtml}
      </div>
    `
  }
  const per = document.getElementById("perSection")
  per.innerHTML = ""
  const sec = a.per_section || {}
  const secNames = Object.keys(sec)
  if (secNames.length) {
    const table = document.createElement("table")
    table.style.width = "100%"
    table.style.borderCollapse = "collapse"
    table.innerHTML = `<thead><tr><th style="text-align:left; padding:8px; border-bottom:1px solid var(--glass-border); font-weight:600;">Section</th><th style="text-align:left; padding:8px; border-bottom:1px solid var(--glass-border); font-weight:600;">Correct</th><th style="text-align:left; padding:8px; border-bottom:1px solid var(--glass-border); font-weight:600;">Attempted</th></tr></thead>`
    const tbody = document.createElement("tbody")
    for (const name of secNames) {
      const r = sec[name] || { attempted: 0, correct: 0 }
      const tr = document.createElement("tr")
      tr.innerHTML = `<td style="padding:8px; border-bottom:1px solid var(--glass-border);">${name}</td><td style="padding:8px; border-bottom:1px solid var(--glass-border);">${r.correct}</td><td style="padding:8px; border-bottom:1px solid var(--glass-border);">${r.attempted}</td>`
      tbody.appendChild(tr)
    }
    table.appendChild(tbody)
    per.appendChild(table)
  } else {
    per.textContent = "No per-section data available."
  }
  const answersDiv = document.getElementById("answersList")
  answersDiv.innerHTML = ""
  
  // Show answers if available
  const rows = Array.isArray(a.answers) ? a.answers : []
  if (rows.length) {
    const ul = document.createElement("ul")
    rows.forEach((r, idx) => {
      const li = document.createElement("li")
      li.style.margin = "6px 0"
      li.innerHTML = `<strong>Q${idx + 1}${r.id != null ? ` (#${r.id})` : ""}</strong> ${r.section ? `<span class=\"dim\">[${r.section}]</span>` : ""} — Your: ${r.your || ""}${r.correct ? ` — Correct: ${r.correct}` : ""} ${r.is_correct ? '<span style="color:#22c55e; font-weight:700;">✓</span>' : '<span style="color:#ef4444; font-weight:700;">✗</span>'}`
      ul.appendChild(li)
    })
    answersDiv.appendChild(ul)
  } else if (!a.terminated) {
    // Only show "No detailed answers" if not rejected
    answersDiv.textContent = "No detailed answers available."
  }

  // Display captured violation images if assignment was rejected
  if (a.terminated) {
    const violationLog = Array.isArray(a.violation_log) ? a.violation_log : []
    
    if (violationLog.length > 0) {
      const violationsWithImages = violationLog.filter(v => v.captured_image)
      
      // Show violation section even if there are no images, but prioritize showing ones with images
      const violationsToShow = violationsWithImages.length > 0 ? violationsWithImages : violationLog
      
      if (violationsToShow.length > 0) {
        const violationSection = document.createElement("div")
        violationSection.style.marginTop = "24px"
        violationSection.style.padding = "16px"
        violationSection.style.background = "rgba(239, 68, 68, 0.1)"
        violationSection.style.border = "1px solid rgba(239, 68, 68, 0.3)"
        violationSection.style.borderRadius = "8px"
        
        const violationTitle = document.createElement("h3")
        violationTitle.style.margin = "0 0 16px 0"
        violationTitle.style.color = "#ef4444"
        violationTitle.style.fontSize = "16px"
        violationTitle.textContent = "❌ Rejection Evidence (Captured Screenshots)"
        violationSection.appendChild(violationTitle)

        violationsToShow.forEach((violation, idx) => {
          const violationItem = document.createElement("div")
          violationItem.style.marginBottom = "16px"
          
          const violationInfo = document.createElement("div")
          violationInfo.style.marginBottom = "8px"
          violationInfo.style.fontSize = "14px"
          violationInfo.style.color = "#fca5a5"
          const timestamp = violation.timestamp ? new Date(violation.timestamp).toLocaleString() : "Unknown time"
          violationInfo.innerHTML = `<strong>Violation #${idx + 1}:</strong> ${violation.type || "Unknown"} — ${violation.message || "No message"} — <span class="dim">${timestamp}</span>`
          violationItem.appendChild(violationInfo)

          // Only show image if captured_image exists
          if (violation.captured_image) {
            const img = document.createElement("img")
            img.src = violation.captured_image
            img.style.maxWidth = "100%"
            img.style.height = "auto"
            img.style.borderRadius = "8px"
            img.style.border = "2px solid rgba(239, 68, 68, 0.5)"
            img.style.cursor = "pointer"
            img.style.marginTop = "8px"
            img.title = "Click to view full size"
            
            // Click to view full size
            img.addEventListener("click", () => {
              const modal = document.createElement("div")
              modal.style.position = "fixed"
              modal.style.top = "0"
              modal.style.left = "0"
              modal.style.width = "100%"
              modal.style.height = "100%"
              modal.style.background = "rgba(0, 0, 0, 0.9)"
              modal.style.display = "flex"
              modal.style.alignItems = "center"
              modal.style.justifyContent = "center"
              modal.style.zIndex = "10000"
              modal.style.cursor = "pointer"
              
              const fullImg = document.createElement("img")
              fullImg.src = violation.captured_image
              fullImg.style.maxWidth = "90%"
              fullImg.style.maxHeight = "90%"
              fullImg.style.objectFit = "contain"
              fullImg.style.borderRadius = "8px"
              fullImg.style.border = "2px solid rgba(255, 255, 255, 0.3)"
              
              modal.appendChild(fullImg)
              document.body.appendChild(modal)
              
              modal.addEventListener("click", () => {
                document.body.removeChild(modal)
              })
            })
            
            violationItem.appendChild(img)
          }
          
          violationSection.appendChild(violationItem)
        })
        
        answersDiv.appendChild(violationSection)
      }
    } else {
      // Show rejection info even if no violation log available
      const rejectionSection = document.createElement("div")
      rejectionSection.style.marginTop = "24px"
      rejectionSection.style.padding = "16px"
      rejectionSection.style.background = "rgba(239, 68, 68, 0.1)"
      rejectionSection.style.border = "1px solid rgba(239, 68, 68, 0.3)"
      rejectionSection.style.borderRadius = "8px"
      
      const rejectionInfo = document.createElement("div")
      rejectionInfo.style.color = "#fca5a5"
      rejectionInfo.style.fontSize = "14px"
      let rejectionText = "❌ This assignment was rejected"
      if (a.termination_reason) {
        rejectionText += ` (${a.termination_reason})`
      }
      if (a.termination_message) {
        rejectionText += ` — ${a.termination_message}`
      }
      if (a.terminated_at) {
        rejectionText += ` — Rejected at: ${new Date(a.terminated_at).toLocaleString()}`
      }
      rejectionInfo.textContent = rejectionText
      rejectionSection.appendChild(rejectionInfo)
      
      answersDiv.appendChild(rejectionSection)
    }
  }
}

async function loadSections() {
  try {
    const res = await fetch("/api/quiz-sections", { credentials: "include" })
    if (!res.ok) return
    let sections = await res.json()
    const secSearch = (document.getElementById("sectionSearch")?.value || "").trim().toLowerCase()
    if (secSearch) {
      sections = sections.filter((s) => (s.name || "").toLowerCase().includes(secSearch))
    }

    const ul = document.getElementById("sectionsList")
    const filter = document.getElementById("sectionFilter")

    if (ul) {
      ul.innerHTML = ""
      if (sections.length === 0) {
        ul.innerHTML = '<li style="color: var(--muted); text-align: center; padding: 20px;">No sections found</li>'
      } else {
        sections.forEach((section) => {
          const li = document.createElement("li")
          li.innerHTML = `
            <div class="user-info">
              <div class="user-email">${section.name}</div>
              <div class="user-details">
                <span class="user-matricule">${section.question_count} questions</span>
                <span class="user-created" style="color: var(--muted); font-size: 12px;">Created: ${new Date(section.created_at).toLocaleDateString()}</span>
              </div>
            </div>
            <div style="display: flex; gap: 8px;">
              <button class="btn secondary" onclick="openEditSectionModal('${section._id}', '${section.name}', '${(section.description || "").replace(/'/g, "\\'")}')">Edit</button>
              <button class="btn secondary" onclick="deleteSection('${section._id}', '${section.name}')" style="background: var(--danger); border-color: var(--danger);">Delete</button>
            </div>
          `
          ul.appendChild(li)
        })
      }
    }

    if (filter) {
      filter.innerHTML = '<option value="">All Sections</option>'
      sections.forEach((section) => {
        const opt = document.createElement("option")
        opt.value = section.name
        opt.textContent = `${section.name} (${section.question_count})`
        filter.appendChild(opt)
      })
    }
  } catch (error) {
    console.error("Error loading sections:", error)
  }
}

async function loadQuestions() {
  try {
    const sectionFilter =
      document.getElementById("questionSectionFilter")?.value || document.getElementById("sectionFilter")?.value || ""
    const textFilter = (document.getElementById("questionSearch")?.value || "").trim().toLowerCase()
    const url = sectionFilter ? `/api/questions?section=${encodeURIComponent(sectionFilter)}` : "/api/questions"
    const res = await fetch(url, { credentials: "include" })
    if (!res.ok) return
    let questions = await res.json()
    if (textFilter) {
      questions = questions.filter((q) => (q.question || "").toLowerCase().includes(textFilter))
    }

    const ul = document.getElementById("questionsList")
    if (ul) {
      ul.innerHTML = ""
      if (questions.length === 0) {
        ul.innerHTML = '<li style="color: var(--muted); text-align: center; padding: 20px;">No questions found</li>'
      } else {
        questions.forEach((question) => {
          const li = document.createElement("li")
          const answers = question.answers || []
          const correctAnswer = question.correct_answer || "A"
          li.innerHTML = `
            <div class="user-info" style="flex: 1;">
              <div class="user-email">${question.question}</div>
              <div class="user-details">
                <span class="user-matricule">Section: ${question.section}</span>
                <span class="user-matricule">ID: ${question.id}</span>
                <span class="user-created" style="color: var(--muted); font-size: 12px;">Correct: ${correctAnswer}</span>
              </div>
              <div style="margin-top: 8px; font-size: 12px; color: var(--muted);">
                ${answers
                  .map(
                    (answer, idx) =>
                      `<div>${String.fromCharCode(65 + idx)}. ${answer}${String.fromCharCode(65 + idx) === correctAnswer ? " ✓" : ""}</div>`,
                  )
                  .join("")}
              </div>
            </div>
            <div style="display: flex; gap: 8px;">
              <button class="btn secondary" onclick="openEditQuestionFromList(this)">Edit</button>
              <button class="btn secondary" onclick="deleteQuestion('${question._id}')" style="background: var(--danger); border-color: var(--danger);">Delete</button>
            </div>
          `
          // Attach serialized data for editing
          li.querySelector("button.btn.secondary").dataset.qdata = encodeURIComponent(JSON.stringify(question))
          ul.appendChild(li)
        })
      }
    }
  } catch (error) {
    console.error("Error loading questions:", error)
  }
}

function filterQuestions() {
  loadQuestions()
}

async function migrateQuestions() {
  const statusDiv = document.getElementById("migrationStatus")
  if (statusDiv) {
    statusDiv.innerHTML = '<div style="color: var(--accent);">Migrating questions...</div>'
  }

  try {
    const res = await fetch("/api/migrate-questions", {
      method: "POST",
      credentials: "include",
    })
    const result = await res.json()

    if (res.ok) {
      if (statusDiv) {
        statusDiv.innerHTML = `<div style="color: var(--success);">Migration successful! ${result.sections_created} sections created, ${result.questions_migrated} questions migrated.</div>`
      }
      showToast("Migration completed successfully", "success")
      loadSections()
      loadQuestions()
    } else {
      if (statusDiv) {
        statusDiv.innerHTML = `<div style="color: var(--danger);">Migration failed: ${result.error}</div>`
      }
      showToast("Migration failed: " + result.error, "error")
    }
  } catch (error) {
    if (statusDiv) {
      statusDiv.innerHTML = `<div style="color: var(--danger);">Migration failed: ${error.message}</div>`
    }
    showToast("Migration failed: " + error.message, "error")
  }
}

function showCreateSectionForm() {
  const form = document.getElementById("createSectionForm")
  if (form) {
    form.style.display = "block"
    clearSectionForm()
  }
}

function hideCreateSectionForm() {
  const form = document.getElementById("createSectionForm")
  if (form) {
    form.style.display = "none"
  }
}

function clearSectionForm() {
  document.getElementById("newSectionName").value = ""
  document.getElementById("newSectionQuestionCount").value = ""
  document.getElementById("newSectionDescription").value = ""
}

async function submitNewSection() {
  const name = document.getElementById("newSectionName").value.trim()
  const questionCount = Number.parseInt(document.getElementById("newSectionQuestionCount").value)
  const description = document.getElementById("newSectionDescription").value.trim()

  if (!name) {
    showToast("Section name is required", "error")
    return
  }

  if (!questionCount || questionCount < 1) {
    showToast("Number of questions is required and must be at least 1", "error")
    return
  }

  try {
    const res = await fetch("/api/sections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        name: name,
        question_count: questionCount,
        description: description,
      }),
    })

    if (res.ok) {
      showToast("Section created successfully", "success")
      hideCreateSectionForm()
      loadSections()
      populateSectionDropdown("newQuestionSection")
    } else {
      const error = await res.json()
      showToast(error.error || "Failed to create section", "error")
    }
  } catch (error) {
    console.error("Error creating section:", error)
    showToast("Error creating section", "error")
  }
}

async function deleteSection(sectionId, sectionName) {
  if (!confirm(`Are you sure you want to delete section "${sectionName}" and all its questions?`)) return

  try {
    const res = await fetch(`/api/sections/${sectionId}`, {
      method: "DELETE",
      credentials: "include",
    })

    const result = await res.json()
    if (res.ok) {
      showToast("Section deleted successfully", "success")
      loadSections()
      loadQuestions()
    } else {
      showToast("Error: " + result.error, "error")
    }
  } catch (error) {
    showToast("Error: " + error.message, "error")
  }
}

let currentQuestionStep = 1
let selectedSectionData = null

function showCreateQuestionForm() {
  const form = document.getElementById("createQuestionForm")
  if (form) {
    form.style.display = "block"
    currentQuestionStep = 1
    selectedSectionData = null
    populateSectionDropdown("newQuestionSection")
    clearQuestionForm()
    showQuestionStep(1)
  }
}

function hideCreateQuestionForm() {
  const form = document.getElementById("createQuestionForm")
  if (form) {
    form.style.display = "none"
  }
}

function clearQuestionForm() {
  document.getElementById("newQuestionText").value = ""
  document.getElementById("newQuestionSection").value = ""
  document.getElementById("newQuestionCorrect").value = "A"
  document.getElementById("answerA").value = ""
  document.getElementById("answerB").value = ""
  document.getElementById("answerC").value = ""
  document.getElementById("answerD").value = ""
}

function showQuestionStep(step) {
  document.getElementById("questionStep1").style.display = "none"
  document.getElementById("questionStep2").style.display = "none"
  document.getElementById("questionStep3").style.display = "none"

  document.getElementById("prevStepBtn").style.display = "none"
  document.getElementById("nextStepBtn").style.display = "none"
  document.getElementById("submitQuestionBtn").style.display = "none"

  document.getElementById(`questionStep${step}`).style.display = "block"

  if (step > 1) {
    document.getElementById("prevStepBtn").style.display = "inline-block"
  }
  if (step < 3) {
    document.getElementById("nextStepBtn").style.display = "inline-block"
  } else {
    document.getElementById("submitQuestionBtn").style.display = "inline-block"
  }
}

function nextQuestionStep() {
  if (currentQuestionStep < 3) {
    currentQuestionStep++
    showQuestionStep(currentQuestionStep)
  }
}

function prevQuestionStep() {
  if (currentQuestionStep > 1) {
    currentQuestionStep--
    showQuestionStep(currentQuestionStep)
  }
}

async function onSectionSelected() {
  const sectionName = document.getElementById("newQuestionSection").value
  const sectionInfo = document.getElementById("sectionInfo")

  if (!sectionName) {
    sectionInfo.style.display = "none"
    return
  }

  try {
    const res = await fetch(`/api/sections?name=${encodeURIComponent(sectionName)}`, { credentials: "include" })
    if (res.ok) {
      const section = await res.json()
      selectedSectionData = section

      const questionsRes = await fetch(`/api/questions?section=${encodeURIComponent(sectionName)}`, {
        credentials: "include",
      })
      const questions = questionsRes.ok ? await questionsRes.json() : []

      document.getElementById("selectedSectionName").textContent = section.name
      document.getElementById("sectionQuestionCount").textContent = questions.length
      document.getElementById("sectionTargetCount").textContent = section.question_count || "Not set"

      sectionInfo.style.display = "block"
      document.getElementById("nextStepBtn").style.display = "inline-block"
    }
  } catch (error) {
    console.error("Error loading section details:", error)
  }
}

async function submitNewQuestion() {
  const questionText = document.getElementById("newQuestionText").value.trim()
  const section = document.getElementById("newQuestionSection").value
  const correctAnswer = document.getElementById("newQuestionCorrect").value
  const answerA = document.getElementById("answerA").value.trim()
  const answerB = document.getElementById("answerB").value.trim()
  const answerC = document.getElementById("answerC").value.trim()
  const answerD = document.getElementById("answerD").value.trim()

  if (!questionText) {
    showToast("Question text is required", "error")
    showQuestionStep(2)
    return
  }
  if (!section) {
    showToast("Please select a section", "error")
    showQuestionStep(1)
    return
  }
  if (!answerA || !answerB || !answerC || !answerD) {
    showToast("All four answers (A, B, C, D) are required", "error")
    showQuestionStep(3)
    return
  }

  const answers = [answerA, answerB, answerC, answerD]
  const correctIndex = { A: 0, B: 1, C: 2, D: 3 }[correctAnswer]
  if (correctIndex == null || !answers[correctIndex]) {
    showToast("Select a valid correct answer (A–D) with text provided", "error")
    showQuestionStep(2)
    return
  }

  try {
    const res = await fetch("/api/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        question: questionText,
        answers: answers,
        correct_answer: correctAnswer,
        section: section,
      }),
    })

    if (res.ok) {
      showToast("Question created successfully", "success")
      hideCreateQuestionForm()
      loadQuestions()
      loadSections()
    } else {
      const error = await res.json()
      showToast(error.error || "Failed to create question", "error")
    }
  } catch (error) {
    console.error("Error creating question:", error)
    showToast("Error creating question", "error")
  }
}

function populateSectionDropdown(selectId) {
  const select = document.getElementById(selectId)
  if (!select) return

  select.innerHTML = '<option value="">Select a section...</option>'

  fetch("/api/sections", { credentials: "include" })
    .then((res) => res.json())
    .then((data) => {
      const sections = Array.isArray(data) ? data : Array.isArray(data.sections) ? data.sections : []
      sections.forEach((section) => {
        const option = document.createElement("option")
        option.value = section.name
        const target =
          section.target_questions != null
            ? section.target_questions
            : section.question_count != null
              ? section.question_count
              : "?"
        option.textContent = `${section.name} (${section.question_count || 0}/${target} questions)`
        select.appendChild(option)
      })
    })
    .catch((error) => console.error("Error loading sections:", error))
}

function openEditQuestionFromList(btn) {
  try {
    const dataAttr = btn && btn.dataset ? btn.dataset.qdata : ""
    if (!dataAttr) {
      showToast("Missing question data", "error")
      return
    }
    const q = JSON.parse(decodeURIComponent(dataAttr))
    if (!Array.isArray(q.answers) && q.options) {
      const keys = Object.keys(q.options).sort()
      q.answers = keys.map((k) => q.options[k])
    }
    openEditQuestionModal(q)
  } catch (e) {
    showToast("Failed to open editor", "error")
  }
}

function openEditSectionModal(sectionId, name, description) {
  const modal = document.getElementById("editSectionModal")
  if (!modal) return
  document.getElementById("editSectionId").value = sectionId || ""
  document.getElementById("editSectionName").value = name || ""
  document.getElementById("editSectionDesc").value = description || ""
  const info = document.getElementById("secEditInfo")
  if (info) info.textContent = ""
  modal.classList.add("active")
}
;(() => {
  const modal = document.getElementById("editSectionModal")
  const btnClose = document.getElementById("secEditClose")
  const btnCancel = document.getElementById("secEditCancel")
  const btnSave = document.getElementById("secEditSave")
  const info = document.getElementById("secEditInfo")
  function hide() {
    if (modal) modal.classList.remove("active")
  }
  if (btnClose) btnClose.addEventListener("click", hide)
  if (btnCancel) btnCancel.addEventListener("click", hide)
  if (modal)
    modal.addEventListener("click", (e) => {
      if (e.target === modal) hide()
    })
  if (btnSave)
    btnSave.addEventListener("click", async () => {
      const id = document.getElementById("editSectionId").value
      const name = (document.getElementById("editSectionName").value || "").trim()
      const description = (document.getElementById("editSectionDesc").value || "").trim()
      if (!name) {
        if (info) info.textContent = "Section name is required"
        showToast("Section name is required", "error")
        return
      }
      try {
        const res = await fetch(`/api/sections/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ name, description }),
        })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) {
          const msg = data.error || "Failed to update section"
          if (info) info.textContent = msg
          showToast(msg, "error")
          return
        }
        showToast("Section updated", "success")
        hide()
        loadSections()
        loadQuestions()
      } catch (e) {
        if (info) info.textContent = String(e)
        showToast(String(e), "error")
      }
    })
})()

function openEditQuestionModal(question) {
  try {
    populateSectionDropdown("editQuestionSection")
  } catch (_) {}
  const modal = document.getElementById("editQuestionModal")
  if (!modal || !question) return
  document.getElementById("editQuestionId").value = question._id || ""
  document.getElementById("editQuestionText").value = question.question || ""
  document.getElementById("editQuestionCorrect").value = question.correct_answer || "A"
  const answers = Array.isArray(question.answers) ? question.answers : []
  document.getElementById("editAnswerA").value = answers[0] || ""
  document.getElementById("editAnswerB").value = answers[1] || ""
  document.getElementById("editAnswerC").value = answers[2] || ""
  document.getElementById("editAnswerD").value = answers[3] || ""
  setTimeout(() => {
    const sel = document.getElementById("editQuestionSection")
    if (sel) sel.value = question.section || ""
  }, 80)
  const info = document.getElementById("qEditInfo")
  if (info) info.textContent = ""
  modal.classList.add("active")
}
;(() => {
  const modal = document.getElementById("editQuestionModal")
  const btnClose = document.getElementById("qEditClose")
  const btnCancel = document.getElementById("qEditCancel")
  const btnSave = document.getElementById("qEditSave")
  const info = document.getElementById("qEditInfo")
  function hide() {
    if (modal) modal.classList.remove("active")
  }
  if (btnClose) btnClose.addEventListener("click", hide)
  if (btnCancel) btnCancel.addEventListener("click", hide)
  if (modal)
    modal.addEventListener("click", (e) => {
      if (e.target === modal) hide()
    })
  if (btnSave)
    btnSave.addEventListener("click", async () => {
      const id = document.getElementById("editQuestionId").value
      const text = (document.getElementById("editQuestionText").value || "").trim()
      const section = document.getElementById("editQuestionSection").value
      const correct = document.getElementById("editQuestionCorrect").value
      const a = (document.getElementById("editAnswerA").value || "").trim()
      const b = (document.getElementById("editAnswerB").value || "").trim()
      const c = (document.getElementById("editAnswerC").value || "").trim()
      const d = (document.getElementById("editAnswerD").value || "").trim()
      if (!text) {
        if (info) info.textContent = "Question text is required"
        showToast("Question text is required", "error")
        return
      }
      if (!section) {
        if (info) info.textContent = "Section is required"
        showToast("Section is required", "error")
        return
      }
      if (!a || !b || !c || !d) {
        if (info) info.textContent = "All four options are required"
        showToast("All four options are required", "error")
        return
      }
      const answers = [a, b, c, d]
      const correctIndex = { A: 0, B: 1, C: 2, D: 3 }[correct] ?? -1
      if (correctIndex < 0 || !answers[correctIndex]) {
        if (info) info.textContent = "Correct answer must match a non-empty option"
        showToast("Invalid correct answer", "error")
        return
      }
      try {
        const res = await fetch(`/api/questions/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ question: text, answers, correct_answer: correct, section }),
        })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) {
          const msg = data.error || "Failed to update question"
          if (info) info.textContent = msg
          showToast(msg, "error")
          return
        }
        showToast("Question updated", "success")
        hide()
        loadQuestions()
      } catch (e) {
        if (info) info.textContent = String(e)
        showToast(String(e), "error")
      }
    })
})()

async function deleteQuestion(questionId) {
  if (!confirm("Are you sure you want to delete this question?")) return

  try {
    const res = await fetch(`/api/questions/${questionId}`, {
      method: "DELETE",
      credentials: "include",
    })

    const result = await res.json()
    if (res.ok) {
      showToast("Question deleted successfully", "success")
      loadQuestions()
      loadSections()
    } else {
      showToast("Error: " + result.error, "error")
    }
  } catch (error) {
    showToast("Error: " + error.message, "error")
  }
}

async function loadAssignments() {
  const ul = document.getElementById("assignmentsList")
  if (!ul) return
  ul.innerHTML = ""
  try {
    const res = await fetch("/api/quiz-assignments", { credentials: "include" })
    if (!res.ok) return
    let rows = await res.json()
    const search = (document.getElementById("assignmentSearch")?.value || "").trim().toLowerCase()
    const airportFilter = (document.getElementById("assignmentsAirportFilter")?.value || "").trim()
    if (search) {
      rows = rows.filter((r) => {
        const email = (r.email || "").toLowerCase()
        const status = r.finished_at ? "completed" : r.started_at ? "started" : "pending"
        const terminated = r.terminated ? "terminated" : ""
        return email.includes(search) || status.includes(search) || terminated.includes(search)
      })
    }
    if (airportFilter) {
      const emailToAirport = new Map((Array.isArray(window.__assignUsers) ? window.__assignUsers : []).map((u) => [String(u.email || '').toLowerCase(), u.airport || '']))
      rows = rows.filter((r) => {
        const fromRow = r.airport || ''
        const fromUser = emailToAirport.get(String(r.email || '').toLowerCase()) || ''
        const resolved = fromRow || fromUser
        return resolved === airportFilter
      })
    }
    if (!rows.length) {
      ul.innerHTML = '<li class="muted">No quiz assignments yet</li>'
      return
    }
    for (const r of rows) {
      const li = document.createElement("li")
      li.style.display = "grid"
      li.style.gridTemplateColumns = "1fr auto"
      li.style.alignItems = "center"
      const left = document.createElement("div")
      const right = document.createElement("div")
      const started = r.started_at ? new Date(r.started_at).toLocaleString() : ""
      const finished = r.finished_at ? new Date(r.finished_at).toLocaleString() : ""
      const total = r.total || r.question_count || (Array.isArray(r.selected) ? r.selected.length : undefined)
      left.innerHTML = `<div style="font-weight:700;">${r.email}</div>
        <div class="dim">${r.category || "All"} — ${typeof total === "number" ? total : "?"} questions ${started ? " — started " + started : ""}${finished ? " — finished " + finished : ""}${typeof r.score === "number" ? ` — score ${r.score}/${r.total_with_keys}` : ""}</div>`
      const viewBtn = document.createElement("button")
      viewBtn.className = "btn secondary"
      viewBtn.textContent = "View questions"
      viewBtn.addEventListener("click", () => showAssignmentQuestions(r))
      right.appendChild(viewBtn)
      li.appendChild(left)
      li.appendChild(right)
      ul.appendChild(li)
    }
  } catch (e) {}
}

async function showAssignmentQuestions(row) {
  const id = row.assignment_id
  if (!id) {
    showToast("Missing assignment_id", "error")
    return
  }
  try {
    const res = await fetch("/api/quiz-assignments/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ assignment_id: id }),
    })
    if (!res.ok) {
      showToast("Failed to load questions", "error")
      return
    }
    const data = await res.json()
    const cats = data.quiz_data && Array.isArray(data.quiz_data.categories) ? data.quiz_data.categories : []
    const qs = cats.length ? cats[0].questions || [] : []
    const title = document.getElementById("qmTitle")
    const body = document.getElementById("qmBody")
    if (title) title.textContent = `Assignment Questions (${qs.length})`
    if (body) {
      body.innerHTML = ""
      qs.forEach((q, idx) => {
        const item = document.createElement("div")
        item.className = "qm-item"
        const opts = q.options ? Object.entries(q.options).sort((a, b) => a[0].localeCompare(b[0])) : []
        const section = q._section ? `<span class=\"dim\" style=\"margin-left:6px;\">[${q._section}]</span>` : ""
        item.innerHTML =
          `<div class=\"qm-q\">${idx + 1}. ${q.question || ""} ${section}</div>` +
          (opts.length
            ? `<div>${opts.map(([k, v]) => `<div class=\"qm-opt\"><strong>${k}.</strong> ${v}</div>`).join("")}</div>`
            : "")
        body.appendChild(item)
      })
    }
    const modal = document.getElementById("questionModal")
    if (modal) modal.classList.add("active")
  } catch (_) {
    showToast("Failed to load questions", "error")
  }
}

async function loadViolationReports() {
  try {
    const res = await fetch("/api/violation-reports", { credentials: "include" })
    if (!res.ok) {
      showToast("Failed to load violation reports", "error")
      return
    }
    const data = await res.json()
    const reports = data.reports || []

    const panel = document.getElementById("violationReportsPanel")
    const list = document.getElementById("violationReportsList")

    if (panel) panel.style.display = "block"
    if (list) {
      if (reports.length === 0) {
        list.innerHTML = '<p class="muted">No violations reported.</p>'
        return
      }

      list.innerHTML = reports
        .map((report) => {
          const createdDate = new Date(report.created_at).toLocaleString()
          const finishedDate = report.finished_at ? new Date(report.finished_at).toLocaleString() : "Not finished"
          const status = report.finished_at ? "Completed" : "Terminated"
          const statusColor = report.finished_at ? "var(--success)" : "var(--danger)"

          const isRejected = report.terminated || (!report.finished_at && report.total_violations > 0)
          const rejectionReason = isRejected
            ? (report.termination_reason || report.violations[0]?.type || "UNKNOWN").replace(/_/g, " ").toUpperCase()
            : ""
          const rejectionTime = isRejected
            ? report.terminated_at
              ? new Date(report.terminated_at).toLocaleString()
              : report.violations[0]
                ? new Date(report.violations[0].timestamp).toLocaleString()
                : ""
            : ""

          return `
          <div class="violation-report-item ${isRejected ? 'rejected' : ''}" style="
            background: ${isRejected ? "linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05))" : "var(--glass)"};
            border: 2px solid ${isRejected ? "rgba(239, 68, 68, 0.6)" : "var(--glass-border)"};
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            ${isRejected ? "box-shadow: 0 0 25px rgba(239, 68, 68, 0.3);" : ""}
            position: relative;
          ">
            ${
              isRejected
                ? `
              <div style="
                position: absolute;
                top: -8px;
                right: 16px;
                background: var(--danger);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
              ">REJECTED</div>
            `
                : ""
            }
            
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
              <div style="flex: 1;">
                <h3 style="margin: 0 0 4px 0; font-size: 16px; color: ${isRejected ? "#fca5a5" : "var(--text)"};">${report.email}</h3>
                <div class="muted" style="font-size: 14px;">
                  📅 Created: ${createdDate}<br>
                  ${isRejected ? `🚫 Rejected: ${rejectionTime}` : `✅ Finished: ${finishedDate}`}
                </div>
                ${
                  isRejected
                    ? `
                  <div style="
                    color: var(--danger); 
                    font-weight: 600; 
                    margin-top: 8px; 
                    padding: 12px; 
                    background: rgba(239, 68, 68, 0.15); 
                    border-radius: 8px; 
                    border: 1px solid rgba(239, 68, 68, 0.4);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                  ">
                    <span style="font-size: 18px;">🚫</span>
                    <div>
                      <div style="font-size: 14px; margin-bottom: 2px;">REJECTION CAUSE:</div>
                      <div style="font-size: 16px;">${rejectionReason}</div>
                    </div>
                  </div>
                `
                    : ""
                }
              </div>
              <div style="text-align: right;">
                <div style="color: ${statusColor}; font-weight: 600; margin-bottom: 4px; font-size: 14px;">${status}</div>
                <div class="muted" style="font-size: 12px;">${report.total_violations} violation(s)</div>
                ${
                  isRejected
                    ? `
                  <div style="color: var(--danger); font-size: 11px; margin-top: 4px; font-weight: 600;">
                    BLOCKED ACCESS
                  </div>
                `
                    : ""
                }
              </div>
            </div>
            
            <div class="violations-list">
              ${report.violations
                .map((violation, idx) => {
                  const violationTime = new Date(violation.timestamp)
                  const violationTimeFormatted = violationTime.toLocaleString()
                  const violationTimeAgo = getTimeAgo(violationTime)
                  const violationType = violation.type.replace(/_/g, " ").toUpperCase()
                  const isCritical = ["FACE_MISMATCH", "MULTIPLE_FACES", "NO_FACE"].includes(violation.type)

                  return `
                  <div style="
                    background: ${isCritical ? "rgba(239, 68, 68, 0.15)" : "rgba(239, 68, 68, 0.1)"};
                    border: 2px solid ${isCritical ? "rgba(239, 68, 68, 0.5)" : "rgba(239, 68, 68, 0.3)"};
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 8px;
                    ${isCritical ? "box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);" : ""}
                  ">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                      <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                          <div style="color: #fca5a5; font-weight: 600; font-size: 14px;">${violationType}</div>
                          ${isCritical ? '<span style="background: var(--danger); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700;">CRITICAL</span>' : ""}
                        </div>
                        <div class="muted" style="font-size: 13px; margin-bottom: 6px;">${violation.message || "No message"}</div>
                        <div style="display: flex; align-items: center; gap: 12px; font-size: 12px; flex-wrap: wrap;">
                          <span style="color: var(--muted);">🕒 ${violationTimeFormatted}</span>
                          <span style="color: var(--accent-2); font-weight: 600;">(${violationTimeAgo})</span>
                          ${violation.assignment_id ? `<span style="color: var(--muted); font-size: 11px; background: rgba(59, 130, 246, 0.1); padding: 2px 6px; border-radius: 4px;">Quiz ID: ${violation.assignment_id.substring(0, 8)}...</span>` : ''}
                        </div>
                      </div>
                      <div style="display: flex; gap: 8px; align-items: center;">
                        ${
                          violation.has_image
                            ? `
                          <button onclick="showViolationImage('${violation.assignment_id || report.assignment_id}', ${idx})" style="
                            background: var(--accent);
                            border: none;
                            color: white;
                            padding: 8px 14px;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.2s ease;
                            display: flex;
                            align-items: center;
                            gap: 4px;
                          " onmouseover="this.style.background='var(--accent-2)'" onmouseout="this.style.background='var(--accent)'">
                            📷 View Evidence
                          </button>
                        `
                            : ""
                        }
                        <div style="text-align: center;">
                          <div style="color: ${violation.has_image ? "var(--success)" : "var(--muted)"}; font-size: 11px; font-weight: 600;">
                            ${violation.has_image ? "✅ Evidence" : "❌ No Evidence"}
                          </div>
                          ${violation.has_image ? '<div style="color: var(--muted); font-size: 10px;">Screenshot captured</div>' : ""}
                        </div>
                      </div>
                    </div>
                  </div>
                `
                })
                .join("")}
            </div>
          </div>
        `
        })
        .join("")
    }
  } catch (e) {
    showToast("Failed to load violation reports", "error")
  }
}

// Load analytics charts (replaced with Chart.js version in dashboard.html)
async function loadAnalyticsChart() {
  // This function is now replaced by loadAnalyticsCharts() in dashboard.html
  // Keep for backward compatibility - it will call the new function if available
  if (typeof loadAnalyticsCharts === 'function') {
    return loadAnalyticsCharts();
  }
  console.warn('loadAnalyticsCharts function not found');
}

// Generate CSV report for all users in selected airport and prompt download
async function generateAirportReport() {
  try {
    const sel = document.getElementById("reportAirportSelect")
    const airport = sel ? sel.value : ""
    const resultDiv = document.getElementById("airportReportResult")
    if (resultDiv) {
      resultDiv.innerHTML = '<div style="color: var(--muted);">Loading report...</div>'
    }

    const params = airport ? `?airport=${encodeURIComponent(airport)}` : ""
    const res = await fetch(`/api/stats/airport-report${params}`, { credentials: "include" })
    if (!res.ok) {
      const err = await res.json().catch(()=> ({}))
      showToast(err.error || "Failed to load airport report", "error")
      if (resultDiv) resultDiv.innerHTML = `<div style="color: var(--danger);">Failed to load report</div>`
      return
    }
    const data = await res.json()
    if (!resultDiv) return

    // Render summary cards
    const rows = []
    rows.push(`<div style="display:grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap:12px;">`)
    rows.push(`<div style="background:#fff; border:1px solid var(--glass-border); border-radius:10px; padding:12px;"><div style="font-weight:800; font-size:18px;">Total users</div><div style="font-size:20px; color:var(--secondary-blue); font-weight:800;">${data.total_users ?? 0}</div></div>`)
    rows.push(`<div style="background:#fff; border:1px solid var(--glass-border); border-radius:10px; padding:12px;"><div style="font-weight:800; font-size:18px;">Completed assignments</div><div style="font-size:20px; color:var(--secondary-blue); font-weight:800;">${data.total_completed ?? 0}</div></div>`)
    rows.push(`<div style="background:#fff; border:1px solid var(--glass-border); border-radius:10px; padding:12px;"><div style="font-weight:800; font-size:18px;">Avg. percentage</div><div style="font-size:20px; color:var(--secondary-blue); font-weight:800;">${(data.avg_percentage_score !== null && data.avg_percentage_score !== undefined) ? data.avg_percentage_score + '%' : 'n/a'}</div></div>`)
    rows.push(`<div style="background:#fff; border:1px solid var(--glass-border); border-radius:10px; padding:12px;"><div style="font-weight:800; font-size:18px;">Pass rate</div><div style="font-size:20px; color:var(--secondary-blue); font-weight:800;">${(data.pass_rate !== null && data.pass_rate !== undefined) ? data.pass_rate + '%' : 'n/a'}</div></div>`)
    rows.push(`</div>`)

    // Additional metrics
    rows.push(`<div style="margin-top:12px; display:flex; gap:12px; flex-wrap:wrap;">`)
    rows.push(`<div style="background:#fff; border:1px solid var(--glass-border); border-radius:10px; padding:12px; min-width:220px;"><div style="font-weight:700; color:var(--muted)">Avg. raw score</div><div style="font-size:18px; font-weight:800; color:var(--primary-blue)">${data.avg_score ?? 'n/a'}</div></div>`)
    rows.push(`<div style="background:#fff; border:1px solid var(--glass-border); border-radius:10px; padding:12px; min-width:220px;"><div style="font-weight:700; color:var(--muted)">Avg. attempted</div><div style="font-size:18px; font-weight:800; color:var(--primary-blue)">${data.avg_attempts_used ?? 'n/a'}</div></div>`)
    rows.push(`</div>`)

    resultDiv.innerHTML = rows.join('')
  } catch (e) {
    showToast("Failed to load airport report", "error")
    console.error(e)
    const resultDiv = document.getElementById("airportReportResult")
    if (resultDiv) resultDiv.innerHTML = `<div style="color: var(--danger);">Failed to load report</div>`
  }
}

function getTimeAgo(date) {
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

function filterRejectedOnly() {
  const items = document.querySelectorAll(".violation-report-item")
  const filterBtn = document.getElementById("filterRejectedBtn")
  const showAllBtn = document.getElementById("showAllBtn")

  items.forEach((item) => {
    const isRejected = item.classList.contains('rejected')
    item.style.display = isRejected ? "block" : "none"
  })

  filterBtn.style.display = "none"
  showAllBtn.style.display = "inline-block"
}

function showAllReports() {
  const items = document.querySelectorAll(".violation-report-item")
  const filterBtn = document.getElementById("filterRejectedBtn")
  const showAllBtn = document.getElementById("showAllBtn")

  items.forEach((item) => {
    item.style.display = "block"
  })

  filterBtn.style.display = "inline-block"
  showAllBtn.style.display = "none"
}

async function showViolationImage(assignmentId, violationIndex) {
  try {
    const res = await fetch(`/api/violation-image/${assignmentId}/${violationIndex}`, { credentials: "include" })
    if (!res.ok) {
      showToast("Failed to load violation image", "error")
      return
    }
    const data = await res.json()

    const modal = document.createElement("div")
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.9);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      padding: 20px;
    `

    const modalContent = document.createElement("div")
    modalContent.style.cssText = `
      background: var(--bg1);
      border: 2px solid rgba(239, 68, 68, 0.3);
      border-radius: 16px;
      padding: 24px;
      max-width: 800px;
      width: 100%;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    `

    modalContent.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
          <h3 style="margin: 0 0 4px 0; color: var(--text); font-size: 20px;">Violation Evidence</h3>
          <p style="margin: 0; color: var(--muted); font-size: 14px;">Assignment ID: ${assignmentId}</p>
        </div>
        <button onclick="this.closest('.modal').remove()" style="
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: var(--danger);
          font-size: 18px;
          cursor: pointer;
          padding: 8px 12px;
          border-radius: 8px;
          transition: all 0.2s ease;
        " onmouseover="this.style.background='rgba(239, 68, 68, 0.2)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.1)'">✕ Close</button>
      </div>
      
      <div style="text-align: center; margin-bottom: 20px;">
        <div style="
          background: rgba(239, 68, 68, 0.1);
          border: 2px solid rgba(239, 68, 68, 0.3);
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 16px;
        ">
          <h4 style="color: var(--danger); margin: 0 0 8px 0; font-size: 16px;">Evidence of Violation</h4>
          <p style="color: var(--text); margin: 0; font-size: 14px;">
            This screenshot was automatically captured when the violation occurred
          </p>
        </div>
        
        <img src="data:image/jpeg;base64,${data.image}" style="
          max-width: 100%;
          max-height: 500px;
          border-radius: 12px;
          border: 2px solid rgba(239, 68, 68, 0.3);
          box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        " alt="Violation Evidence">
        
        <div style="
          background: rgba(0, 0, 0, 0.3);
          border-radius: 8px;
          padding: 12px;
          margin-top: 16px;
        ">
          <p style="color: var(--muted); margin: 0; font-size: 14px;">
            <strong>Captured:</strong> ${new Date(data.timestamp).toLocaleString()}
          </p>
          <p style="color: var(--muted); margin: 4px 0 0 0; font-size: 12px;">
            This evidence is stored permanently and cannot be modified
          </p>
        </div>
      </div>
      
      <div style="
        background: rgba(239, 68, 68, 0.05);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 8px;
        padding: 16px;
        margin-top: 16px;
      ">
        <h4 style="color: var(--danger); margin: 0 0 8px 0; font-size: 14px;">Violation Details</h4>
        <p style="color: var(--text); margin: 0; font-size: 13px; line-height: 1.4;">
          This image serves as proof of the violation that led to quiz termination. 
          The candidate's access has been permanently blocked and cannot be restored.
        </p>
      </div>
    `

    modal.appendChild(modalContent)
    modal.className = "modal"
    document.body.appendChild(modal)

    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.remove()
    })

    const handleEscape = (e) => {
      if (e.key === "Escape") {
        modal.remove()
        document.removeEventListener("keydown", handleEscape)
      }
    }
    document.addEventListener("keydown", handleEscape)
  } catch (e) {
    showToast("Failed to load violation image", "error")
  }
}

function openEditUserModal(email, role, airport, matricule) {
  try {
    loadAirportsInto("editAirport")
  } catch (_) {}
  const modal = document.getElementById("editUserModal")
  if (!modal) return
  const fEmail = document.getElementById("editEmail")
  const fRole = document.getElementById("editRole")
  const fAirport = document.getElementById("editAirport")
  const fMat = document.getElementById("editMatricule")
  const info = document.getElementById("editInfo")
  if (info) info.textContent = ""
  if (fEmail) fEmail.value = email || ""
  if (fRole) fRole.value = role || "user"
  setTimeout(() => {
    if (fAirport) fAirport.value = airport || ""
  }, 50)
  if (fMat) fMat.value = matricule || ""
  modal.classList.add("active")
}
;(() => {
  const modal = document.getElementById("editUserModal")
  const btnClose = document.getElementById("editClose")
  const btnCancel = document.getElementById("editCancel")
  const btnSave = document.getElementById("editSave")
  const info = document.getElementById("editInfo")
  function hide() {
    if (modal) modal.classList.remove("active")
  }
  if (btnClose) btnClose.addEventListener("click", hide)
  if (btnCancel) btnCancel.addEventListener("click", hide)
  if (modal)
    modal.addEventListener("click", (e) => {
      if (e.target === modal) hide()
    })
  if (btnSave)
    btnSave.addEventListener("click", async () => {
      const email = document.getElementById("editEmail").value
      const role = document.getElementById("editRole").value
      const airport = document.getElementById("editAirport").value
      const matricule = (document.getElementById("editMatricule").value || "").trim().toUpperCase()
      if (matricule && !/^[A-Z0-9]{8}$/.test(matricule)) {
        if (info) info.textContent = "Matricule must be 8 characters A–Z or 0–9"
        showToast("Invalid matricule format", "error")
        return
      }
      try {
        const res = await fetch(`/api/users/${encodeURIComponent(email)}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ role, airport, matricule }),
        })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) {
          const msg = data.error || "Failed to update user"
          if (info) info.textContent = msg
          showToast(msg, "error")
          return
        }
        showToast("User updated successfully", "success")
        hide()
        loadUsers()
        loadUsersForAssign()
      } catch (e) {
        if (info) info.textContent = String(e)
        showToast(String(e), "error")
      }
    })
})()

function debounce(fn, ms) {
  let t
  return function (...args) {
    clearTimeout(t)
    t = setTimeout(() => fn.apply(this, args), ms || 220)
  }
}

document.getElementById("assignmentSearch").addEventListener(
  "input",
  debounce(() => {
    loadAssignments()
  }, 350),
)
;(() => {
  const modal = document.getElementById("questionModal")
  const close = document.getElementById("qmClose")
  if (close && modal) {
    close.addEventListener("click", () => modal.classList.remove("active"))
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active")
    })
  }
})()

// Wire airport filter controls
document.getElementById('assignAirportFilter')?.addEventListener('change', renderAssignUsers)
document.getElementById('assignmentsAirportFilter')?.addEventListener('change', loadAssignments)
