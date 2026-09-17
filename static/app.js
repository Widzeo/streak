function todayISO() {
  const d = new Date();
  const tz = d.getTimezoneOffset() * 60000;
  return new Date(d - tz).toISOString().slice(0, 10);
}

const today = todayISO();

async function loadDay() {
  const res = await fetch(`/days/${today}`);
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

function buildHabitCard(h) {
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

  body.append(name, scope, progressText, bar, action);
  card.appendChild(body);

  return card;
}

function renderHabitCards() {
  const container = document.getElementById("habit-cards");
  container.innerHTML = "";

  const total = currentHabits.length;
  const maxStart = Math.max(0, total - PAGE_SIZE);
  currentStart = Math.min(currentStart, maxStart);

  const pageHabits = currentHabits.slice(currentStart, currentStart + PAGE_SIZE);

  for (const h of pageHabits) {
    container.appendChild(buildHabitCard(h));
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
  document.getElementById("today-date").textContent = formatDateLabel(data.date);

  document.getElementById("ratio-value").textContent =
    `${data.habits_met}/${data.habits_total}`;

  // Neutralized habits are excluded from the essentials count too, same
  // reasoning as the back-end's essentials_met: a habit that's neither a
  // success nor a failure that day shouldn't count against you either.
  const evaluable = data.habits.filter((h) => h.status !== "neutralized");
  const essentials = evaluable.filter((h) => h.is_essential);
  const essentialsMet = essentials.filter((h) => h.status === "complete").length;
  document.getElementById("essentials-value").textContent =
    `${essentialsMet}/${essentials.length}`;

  const overallRatio = data.habits_total > 0 ? data.habits_met / data.habits_total : null;
  document.getElementById("mood").textContent = moodEmoji(overallRatio);

  currentHabits = data.habits;
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

loadDay();
