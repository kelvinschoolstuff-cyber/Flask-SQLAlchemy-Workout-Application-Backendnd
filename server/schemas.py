from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class ExerciseBriefSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)
    category = fields.String(dump_only=True)
    equipment_needed = fields.Boolean(dump_only=True)


class WorkoutExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    workout_id = fields.Integer(dump_only=True)
    exercise_id = fields.Integer(dump_only=True)
    reps = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    sets = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    duration_seconds = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    exercise = fields.Nested(ExerciseBriefSchema, dump_only=True)

    @validates_schema
    def validate_metrics(self, data, **_kwargs):
        has_reps = data.get("reps") is not None
        has_sets = data.get("sets") is not None
        has_duration = data.get("duration_seconds") is not None
        if has_reps != has_sets:
            raise ValidationError("reps and sets must be provided together")
        if not has_reps and not has_duration:
            raise ValidationError("provide reps and sets, duration_seconds, or both")


class WorkoutSchema(Schema):
    id = fields.Integer(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Integer(
        required=True, validate=validate.Range(min=1)
    )
    notes = fields.String(load_default="")
    workout_exercises = fields.Nested(WorkoutExerciseSchema, many=True, dump_only=True)


class ExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True, validate=validate.Length(min=1, max=120, error="name is required")
    )
    category = fields.String(
        required=True,
        validate=validate.Length(min=1, max=80, error="category is required"),
    )
    equipment_needed = fields.Boolean(load_default=False)

    @validates_schema
    def validate_nonblank_strings(self, data, **_kwargs):
        errors = {}
        for field_name in ("name", "category"):
            value = data.get(field_name)
            if value is not None and not value.strip():
                errors[field_name] = [f"{field_name} must not be blank"]
        if errors:
            raise ValidationError(errors)