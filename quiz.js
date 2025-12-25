/* Minimal client-side quiz engine for aviation_quiz_data.json */

(function () {
  /** @typedef {{ id?: number, question: string, options: Record<string,string>, correct_answer?: string|null }} Question */

  const state = {
    raw: null,
    categories: [],
    currentSet: /** @type {Question[]} */ ([]),
    currentIndex: 0,
    answers: /** @type {Record<number,string>} */ ({}),
    scored: /** @type {Array<{id:number, your:string, correct:string}>} */ ([]),
    unkeyed: /** @type {number[]} */ ([]),
    assignmentId: null,
  };

  // Elements
  const titleEl = document.getElementById('title');
  const descEl = document.getElementById('description');
  const sectionSelect = document.getElementById('sectionSelect');
  const questionCountInput = document.getElementById('questionCount');
  const startBtn = document.getElementById('startBtn');
  const setupNotice = document.getElementById('setupNotice');

  const quizCard = document.getElementById('quizCard');
  const progressEl = document.getElementById('progress');
  const questionTextEl = document.getElementById('questionText');
  const optionsEl = document.getElementById('options');
  const nextBtn = document.getElementById('nextBtn');
  const submitBtn = document.getElementById('submitBtn');
  const cancelBtn = document.getElementById('cancelBtn');
  const quizNotice = document.getElementById('quizNotice');

  const resultCard = document.getElementById('resultCard');
  const resultSummary = document.getElementById('resultSummary');
  const resultDetails = document.getElementById('resultDetails');
  const restartBtn = document.getElementById('restartBtn');

  // Utils
  function show(el) { el.classList.remove('hidden'); }
  function hide(el) { el.classList.add('hidden'); }
  function setNotice(el, text) {
    if (!text) { el.textContent = ''; hide(el); return; }
    el.textContent = text; show(el);
  }
  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }
  function sortedEntries(obj) {
    return Object.entries(obj).sort((a, b) => a[0].localeCompare(b[0]));
  }

  async function loadData() {
    try {
      // Try embedded JSON first
      const embedded = document.getElementById('quizData');
      if (embedded && embedded.textContent && embedded.textContent.trim().length > 0) {
        const parsed = JSON.parse(embedded.textContent);
        applyData(parsed);
        return;
      }

      // Check remaining attempts first
      const attemptsRes = await fetch('/api/my/attempts', { credentials: 'include' });
      if (!attemptsRes.ok) throw new Error(`HTTP ${attemptsRes.status}`);
      const attemptsData = await attemptsRes.json();
      const remainingAttempts = 3 - (attemptsData.attempts_used || 0);
      
      if (remainingAttempts <= 0) {
        setNotice(setupNotice, 'You have used all your attempts. No more attempts remaining.');
        hide(startBtn);
        return;
      }

      document.getElementById('attemptsInfo').textContent = `Remaining attempts: ${remainingAttempts}`;
      
      // Fallback: fetch from file
      const res = await fetch('aviation_quiz_data.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      applyData(data);
    } catch (e) {
      setNotice(setupNotice, `Failed to load quiz data: ${e}`);
      console.error(e);
    }
  }

  function applyData(data) {
    state.raw = data.quiz_data || {};
    titleEl.textContent = state.raw.title || 'Aviation Quiz';
    descEl.textContent = state.raw.description || '';
    state.categories = Array.isArray(state.raw.categories) ? state.raw.categories : [];
    populateSections();
  }

  function populateSections() {
    sectionSelect.innerHTML = '';
    const allOpt = document.createElement('option');
    allOpt.value = 'ALL';
    allOpt.textContent = 'All sections';
    sectionSelect.appendChild(allOpt);
    state.categories.forEach((cat, idx) => {
      const opt = document.createElement('option');
      opt.value = String(idx);
      opt.textContent = `${cat.name || 'Section'} — ${cat.description || ''}`.trim();
      sectionSelect.appendChild(opt);
    });
  }

  function validateStart() {
    const count = parseInt(String(questionCountInput.value), 10);
    if (!count || count < 1) {
      setNotice(setupNotice, 'Please enter a valid number of questions (>= 1).');
      return false;
    }
    const pool = collectPool();
    if (pool.length === 0) {
      setNotice(setupNotice, 'No questions available in the selected section.');
      return false;
    }
    if (count > pool.length) {
      setNotice(setupNotice, `Only ${pool.length} questions available; using that many.`);
    } else {
      setNotice(setupNotice, '');
    }
    return true;
  }

  function collectPool() {
    const sel = sectionSelect.value;
    if (sel === 'ALL') {
      const all = [];
      state.categories.forEach(cat => { if (Array.isArray(cat.questions)) all.push(...cat.questions); });
      return all;
    }
    const idx = parseInt(sel, 10);
    if (Number.isNaN(idx) || !state.categories[idx]) return [];
    return Array.isArray(state.categories[idx].questions) ? state.categories[idx].questions : [];
  }

  async function startQuiz() {
    if (!validateStart()) return;
    const desired = parseInt(String(questionCountInput.value), 10);
    const pool = collectPool();
    const set = shuffle(pool.slice());
    state.currentSet = set.slice(0, Math.min(desired, set.length));
    state.currentIndex = 0;
    state.answers = {};
    state.scored = [];
    state.unkeyed = [];
    // create assignment on server (best-effort)
    try {
      const category = (function () {
        const sel = document.getElementById('sectionSelect');
        if (sel && sel.value !== 'ALL') {
          const opt = sel.options[sel.selectedIndex];
          return opt ? String(opt.textContent || '').split(' — ')[0] : null;
        }
        return null;
      })();
      const res = await fetch('/api/quiz-assignments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ category, question_count: desired })
      });
      if (res.ok) {
        const data = await res.json();
        state.assignmentId = data.assignment_id || null;
      } else {
        state.assignmentId = null;
      }
    } catch (_) {
      state.assignmentId = null;
    }
    hide(resultCard);
    show(quizCard);
    renderCurrentQuestion();
  }

  function renderCurrentQuestion() {
    const i = state.currentIndex;
    const q = state.currentSet[i];
    progressEl.textContent = `Question ${i + 1} of ${state.currentSet.length}`;
    questionTextEl.textContent = q.question || '';
    optionsEl.innerHTML = '';
    const entries = sortedEntries(q.options || {});
    entries.forEach(([key, label]) => {
      const id = `opt_${i}_${key}`;
      const div = document.createElement('div');
      div.className = 'option';
      div.innerHTML = `<label><input type="radio" name="q_${i}" value="${key}" id="${id}"> ${key}. ${label}</label>`;
      optionsEl.appendChild(div);
    });
    restoreSelection();
    updateButtons();
    setNotice(quizNotice, '');
  }

  function getSelected() {
    const i = state.currentIndex;
    const sel = /** @type {HTMLInputElement|null} */ (document.querySelector(`input[name="q_${i}"]:checked`));
    return sel ? sel.value : '';
  }

  function restoreSelection() {
    const i = state.currentIndex;
    const saved = state.answers[i];
    if (!saved) return;
    const el = /** @type {HTMLInputElement|null} */ (document.querySelector(`input[name="q_${i}"][value="${saved}"]`));
    if (el) el.checked = true;
  }

  function updateButtons() {
    const last = state.currentIndex === state.currentSet.length - 1;
    if (last) { hide(nextBtn); show(submitBtn); } else { show(nextBtn); hide(submitBtn); }
  }

  function recordAnswerOrWarn() {
    const pick = getSelected();
    if (!pick) {
      setNotice(quizNotice, 'Please select an answer to continue.');
      return false;
    }
    state.answers[state.currentIndex] = pick;
    return true;
  }

  function goNext() {
    if (!recordAnswerOrWarn()) return;
    if (state.currentIndex < state.currentSet.length - 1) {
      state.currentIndex += 1;
      renderCurrentQuestion();
    }
  }

  function cancelQuiz() {
    hide(quizCard);
    hide(resultCard);
    setNotice(setupNotice, 'Quiz cancelled. You can start another one.');
  }

  function submitQuiz() {
    if (!recordAnswerOrWarn()) return;
    // score
    let score = 0;
    let totalWithKeys = 0;
    state.scored = [];
    state.unkeyed = [];
    state.currentSet.forEach((q, i) => {
      const ans = state.answers[i];
      const key = (q.correct_answer == null) ? null : String(q.correct_answer).toUpperCase();
      if (key == null) {
        if (typeof q.id === 'number') state.unkeyed.push(q.id);
        return;
      }
      totalWithKeys += 1;
      if (String(ans).toUpperCase() === key) {
        score += 1;
      } else {
        state.scored.push({ id: (q.id || i), your: String(ans).toUpperCase(), correct: key });
      }
    });

    const attempted = state.currentSet.length;
    resultSummary.textContent = `Attempted: ${attempted} — Score: ${score}/${totalWithKeys}`;
    // Post result for persistence (best effort)
    const category = (function () {
      // If a single category was selected, try to infer its name from the dropdown text
      const sel = document.getElementById('sectionSelect');
      if (sel && sel.value !== 'ALL') {
        const opt = sel.options[sel.selectedIndex];
        return opt ? String(opt.textContent || '').split(' — ')[0] : null;
      }
      return null;
    })();
    // prepare detailed answers for reporting
    const answers = state.currentSet.map((q, i) => ({
      id: (q.id != null ? q.id : i),
      section: q._section || null,
      your: String(state.answers[i] || '').toUpperCase(),
      correct: (q.correct_answer == null ? null : String(q.correct_answer).toUpperCase()),
    }));
    const payload = { category, attempted, correct: score, total_with_keys: totalWithKeys, answers };
    if (state.assignmentId) payload.assignment_id = state.assignmentId;
    fetch('/api/scores', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload)
    }).catch(() => {});

    const details = [];
    if (state.scored.length) {
      const items = state.scored.map(r => `<li>Question ID ${r.id}: Your answer ${r.your} | Correct ${r.correct}</li>`).join('');
      details.push(`<div><strong>Review:</strong><ul class="result-list">${items}</ul></div>`);
    }
    if (state.unkeyed.length) {
      details.push(`<div class="notice">Not scored (no answer key): ${state.unkeyed.join(', ')}</div>`);
    }
    // answered-all summary
    const answeredCount = Object.keys(state.answers).length;
    const allAnswered = answeredCount === state.currentSet.length;
    details.unshift(`<div><strong>Summary:</strong> ${allAnswered ? 'All questions answered.' : `Answered ${answeredCount}/${state.currentSet.length}.`}</div>`);
    resultDetails.innerHTML = details.join('');

    hide(quizCard);
    show(resultCard);
    // finish notification
    try { alert('Good luck with check'); } catch (_) {}
  }

  // Events
  startBtn.addEventListener('click', startQuiz);
  nextBtn.addEventListener('click', goNext);
  cancelBtn.addEventListener('click', cancelQuiz);
  submitBtn.addEventListener('click', submitQuiz);
  restartBtn.addEventListener('click', () => { hide(resultCard); setNotice(setupNotice, ''); });

  // init
  loadData();
})();


