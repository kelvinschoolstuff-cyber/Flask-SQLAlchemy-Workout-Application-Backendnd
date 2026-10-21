#!/usr/bin/env python3
from datetime import date

from .app import app
from .models import Exercise, Workout, WorkoutExercise, db


def seed():
    with app.app_context():
        WorkoutExercise.query.delete()
        Workout.query.delete()
        Exercise.query.delete()

        squat = Exercise(
            name="Goblet squat", category="Strength", equipment_needed=True
        )
        plank = Exercise(name="Plank", category="Core", equipment_needed=False)
        workout = Workout(
            date=date.today(), duration_minutes=35, notes="Full-body session"
        )
        db.session.add_all([squat, plank, workout])
        db.session.flush()
        db.session.add_all(
            [
                WorkoutExercise(
                    workout=workout, exercise=squat, reps=10, sets=3
                ),
                WorkoutExercise(
                    workout=workout, exercise=plank, duration_seconds=45
                ),
            ]
        )
        db.session.commit()


if __name__ == "__main__":
    seed()