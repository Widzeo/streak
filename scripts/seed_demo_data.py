"""Seed the database with ~6 months of realistic demo data, gaps included.

WARNING: this truncates habit/completion/neutralized_day/category first.
Do not run against a database you want to keep.

Usage: python -m scripts.seed_demo_data
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.completions.models import Completion
from app.core.database import SessionLocal
from app.habits.enums import Direction, HabitKind, PeriodScope
from app.habits.models import Category, Habit
from app.stats.models import NeutralizedDay

random.seed(42)

TODAY = date.today()
SIX_MONTHS_AGO = TODAY - timedelta(days=182)


def truncate(session: Session) -> None:
    session.execute(
        text(
            "TRUNCATE TABLE completion, neutralized_day, category, habit "
            "RESTART IDENTITY CASCADE"
        )
    )
    session.commit()


def seed_categories(session: Session) -> tuple[Category, Category]:
    health = Category(name="Santé")
    finance = Category(name="Finances")
    session.add_all([health, finance])
    session.commit()
    return health, finance


def seed_habits(session: Session, health: Category, finance: Category) -> list[Habit]:
    habits = [
        Habit(
            name="Boire 2L d'eau",
            kind=HabitKind.QUANTIFIED,
            unit="L",
            period_scope=PeriodScope.DAY,
            cadence=1,
            target=Decimal("2"),
            direction=Direction.AT_LEAST,
            is_essential=True,
            category_id=health.id,
            active_from=SIX_MONTHS_AGO,
        ),
        Habit(
            name="Sport",
            kind=HabitKind.BINARY,
            period_scope=PeriodScope.WEEK,
            cadence=3,
            target=Decimal(1),
            direction=Direction.AT_LEAST,
            is_essential=True,
            category_id=health.id,
            active_from=SIX_MONTHS_AGO,
        ),
        Habit(
            name="Lecture",
            kind=HabitKind.QUANTIFIED,
            unit="min",
            period_scope=PeriodScope.DAY,
            cadence=1,
            target=Decimal("30"),
            direction=Direction.AT_LEAST,
            is_essential=False,
            category_id=None,
            active_from=SIX_MONTHS_AGO,
        ),
        Habit(
            name="Méditation",
            kind=HabitKind.BINARY,
            period_scope=PeriodScope.DAY,
            cadence=1,
            target=Decimal(1),
            direction=Direction.AT_LEAST,
            is_essential=False,
            category_id=None,
            # started 6 weeks ago, not from day one - demonstrates a habit
            # added mid-route rather than every habit starting together
            active_from=TODAY - timedelta(days=42),
        ),
        Habit(
            name="Budget restaurant",
            kind=HabitKind.QUANTIFIED,
            unit="€",
            period_scope=PeriodScope.MONTH,
            cadence=1,
            target=Decimal("100"),
            direction=Direction.AT_MOST,
            is_essential=False,
            category_id=finance.id,
            active_from=SIX_MONTHS_AGO,
        ),
    ]
    session.add_all(habits)
    session.commit()
    return habits


def seed_daily_completions(session: Session, habits: list[Habit]) -> None:
    water, _sport, reading, meditation, _budget = habits
    completions = []

    for habit, probability, value_range in [
        (water, 0.8, (Decimal("1.5"), Decimal("3"))),
        (reading, 0.6, (Decimal("10"), Decimal("50"))),
        (meditation, 0.7, (Decimal(1), Decimal(1))),
    ]:
        day = habit.active_from
        while day < TODAY:
            if random.random() < probability:
                low, high = value_range
                value = low + (high - low) * Decimal(str(round(random.random(), 2)))
                completions.append(
                    Completion(habit_id=habit.id, logical_date=day, value=value)
                )
            day += timedelta(days=1)

    session.add_all(completions)
    session.commit()


def seed_sport_completions(session: Session, sport: Habit) -> None:
    completions = []
    day = sport.active_from - timedelta(days=sport.active_from.weekday())  # Monday on/before start

    while day < TODAY:
        sessions_this_week = random.choice([0, 2, 2, 3, 3, 4])
        chosen_offsets = random.sample(range(7), k=min(sessions_this_week, 7))
        for offset in chosen_offsets:
            session_day = day + timedelta(days=offset)
            if sport.active_from <= session_day < TODAY:
                completions.append(
                    Completion(habit_id=sport.id, logical_date=session_day, value=Decimal(1))
                )
        day += timedelta(days=7)

    session.add_all(completions)
    session.commit()


def seed_budget_completions(session: Session, budget: Habit) -> None:
    # one lump-sum entry at month-end, matching how this habit is meant to
    # be used in practice: log the total once you know it, not day by day
    completions = []
    day = budget.active_from.replace(day=1)

    while day < TODAY:
        next_month = (day.replace(day=28) + timedelta(days=4)).replace(day=1)
        last_day_of_month = next_month - timedelta(days=1)
        if budget.active_from <= last_day_of_month < TODAY:
            spend = Decimal(random.randint(60, 220))  # sometimes over the 100 cap, on purpose
            completions.append(
                Completion(habit_id=budget.id, logical_date=last_day_of_month, value=spend)
            )
        day = next_month

    session.add_all(completions)
    session.commit()


def seed_neutralized_days(session: Session) -> None:
    neutralized = [
        NeutralizedDay(logical_date=TODAY - timedelta(days=100), reason="Malade"),
        NeutralizedDay(logical_date=TODAY - timedelta(days=60), reason="Voyage"),
        NeutralizedDay(logical_date=TODAY - timedelta(days=59), reason="Voyage"),
    ]
    session.add_all(neutralized)
    session.commit()


def main() -> None:
    with SessionLocal() as session:
        truncate(session)
        health, finance = seed_categories(session)
        habits = seed_habits(session, health, finance)
        seed_daily_completions(session, habits)
        seed_sport_completions(session, habits[1])
        seed_budget_completions(session, habits[4])
        seed_neutralized_days(session)

    print("Demo data seeded: 5 habits, 2 categories, ~6 months of completions with gaps.")


if __name__ == "__main__":
    main()
