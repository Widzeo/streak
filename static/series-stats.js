const SCOPE_UNIT = { day: "jours", week: "sem.", month: "mois", year: "ans" };

let allStreaks = [];

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

async function loadStreaks() {
  const [habitsRes, streaksRes] = await Promise.all([fetch("/habits"), fetch("/stats/streaks")]);
  const habits = await habitsRes.json();
  const streaksData = await streaksRes.json();

  const habitsById = {};
  for (const h of habits) {
    habitsById[h.id] = h;
  }

  allStreaks = streaksData.streaks.map((s) => {
    const habit = habitsById[s.habit_id];
    return {
      ...s,
      is_essential: habit ? habit.is_essential : false,
      period_scope: habit ? habit.period_scope : "day",
    };
  });

  renderStreakCards();
}

function buildStreakFigure(value, unit, label, extraClass) {
  const figure = document.createElement("div");
  figure.className = extraClass ? `streak-figure ${extraClass}` : "streak-figure";

  const amount = document.createElement("span");
  amount.className = "streak-figure-value";
  amount.textContent = `${value}`;

  const unitEl = document.createElement("span");
  unitEl.className = "streak-figure-unit";
  unitEl.textContent = ` ${unit}`;

  const labelEl = document.createElement("span");
  labelEl.className = "streak-figure-label";
  labelEl.textContent = label;

  figure.append(amount, unitEl, labelEl);
  return figure;
}

function buildStreakCard(streak) {
  const card = document.createElement("article");
  card.className = "streak-card";

  const name = document.createElement("h3");
  name.className = "streak-card-name";
  name.textContent = streak.name + (streak.is_essential ? " ★" : "");
  card.appendChild(name);

  const unit = SCOPE_UNIT[streak.period_scope] || "jours";

  const numbers = document.createElement("div");
  numbers.className = "streak-card-numbers";
  numbers.append(
    buildStreakFigure(streak.current_streak, unit, "Série actuelle"),
    buildStreakFigure(streak.best_streak, unit, "Meilleure série", "streak-figure-best")
  );
  card.appendChild(numbers);

  if (streak.current_streak > 0 && streak.current_streak === streak.best_streak) {
    const badge = document.createElement("span");
    badge.className = "record-badge";
    badge.textContent = "Record en cours";
    card.appendChild(badge);
  }

  return card;
}

function renderStreakCards() {
  const scope = document.querySelector('.segmented[data-field="streak-scope"]').dataset.value;
  const filtered =
    scope === "all" ? allStreaks : allStreaks.filter((s) => s.period_scope === scope);

  const container = document.getElementById("streak-cards");
  container.innerHTML = "";

  for (const streak of filtered) {
    container.appendChild(buildStreakCard(streak));
  }
}

setupSegmented(document.querySelector('.segmented[data-field="streak-scope"]'), renderStreakCards);

loadStreaks();

const MONTH_NAMES = [
  "Janv", "Févr", "Mars", "Avr", "Mai", "Juin",
  "Juil", "Août", "Sept", "Oct", "Nov", "Déc",
];
const DAY_ROW_LABELS = ["Lun", "", "Mer", "", "Ven", "", ""];

let currentYear = new Date().getFullYear();

function toISO(d) {
  const tz = d.getTimezoneOffset() * 60000;
  return new Date(d - tz).toISOString().slice(0, 10);
}

// Weeks start on Monday and pad both ends of the year so every week is a
// full 7-day column, like a GitHub-style contribution calendar.
function buildWeekGrid(year) {
  const jan1 = new Date(year, 0, 1);
  const gridStart = new Date(jan1);
  gridStart.setDate(gridStart.getDate() - ((jan1.getDay() + 6) % 7));

  const dec31 = new Date(year, 11, 31);
  const gridEnd = new Date(dec31);
  gridEnd.setDate(gridEnd.getDate() + (6 - ((dec31.getDay() + 6) % 7)));

  const weeks = [];
  const cursor = new Date(gridStart);
  while (cursor <= gridEnd) {
    const week = [];
    for (let i = 0; i < 7; i++) {
      week.push({
        date: toISO(cursor),
        inYear: cursor.getFullYear() === year,
        isMonthStart: cursor.getFullYear() === year && cursor.getDate() === 1,
        month: cursor.getMonth(),
      });
      cursor.setDate(cursor.getDate() + 1);
    }
    weeks.push(week);
  }
  return weeks;
}

function heatClass(day) {
  if (!day || day.habits_total === 0) return "heat-0";
  if (day.complete) return "heat-full";
  const ratio = day.habits_met / day.habits_total;
  if (ratio <= 0) return "heat-0";
  if (ratio < 0.25) return "heat-1";
  if (ratio < 0.5) return "heat-2";
  if (ratio < 0.75) return "heat-3";
  return "heat-4";
}

function renderHeatmap(data) {
  const dayByDate = {};
  for (const day of data.days) {
    dayByDate[day.date] = day;
  }

  const weeks = buildWeekGrid(data.year);

  const grid = document.getElementById("heatmap-grid");
  grid.innerHTML = "";
  grid.style.gridTemplateColumns = `auto repeat(${weeks.length}, 1fr)`;

  grid.appendChild(document.createElement("div"));
  for (const week of weeks) {
    const monthStart = week.find((cell) => cell.isMonthStart);
    const label = document.createElement("div");
    label.className = "heatmap-month-label";
    if (monthStart) {
      label.textContent = MONTH_NAMES[monthStart.month];
    }
    grid.appendChild(label);
  }

  for (let row = 0; row < 7; row++) {
    const rowLabel = document.createElement("div");
    rowLabel.className = "heatmap-row-label";
    rowLabel.textContent = DAY_ROW_LABELS[row];
    grid.appendChild(rowLabel);

    for (const week of weeks) {
      const cellInfo = week[row];
      const cell = document.createElement("div");

      if (cellInfo.inYear) {
        const day = dayByDate[cellInfo.date];
        cell.className = `heatmap-cell ${heatClass(day)}`;
        const ratio = day ? `${day.habits_met}/${day.habits_total}` : "aucune donnée";
        cell.title = `${cellInfo.date} — ${ratio}`;
      } else {
        cell.className = "heatmap-cell heatmap-cell-empty";
      }

      grid.appendChild(cell);
    }
  }
}

async function loadHeatmap() {
  document.getElementById("heatmap-year").textContent = `${currentYear}`;
  const res = await fetch(`/stats/heatmap?year=${currentYear}`);
  const data = await res.json();
  renderHeatmap(data);
}

document.getElementById("heatmap-prev").addEventListener("click", () => {
  currentYear -= 1;
  loadHeatmap();
});

document.getElementById("heatmap-next").addEventListener("click", () => {
  currentYear += 1;
  loadHeatmap();
});

loadHeatmap();
