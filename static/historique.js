const PAGE_SIZE = 15;
let offset = 0;
let habitFilter = "";
let habitsById = {};

async function loadHabits() {
  const res = await fetch("/habits");
  const habits = await res.json();

  const select = document.getElementById("habit-filter");
  for (const h of habits) {
    habitsById[h.id] = h;
    const opt = document.createElement("option");
    opt.value = h.id;
    opt.textContent = h.name;
    select.appendChild(opt);
  }
}

function formatQuantity(amount, unit) {
  return unit.length > 1 ? `${amount} ${unit}` : `${amount}${unit}`;
}

function formatValue(item) {
  const habit = habitsById[item.habit_id];
  if (!habit) {
    return `${item.value}`;
  }
  if (habit.kind === "binary") {
    return "Fait";
  }
  const unit = habit.unit || "";
  return `${formatQuantity(item.value, unit)} / ${formatQuantity(habit.target, unit)}`;
}

function formatEntryDate(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString("fr-FR");
}

const STATUS_ICONS = { complete: "✓", incomplete: "✕", neutralized: "–" };

async function fetchStatusLookup(items) {
  const uniqueDates = [...new Set(items.map((item) => item.logical_date))];
  const lookup = {};

  await Promise.all(
    uniqueDates.map(async (date) => {
      const res = await fetch(`/days/${date}`);
      const day = await res.json();
      for (const h of day.habits) {
        lookup[`${date}:${h.habit_id}`] = h.status;
      }
    })
  );

  return lookup;
}

function renderHistory(data, statusLookup) {
  const container = document.getElementById("history-rows");
  container.innerHTML = "";

  for (const item of data.items) {
    const row = document.createElement("div");
    row.className = "history-row";

    const name = document.createElement("span");
    name.textContent = item.habit_name;

    const date = document.createElement("span");
    date.textContent = formatEntryDate(item.logical_date);

    const value = document.createElement("span");
    value.className = "history-value";

    // "Fait" already implies success on its own for a binary habit - an
    // icon there would describe the period's status, not this entry, and
    // can contradict the word right next to it (e.g. a week-scope habit
    // done today but short on its weekly cadence). Only quantified values
    // are ambiguous enough on their own to benefit from the icon.
    const habit = habitsById[item.habit_id];
    const status = statusLookup[`${item.logical_date}:${item.habit_id}`];
    if (status && habit && habit.kind !== "binary") {
      const dot = document.createElement("span");
      dot.className = `status-dot status-${status}`;
      dot.textContent = STATUS_ICONS[status] || "";
      dot.setAttribute("aria-hidden", "true");
      value.appendChild(dot);
    }
    value.appendChild(document.createTextNode(formatValue(item)));

    const del = document.createElement("button");
    del.type = "button";
    del.className = "icon-button";
    del.textContent = "🗑";
    del.setAttribute("aria-label", "Supprimer cette saisie");
    del.addEventListener("click", () => deleteEntry(item.id));

    row.append(name, date, value, del);
    container.appendChild(row);
  }

  const total = data.total;
  document.getElementById("history-summary").textContent =
    total === 0
      ? "Aucune saisie"
      : `Saisies ${offset + 1}-${Math.min(offset + PAGE_SIZE, total)} sur ${total}`;

  document.getElementById("history-prev").disabled = offset === 0;
  document.getElementById("history-next").disabled = offset + PAGE_SIZE >= total;
}

async function deleteEntry(id) {
  await fetch(`/completions/${id}`, { method: "DELETE" });
  loadHistory();
}

async function loadHistory() {
  const params = new URLSearchParams({ limit: PAGE_SIZE, offset });
  if (habitFilter) {
    params.set("habit_id", habitFilter);
  }

  const res = await fetch(`/history?${params}`);
  const data = await res.json();

  // A deletion can empty out the current page (e.g. the last row of the
  // last page): step back rather than showing an empty, out-of-range page.
  if (data.items.length === 0 && offset > 0) {
    offset = Math.max(0, offset - PAGE_SIZE);
    return loadHistory();
  }

  const statusLookup = await fetchStatusLookup(data.items);
  renderHistory(data, statusLookup);
}

document.getElementById("habit-filter").addEventListener("change", (event) => {
  habitFilter = event.target.value;
  offset = 0;
  loadHistory();
});

document.getElementById("history-prev").addEventListener("click", () => {
  if (offset > 0) {
    offset = Math.max(0, offset - PAGE_SIZE);
    loadHistory();
  }
});

document.getElementById("history-next").addEventListener("click", () => {
  offset += PAGE_SIZE;
  loadHistory();
});

(async function init() {
  await loadHabits();
  await loadHistory();
})();
