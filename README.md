# Workout Tracking API

A Flask REST API for managing workouts, reusable exercises, and the metrics attached to an exercise within a workout. SQLAlchemy relationships and database constraints protect the relational data, while Marshmallow schemas validate API input and serialize responses.

## Setup

Install Pipenv and Python 3.8 or newer, then install project dependencies:

```bash
pipenv install --dev
```

Apply the included database migration, then load the repeatable sample dataset:

```bash
pipenv run flask --app server.app db upgrade
pipenv run python -m server.seed
```

After changing models, create and apply a migration with `pipenv run flask --app server.app db migrate -m "Describe the change"` followed by `pipenv run flask --app server.app db upgrade`.

The default SQLite database is `app.db` in the project root. Set `DATABASE_URL` to use a different database.

## Run

```bash
pipenv run flask --app server.app run --port 5555
```

Run tests with `pipenv run pytest`.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/workouts` | List workouts with attached exercise metrics. |
| GET | `/workouts/<id>` | Get one workout and its attached exercises. |
| POST | `/workouts` | Create a workout with `date` (ISO format), `duration_minutes`, and optional `notes`. |
| DELETE | `/workouts/<id>` | Delete a workout and its workout-exercise records. |
| GET | `/exercises` | List reusable exercises. |
| GET | `/exercises/<id>` | Get one exercise. |
| POST | `/exercises` | Create an exercise with `name`, `category`, and optional `equipment_needed`. |
| DELETE | `/exercises/<id>` | Delete an exercise and its workout-exercise records. |
| POST | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Attach an exercise using `reps` and `sets`, `duration_seconds`, or both. |

Creation endpoints return `201`, successful deletions return `204`, invalid input returns `400`, missing records return `404`, and database conflicts (such as attaching the same exercise twice to one workout) return `409`.