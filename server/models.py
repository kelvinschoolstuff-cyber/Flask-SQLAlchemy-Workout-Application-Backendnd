from datetime import date

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates

db = SQLAlchemy()


class Workout(db.Model):
    __tablename__ = "workouts"
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_workout_duration_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=False, default="")

    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    exercises = db.relationship(
        "Exercise",
        secondary="workout_exercises",
        back_populates="workouts",
        viewonly=True,
    )

    @validates("date")
    def validate_date(self, _key, value):
        if not isinstance(value, date):
            raise ValueError("date must be a valid date")
        return value

    @validates("duration_minutes")
    def validate_duration(self, _key, value):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError("duration_minutes must be a positive integer")
        return value


class Exercise(db.Model):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_exercise_name_nonempty"),
        CheckConstraint(
            "length(trim(category)) > 0", name="ck_exercise_category_nonempty"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    workouts = db.relationship(
        "Workout",
        secondary="workout_exercises",
        back_populates="exercises",
        viewonly=True,
    )

    @validates("name", "category")
    def validate_text(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must not be empty")
        return value.strip()

    @validates("equipment_needed")
    def validate_equipment_needed(self, _key, value):
        if not isinstance(value, bool):
            raise ValueError("equipment_needed must be a boolean")
        return value


class WorkoutExercise(db.Model):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint("workout_id", "exercise_id", name="uq_workout_exercise"),
        CheckConstraint(
            "(reps IS NULL AND sets IS NULL) OR (reps > 0 AND sets > 0)",
            name="ck_workout_exercise_reps_sets_pair",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_workout_exercise_duration_positive",
        ),
        CheckConstraint(
            "reps IS NOT NULL OR duration_seconds IS NOT NULL",
            name="ck_workout_exercise_has_metric",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer, db.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id = db.Column(
        db.Integer, db.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    reps = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)

    workout = db.relationship("Workout", back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    @validates("reps", "sets", "duration_seconds")
    def validate_positive_metric(self, key, value):
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
        ):
            raise ValueError(f"{key} must be a positive integer")
        return value