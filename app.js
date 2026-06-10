(() => {
  const STORAGE_KEY = "phraseflow.state.v1";
  const EXPORT_VERSION = 1;
  const DAY = 24 * 60 * 60 * 1000;
  const HOUR = 60 * 60 * 1000;
  const phrases = Array.isArray(window.PHRASES) ? window.PHRASES : [];

  const els = {
    deckSummary: document.querySelector("#deckSummary"),
    statSeen: document.querySelector("#statSeen"),
    statKnown: document.querySelector("#statKnown"),
    statReview: document.querySelector("#statReview"),
    progressRing: document.querySelector("#progressRing"),
    progressPercent: document.querySelector("#progressPercent"),
    tabs: Array.from(document.querySelectorAll(".tab")),
    card: document.querySelector("#phraseCard"),
    cardRank: document.querySelector("#cardRank"),
    cardGram: document.querySelector("#cardGram"),
    phraseText: document.querySelector("#phraseText"),
    phraseContext: document.querySelector("#phraseContext"),
    answerPanel: document.querySelector("#answerPanel"),
    meaningText: document.querySelector("#meaningText"),
    noteText: document.querySelector("#noteText"),
    exampleText: document.querySelector("#exampleText"),
    exampleJa: document.querySelector("#exampleJa"),
    sourceLine: document.querySelector("#sourceLine"),
    leftLabel: document.querySelector("#leftLabel"),
    rightLabel: document.querySelector("#rightLabel"),
    reviewButton: document.querySelector("#reviewButton"),
    knownButton: document.querySelector("#knownButton"),
    undoButton: document.querySelector("#undoButton"),
    exportButton: document.querySelector("#exportButton"),
    importInput: document.querySelector("#importInput")
  };

  let state = loadState();
  let filter = state.filter || "all";
  let queue = [];
  let currentIndex = 0;
  let revealed = false;
  let pointer = null;
  let history = [];
  let locked = false;

  function loadState() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (saved && saved.version === EXPORT_VERSION && saved.records) return saved;
    } catch (error) {
      console.warn("Could not read saved state", error);
    }
    return { version: EXPORT_VERSION, records: {}, filter: "all", updatedAt: Date.now() };
  }

  function saveState() {
    state.filter = filter;
    state.updatedAt = Date.now();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function recordFor(id) {
    return state.records[id] || null;
  }

  function makeRecord(id) {
    return {
      id,
      seen: 0,
      known: 0,
      review: 0,
      streak: 0,
      status: "new",
      dueAt: 0,
      updatedAt: 0
    };
  }

  function hasSeen(phrase) {
    const record = recordFor(phrase.id);
    return Boolean(record && record.seen > 0);
  }

  function isReview(phrase) {
    const record = recordFor(phrase.id);
    return Boolean(record && record.status === "review");
  }

  function priority(phrase) {
    const record = recordFor(phrase.id);
    if (!record) return 20 + phrase.rank / 1000;
    if (record.status === "review") return 0 + phrase.rank / 1000;
    if (record.status === "known") return 50 + record.streak + phrase.rank / 1000;
    return 10 + phrase.rank / 1000;
  }

  function buildQueue(focusId) {
    queue = phrases
      .filter((phrase) => {
        if (filter === "new") return !hasSeen(phrase);
        if (filter === "review") return isReview(phrase);
        return true;
      })
      .sort((a, b) => priority(a) - priority(b));

    currentIndex = 0;
    if (focusId) {
      const index = queue.findIndex((phrase) => phrase.id === focusId);
      if (index >= 0) currentIndex = index;
    }
    revealed = false;
    render();
  }

  function currentPhrase() {
    return queue[currentIndex] || null;
  }

  function render() {
    updateTabs();
    updateStats();

    const phrase = currentPhrase();
    resetCardMotion();

    if (!phrase) {
      renderEmpty();
      return;
    }

    els.card.classList.remove("is-empty");
    els.cardRank.textContent = `rank #${phrase.rank.toLocaleString()}`;
    els.cardGram.textContent = `${phrase.gram}-gram`;
    els.phraseText.textContent = phrase.text;
    els.phraseContext.textContent = phrase.tags.slice(0, 3).join(" / ");
    els.meaningText.textContent = phrase.meaning;
    els.noteText.textContent = phrase.note;
    els.exampleText.textContent = phrase.example;
    els.exampleJa.textContent = phrase.exampleJa;
    els.sourceLine.textContent = `${phrase.source} · ${phrase.freq.toLocaleString()} hits`;
    els.answerPanel.hidden = !revealed;
    els.deckSummary.textContent = `${labelForFilter(filter)} · ${currentIndex + 1}/${queue.length}`;
  }

  function renderEmpty() {
    const label = filter === "review" ? "Review clear" : filter === "new" ? "No new cards" : "Session clear";
    els.card.classList.add("is-empty");
    els.cardRank.textContent = "done";
    els.cardGram.textContent = `${phrases.length} cards`;
    els.phraseText.textContent = label;
    els.phraseContext.textContent = labelForFilter(filter);
    els.meaningText.textContent = filter === "review" ? "復習待ちのカードはありません。" : "このデッキは一通り終わりました。";
    els.noteText.textContent = "履歴はこの端末に保存されています。";
    els.exampleText.textContent = "Switch decks or keep practicing tomorrow.";
    els.exampleJa.textContent = "デッキを切り替えるか、また明日続けられます。";
    els.sourceLine.textContent = "";
    els.answerPanel.hidden = false;
    els.deckSummary.textContent = `${labelForFilter(filter)} · 0/${queue.length}`;
  }

  function updateTabs() {
    els.tabs.forEach((tab) => {
      const active = tab.dataset.filter === filter;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
    });
  }

  function updateStats() {
    const records = Object.values(state.records);
    const seen = records.filter((record) => record.seen > 0).length;
    const known = records.filter((record) => record.status === "known").length;
    const review = records.filter((record) => record.status === "review").length;
    const percent = phrases.length ? Math.round((known / phrases.length) * 100) : 0;

    els.statSeen.textContent = seen.toLocaleString();
    els.statKnown.textContent = known.toLocaleString();
    els.statReview.textContent = review.toLocaleString();
    els.progressPercent.textContent = `${percent}%`;
    els.progressRing.style.setProperty("--progress", `${percent * 3.6}deg`);
  }

  function labelForFilter(value) {
    if (value === "new") return "New deck";
    if (value === "review") return "Review deck";
    return "Core deck";
  }

  function toggleReveal() {
    if (!currentPhrase()) return;
    revealed = !revealed;
    els.answerPanel.hidden = !revealed;
  }

  function grade(kind) {
    if (locked) return;
    const phrase = currentPhrase();
    if (!phrase) return;

    locked = true;
    const previous = state.records[phrase.id] ? structuredCloneSafe(state.records[phrase.id]) : null;
    const record = state.records[phrase.id] || makeRecord(phrase.id);
    const now = Date.now();

    history.push({ id: phrase.id, previous, filter, index: currentIndex });

    record.seen += 1;
    record.updatedAt = now;

    if (kind === "known") {
      record.known += 1;
      record.streak += 1;
      record.status = "known";
      record.dueAt = now + Math.min(30, 2 ** Math.min(record.streak, 5)) * DAY;
    } else {
      record.review += 1;
      record.streak = 0;
      record.status = "review";
      record.dueAt = now + HOUR;
    }

    state.records[phrase.id] = record;
    saveState();
    animateAway(kind);

    window.setTimeout(() => {
      queue.splice(currentIndex, 1);
      if (queue.length > 0) currentIndex %= queue.length;
      revealed = false;
      locked = false;
      render();
    }, 210);
  }

  function undo() {
    const last = history.pop();
    if (!last) return;

    if (last.previous) {
      state.records[last.id] = last.previous;
    } else {
      delete state.records[last.id];
    }
    filter = last.filter || filter;
    saveState();
    buildQueue(last.id);
  }

  function structuredCloneSafe(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
  }

  function animateAway(kind) {
    const direction = kind === "known" ? 1 : -1;
    els.card.classList.toggle("is-known", kind === "known");
    els.card.classList.toggle("is-review", kind === "review");
    els.card.style.transform = `translate3d(${direction * 120}%, -8px, 0) rotate(${direction * 12}deg)`;
    els.card.style.opacity = "0";
  }

  function resetCardMotion() {
    els.card.classList.remove("is-dragging", "is-known", "is-review");
    els.leftLabel.classList.remove("is-visible");
    els.rightLabel.classList.remove("is-visible");
    els.card.style.transform = "";
    els.card.style.opacity = "";
  }

  function showSwipeHint(dx) {
    const showRight = dx > 26;
    const showLeft = dx < -26;
    els.rightLabel.classList.toggle("is-visible", showRight);
    els.leftLabel.classList.toggle("is-visible", showLeft);
    els.card.classList.toggle("is-known", showRight);
    els.card.classList.toggle("is-review", showLeft);
  }

  function onPointerDown(event) {
    if (locked || !currentPhrase()) return;
    pointer = {
      id: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      dx: 0,
      dy: 0,
      moved: false
    };
    els.card.classList.add("is-dragging");
    els.card.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event) {
    if (!pointer || pointer.id !== event.pointerId) return;
    pointer.dx = event.clientX - pointer.startX;
    pointer.dy = event.clientY - pointer.startY;
    pointer.moved = pointer.moved || Math.hypot(pointer.dx, pointer.dy) > 10;

    if (Math.abs(pointer.dx) < 4) return;

    const rotate = Math.max(-10, Math.min(10, pointer.dx / 16));
    els.card.style.transform = `translate3d(${pointer.dx}px, ${pointer.dy * 0.08}px, 0) rotate(${rotate}deg)`;
    showSwipeHint(pointer.dx);
  }

  function onPointerUp(event) {
    if (!pointer || pointer.id !== event.pointerId) return;
    const { dx, dy, moved } = pointer;
    pointer = null;
    els.card.classList.remove("is-dragging");

    if (Math.abs(dx) > 92 && Math.abs(dx) > Math.abs(dy) * 1.1) {
      grade(dx > 0 ? "known" : "review");
      return;
    }

    resetCardMotion();
    if (!moved) toggleReveal();
  }

  function exportProgress() {
    const payload = {
      app: "Phraseflow",
      version: EXPORT_VERSION,
      exportedAt: new Date().toISOString(),
      deckSize: phrases.length,
      records: state.records
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `phraseflow-progress-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function importProgress(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      try {
        const payload = JSON.parse(String(reader.result || "{}"));
        if (!payload.records || typeof payload.records !== "object") {
          throw new Error("No records found");
        }
        state.records = payload.records;
        saveState();
        history = [];
        buildQueue();
      } catch (error) {
        window.alert("読み込めないJSONです。");
        console.warn(error);
      } finally {
        els.importInput.value = "";
      }
    });
    reader.readAsText(file);
  }

  function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) return;
    if (!/^https?:$/.test(location.protocol)) return;
    navigator.serviceWorker.register("./sw.js").catch((error) => {
      console.warn("Service worker registration failed", error);
    });
  }

  els.card.addEventListener("pointerdown", onPointerDown);
  els.card.addEventListener("pointermove", onPointerMove);
  els.card.addEventListener("pointerup", onPointerUp);
  els.card.addEventListener("pointercancel", () => {
    pointer = null;
    resetCardMotion();
  });
  els.card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleReveal();
    }
    if (event.key === "ArrowRight") grade("known");
    if (event.key === "ArrowLeft") grade("review");
  });

  els.reviewButton.addEventListener("click", () => grade("review"));
  els.knownButton.addEventListener("click", () => grade("known"));
  els.undoButton.addEventListener("click", undo);
  els.exportButton.addEventListener("click", exportProgress);
  els.importInput.addEventListener("change", (event) => importProgress(event.target.files[0]));
  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      filter = tab.dataset.filter;
      saveState();
      buildQueue();
    });
  });

  buildQueue();
  registerServiceWorker();
})();
