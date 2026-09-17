function toISODate(d) {
  const tz = d.getTimezoneOffset() * 60000;
  return new Date(d - tz).toISOString().slice(0, 10);
}

function todayISO() {
  return toISODate(new Date());
}

const today = todayISO();
let viewDate = today;

function stepDate(dateStr, scope, direction) {
  const d = new Date(`${dateStr}T00:00:00`);
  if (scope === "day") {
    d.setDate(d.getDate() + direction);
  } else if (scope === "week") {
    d.setDate(d.getDate() + direction * 7);
  } else if (scope === "month") {
    d.setDate(1);
    d.setMonth(d.getMonth() + direction);
  } else if (scope === "year") {
    d.setDate(1);
    d.setMonth(0);
    d.setFullYear(d.getFullYear() + direction);
  }
  return toISODate(d);
}

function periodStart(scope, dateStr) {
  const d = new Date(`${dateStr}T00:00:00`);
  if (scope === "week") {
    const dayIndex = (d.getDay() + 6) % 7; // Monday = 0
    d.setDate(d.getDate() - dayIndex);
  } else if (scope === "month") {
    d.setDate(1);
  } else if (scope === "year") {
    d.setDate(1);
    d.setMonth(0);
  }
  return toISODate(d);
}

function isCurrentPeriod(scope, dateStr) {
  return periodStart(scope, dateStr) === periodStart(scope, today);
}

async function loadDay() {
  const res = await fetch(`/days/${viewDate}`);
  const data = await res.json();
  renderDay(data);
}

function formatDateLabel(isoDate) {
  const d = new Date(`${isoDate}T00:00:00`);
  const label = d.toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function formatPeriodLabel(scope, dateStr) {
  if (scope === "day") {
    return formatDateLabel(dateStr);
  }
  if (scope === "week") {
    const monday = periodStart("week", dateStr);
    const label = new Date(`${monday}T00:00:00`).toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    return `Semaine du ${label}`;
  }
  const d = new Date(`${dateStr}T00:00:00`);
  if (scope === "month") {
    const label = d.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
    return label.charAt(0).toUpperCase() + label.slice(1);
  }
  return `${d.getFullYear()}`;
}

function moodEmoji(ratio) {
  if (ratio === null) return "😐";
  if (ratio >= 1) return "😄";
  if (ratio >= 0.7) return "🙂";
  if (ratio >= 0.4) return "😐";
  if (ratio > 0) return "😕";
  return "😢";
}

const PAGE_SIZE = 3;
let currentStart = 0;
let currentHabits = [];

const SCOPE_LABELS = { day: "Quotidienne", week: "Hebdomadaire", month: "Mensuelle", year: "Annuelle" };
const SCOPE_NOUN = { day: "Journée", week: "Semaine", month: "Mois", year: "Année" };
const SCOPE_CURRENT_NOUN = { day: "Aujourd'hui", week: "Cette semaine", month: "Ce mois-ci", year: "Cette année" };
const STATUS_LABELS = { complete: "Complet", incomplete: "Incomplet", neutralized: "Neutralisée" };

function habitPercent(h) {
  const isDayScope = h.period_scope === "day";
  const denominator = isDayScope ? Number(h.target) : h.cadence;
  const numerator = isDayScope ? Number(h.today_total) : h.days_met;
  if (!denominator || denominator <= 0) return 0;
  return Math.min(100, Math.round((numerator / denominator) * 100));
}

function habitProgressText(h) {
  if (h.period_scope !== "day") {
    return `${h.days_met} / ${h.cadence} jours`;
  }
  if (h.kind === "binary") {
    return Number(h.today_total) >= Number(h.target) ? "Fait" : "À faire";
  }
  const unit = h.unit || "";
  return `${h.today_total}${unit} / ${h.target}${unit}`;
}

function buildHabitCard(h, interactive) {
  const card = document.createElement("article");
  card.className = "habit-card";

  const header = document.createElement("div");
  header.className = `habit-card-header status-${h.status}`;

  const percent = document.createElement("span");
  percent.className = "habit-card-percent";
  percent.textContent = `${habitPercent(h)}%`;

  const statusText = document.createElement("span");
  statusText.className = "habit-card-status";
  statusText.textContent = STATUS_LABELS[h.status] || h.status;

  header.append(percent, statusText);
  card.appendChild(header);

  const body = document.createElement("div");
  body.className = "habit-card-body";

  const name = document.createElement("h3");
  name.className = "habit-card-name";
  name.textContent = h.name + (h.is_essential ? " ★" : "");

  const scope = document.createElement("p");
  scope.className = "habit-card-scope";
  scope.textContent = SCOPE_LABELS[h.period_scope] || h.period_scope;

  const progressText = document.createElement("p");
  progressText.className = "habit-card-progress";
  progressText.textContent = habitProgressText(h);

  const bar = document.createElement("div");
  bar.className = "progress-bar";
  const fill = document.createElement("div");
  fill.className = "progress-bar-fill";
  fill.style.width = `${habitPercent(h)}%`;
  bar.appendChild(fill);

  body.append(name, scope, progressText, bar);

  // Retroactive logging happens through Historique, not through this
  // browsing view - quick-log controls only make sense on the current period.
  if (interactive) {
    const action = document.createElement("div");
    action.className = "habit-card-action";

    if (h.kind === "binary") {
      const btn = document.createElement("button");
      btn.textContent = "✓";
      btn.addEventListener("click", () => logCompletion(h.habit_id, 1));
      action.appendChild(btn);
    } else {
      const input = document.createElement("input");
      input.type = "number";
      input.step = "0.01";
      input.placeholder = h.unit || "val.";
      input.className = "input-small";

      const btn = document.createElement("button");
      btn.textContent = "Ajouter";
      btn.addEventListener("click", () => {
        const value = parseFloat(input.value);
        if (!value || value <= 0) return;
        logCompletion(h.habit_id, value);
      });

      action.append(input, btn);
    }

    body.appendChild(action);
  }

  card.appendChild(body);

  return card;
}

let currentInteractive = true;

function renderHabitCards() {
  const container = document.getElementById("habit-cards");
  container.innerHTML = "";

  const total = currentHabits.length;
  const maxStart = Math.max(0, total - PAGE_SIZE);
  currentStart = Math.min(currentStart, maxStart);

  const pageHabits = currentHabits.slice(currentStart, currentStart + PAGE_SIZE);

  for (const h of pageHabits) {
    container.appendChild(buildHabitCard(h, currentInteractive));
  }

  document.getElementById("pagination-label").textContent =
    total === 0
      ? "Aucune habitude"
      : `${currentStart + 1}-${Math.min(currentStart + PAGE_SIZE, total)} sur ${total} habitudes`;

  document.getElementById("prev-page").disabled = currentStart === 0;
  document.getElementById("next-page").disabled = currentStart >= maxStart;
}

document.getElementById("prev-page").addEventListener("click", () => {
  if (currentStart > 0) {
    currentStart -= 1;
    renderHabitCards();
  }
});

document.getElementById("next-page").addEventListener("click", () => {
  if (currentStart + PAGE_SIZE < currentHabits.length) {
    currentStart += 1;
    renderHabitCards();
  }
});

function renderDay(data) {
  const scope = navScopeField.dataset.value;
  const interactive = isCurrentPeriod(scope, viewDate);
  currentInteractive = interactive;

  document.getElementById("page-title").textContent =
    interactive ? SCOPE_CURRENT_NOUN[scope] : SCOPE_NOUN[scope];
  document.getElementById("cards-heading").textContent = SCOPE_NOUN[scope];
  document.getElementById("today-date").textContent = formatPeriodLabel(scope, viewDate);

  document.getElementById("readonly-badge").hidden = interactive;
  document.getElementById("creation-section").hidden = !interactive;

  // Only keep habits whose own scope matches the selected view: a "Semaine"
  // view shows weekly goals, not daily ones mixed in.
  const scopedHabits = data.habits.filter((h) => h.period_scope === scope);

  // Neutralized habits are excluded from the ratio/essentials count too,
  // same reasoning as the back-end's essentials_met: a habit that's neither
  // a success nor a failure that day shouldn't count against you either.
  const evaluable = scopedHabits.filter((h) => h.status !== "neutralized");
  const met = evaluable.filter((h) => h.status === "complete").length;
  document.getElementById("ratio-value").textContent = `${met}/${evaluable.length}`;

  const essentials = evaluable.filter((h) => h.is_essential);
  const essentialsMet = essentials.filter((h) => h.status === "complete").length;
  document.getElementById("essentials-value").textContent =
    `${essentialsMet}/${essentials.length}`;

  const overallRatio = evaluable.length > 0 ? met / evaluable.length : null;
  document.getElementById("mood").textContent = moodEmoji(overallRatio);

  currentHabits = scopedHabits;
  renderHabitCards();
}

async function logCompletion(habitId, value) {
  await fetch("/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ habit_id: habitId, logical_date: today, value }),
  });
  loadDay();
}

function setupSegmented(container, onChange) {
  const buttons = container.querySelectorAll(".segmented-option");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      container.dataset.value = btn.dataset.value;
      onChange();
    });
  });
}

function resetSegmented(container) {
  const buttons = container.querySelectorAll(".segmented-option");
  buttons.forEach((b, i) => b.classList.toggle("active", i === 0));
  container.dataset.value = buttons[0].dataset.value;
}

const kindField = document.querySelector('.segmented[data-field="kind"]');
const scopeField = document.querySelector('.segmented[data-field="period_scope"]');
const directionField = document.querySelector('.segmented[data-field="direction"]');
const quantifiedFields = document.getElementById("quantified-fields");
const cadenceCountGroup = document.getElementById("cadence-count-group");
const essentialToggle = document.getElementById("essential-toggle");

function updateFormVisibility() {
  quantifiedFields.hidden = kindField.dataset.value !== "quantified";
  cadenceCountGroup.hidden = scopeField.dataset.value === "day";
}

setupSegmented(kindField, updateFormVisibility);
setupSegmented(scopeField, updateFormVisibility);
setupSegmented(directionField, () => {});

essentialToggle.addEventListener("click", () => {
  const isActive = essentialToggle.dataset.active === "true";
  essentialToggle.dataset.active = isActive ? "false" : "true";
  essentialToggle.classList.toggle("active", !isActive);
});

updateFormVisibility();

document.getElementById("habit-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;

  const kind = kindField.dataset.value;
  const periodScope = scopeField.dataset.value;
  const isQuantified = kind === "quantified";

  const data = {
    name: form.name.value,
    kind,
    unit: isQuantified ? form.unit.value || null : null,
    period_scope: periodScope,
    cadence: periodScope === "day" ? 1 : parseInt(form.cadence.value, 10),
    target: isQuantified ? form.target.value : "1",
    direction: isQuantified ? directionField.dataset.value : "at_least",
    is_essential: essentialToggle.dataset.active === "true",
    active_from: today,
  };

  const res = await fetch("/habits", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  const errorEl = document.getElementById("habit-form-error");

  if (!res.ok) {
    const err = await res.json();
    errorEl.textContent = err.detail || "Erreur lors de la création";
    return;
  }

  errorEl.textContent = "";
  form.reset();
  resetSegmented(kindField);
  resetSegmented(scopeField);
  resetSegmented(directionField);
  essentialToggle.dataset.active = "false";
  essentialToggle.classList.remove("active");
  updateFormVisibility();
  loadDay();
});

const navScopeField = document.querySelector('.segmented[data-field="nav-scope"]');

setupSegmented(navScopeField, () => {
  // switching scope jumps back to the current period for that scope,
  // rather than reinterpreting whatever date happened to be selected
  viewDate = today;
  currentStart = 0;
  loadDay();
});

document.getElementById("nav-prev").addEventListener("click", () => {
  viewDate = stepDate(viewDate, navScopeField.dataset.value, -1);
  currentStart = 0;
  loadDay();
});

document.getElementById("nav-next").addEventListener("click", () => {
  viewDate = stepDate(viewDate, navScopeField.dataset.value, 1);
  currentStart = 0;
  loadDay();
});

document.getElementById("nav-today").addEventListener("click", () => {
  viewDate = today;
  currentStart = 0;
  loadDay();
});

loadDay();
