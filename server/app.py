import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from .models import Exercise, Workout, WorkoutExercise, db
from .schemas import ExerciseSchema, WorkoutExerciseSchema, WorkoutSchema

migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__)
    default_database = Path(__file__).resolve().parent.parent / "app.db"
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", f"sqlite:///{default_database}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        with app.app_context():
            @event.listens_for(db.engine, "connect")
            def enable_sqlite_foreign_keys(connection, _record):
                cursor = connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    workout_schema = WorkoutSchema()
    workouts_schema = WorkoutSchema(many=True)
    exercise_schema = ExerciseSchema()
    exercises_schema = ExerciseSchema(many=True)
    workout_exercise_schema = WorkoutExerciseSchema()

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({"errors": error.messages}), 400

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(_error):
        db.session.rollback()
        return jsonify({"error": "Request conflicts with existing data"}), 409

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        db.session.rollback()
        return jsonify({"error": str(error)}), 400

    @app.get("/workouts")
    def list_workouts():
        return jsonify(workouts_schema.dump(Workout.query.order_by(Workout.id).all()))

    @app.get("/workouts/<int:workout_id>")
    def get_workout(workout_id):
        workout = db.session.get(Workout, workout_id)
        if workout is None:
            return jsonify({"error": "Workout not found"}), 404
        return jsonify(workout_schema.dump(workout))

    @app.post("/workouts")
    def create_workout():
        workout = Workout(**workout_schema.load(request.get_json() or {}))
        db.session.add(workout)
        db.session.commit()
        return jsonify(workout_schema.dump(workout)), 201

    @app.delete("/workouts/<int:workout_id>")
    def delete_workout(workout_id):
        workout = db.session.get(Workout, workout_id)
        if workout is None:
            return jsonify({"error": "Workout not found"}), 404
        db.session.delete(workout)
        db.session.commit()
        return "", 204

    @app.get("/exercises")
    def list_exercises():
        return jsonify(exercises_schema.dump(Exercise.query.order_by(Exercise.id).all()))

    @app.get("/exercises/<int:exercise_id>")
    def get_exercise(exercise_id):
        exercise = db.session.get(Exercise, exercise_id)
        if exercise is None:
            return jsonify({"error": "Exercise not found"}), 404
        return jsonify(exercise_schema.dump(exercise))

    @app.post("/exercises")
    def create_exercise():
        exercise = Exercise(**exercise_schema.load(request.get_json() or {}))
        db.session.add(exercise)
        db.session.commit()
        return jsonify(exercise_schema.dump(exercise)), 201

    @app.delete("/exercises/<int:exercise_id>")
    def delete_exercise(exercise_id):
        exercise = db.session.get(Exercise, exercise_id)
        if exercise is None:
            return jsonify({"error": "Exercise not found"}), 404
        db.session.delete(exercise)
        db.session.commit()
        return "", 204

    @app.post(
        "/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises"
    )
    def add_exercise_to_workout(workout_id, exercise_id):
        workout = db.session.get(Workout, workout_id)
        exercise = db.session.get(Exercise, exercise_id)
        if workout is None:
            return jsonify({"error": "Workout not found"}), 404
        if exercise is None:
            return jsonify({"error": "Exercise not found"}), 404

        association = WorkoutExercise(
            **workout_exercise_schema.load(request.get_json() or {}),
            workout=workout,
            exercise=exercise,
        )
        db.session.add(association)
        db.session.commit()
        return jsonify(workout_exercise_schema.dump(association)), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)