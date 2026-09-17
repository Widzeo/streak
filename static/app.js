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

  const list = document.getElementById("habit-list");
  list.innerHTML = "";

  for (const h of data.habits) {
    const li = document.createElement("li");
    li.className = `habit status-${h.status}`;

    const label = document.createElement("span");
    label.textContent = h.name + (h.is_essential ? " ★" : "");
    li.appendChild(label);

    const progress = document.createElement("span");
    progress.className = "progress";
    progress.textContent =
      h.period_scope === "day"
        ? `${h.today_total} / ${h.target}`
        : `${h.days_met} / ${h.cadence} jours`;
    li.appendChild(progress);

    if (h.kind === "binary") {
      const btn = document.createElement("button");
      btn.textContent = "✓";
      btn.addEventListener("click", () => logCompletion(h.habit_id, 1));
      li.appendChild(btn);
    } else {
      const input = document.createElement("input");
      input.type = "number";
      input.step = "0.01";
      input.placeholder = h.unit || "valeur";
      input.style.width = "5em";

      const btn = document.createElement("button");
      btn.textContent = "Ajouter";
      btn.addEventListener("click", () => {
        const value = parseFloat(input.value);
        if (!value || value <= 0) return;
        logCompletion(h.habit_id, value);
      });

      li.appendChild(input);
      li.appendChild(btn);
    }

    list.appendChild(li);
  }
}

async function logCompletion(habitId, value) {
  await fetch("/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ habit_id: habitId, logical_date: today, value }),
  });
  loadDay();
}

document.getElementById("habit-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;

  const data = {
    name: form.name.value,
    kind: form.kind.value,
    unit: form.unit.value || null,
    period_scope: form.period_scope.value,
    cadence: parseInt(form.cadence.value, 10),
    target: form.target.value,
    direction: form.direction.value,
    is_essential: form.is_essential.checked,
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
  loadDay();
});

loadDay();
