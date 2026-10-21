from datetime import date

import pytest

from server.app import create_app
from server.models import Exercise, Workout, WorkoutExercise, db


@pytest.fixture
def client(tmp_path):
    database = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}",
        }
    )
    with app.app_context():
        db.create_all()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def create_records(client):
    workout_response = client.post(
        "/workouts",
        json={"date": date.today().isoformat(), "duration_minutes": 45},
    )
    exercise_response = client.post(
        "/exercises",
        json={"name": "Deadlift", "category": "Strength", "equipment_needed": True},
    )
    return workout_response.json["id"], exercise_response.json["id"]


def test_create_list_and_get_workouts(client):
    workout_id, _exercise_id = create_records(client)

    assert client.get("/workouts").status_code == 200
    response = client.get(f"/workouts/{workout_id}")
    assert response.status_code == 200
    assert response.json["duration_minutes"] == 45


def test_schema_and_model_validations_reject_bad_values(client):
    bad_workout = client.post(
        "/workouts", json={"date": date.today().isoformat(), "duration_minutes": 0}
    )
    bad_exercise = client.post(
        "/exercises", json={"name": "  ", "category": "Strength"}
    )

    assert bad_workout.status_code == 400
    assert bad_exercise.status_code == 400


def test_model_validators_reject_invalid_values(client):
    with client.application.app_context():
        with pytest.raises(ValueError):
            Exercise(name=" ", category="Core")
        with pytest.raises(ValueError):
            Workout(date=date.today(), duration_minutes=0)


def test_association_metrics_and_duplicate_constraint(client):
    workout_id, exercise_id = create_records(client)
    endpoint = (
        f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises"
    )
    response = client.post(endpoint, json={"reps": 8, "sets": 3})
    duplicate = client.post(endpoint, json={"reps": 8, "sets": 3})
    invalid = client.post(endpoint, json={"duration_seconds": 0})

    assert response.status_code == 201
    assert response.json["reps"] == 8
    assert duplicate.status_code == 409
    assert invalid.status_code == 400


def test_deleting_parent_cascades_associations(client):
    workout_id, exercise_id = create_records(client)
    client.post(
        f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises",
        json={"duration_seconds": 30},
    )

    assert client.delete(f"/workouts/{workout_id}").status_code == 204
    with client.application.app_context():
        assert WorkoutExercise.query.count() == 0
        assert Exercise.query.count() == 1
        assert Workout.query.count() == 0


def test_exercise_endpoints_and_delete_cascade(client):
    workout_id, exercise_id = create_records(client)
    client.post(
        f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises",
        json={"duration_seconds": 30},
    )

    assert len(client.get("/exercises").json) == 1
    assert client.get(f"/exercises/{exercise_id}").json["name"] == "Deadlift"
    assert client.delete(f"/exercises/{exercise_id}").status_code == 204
    with client.application.app_context():
        assert WorkoutExercise.query.count() == 0
        assert Workout.query.count() == 1
        assert Exercise.query.count() == 0