from datetime import timedelta
from feast import Entity, FeatureService, FeatureView, Field, FileSource
from feast.types import Float32, Int64, String

user = Entity(name="user", join_keys=["user_id"])
course = Entity(name="course", join_keys=["course_id"])
user_source = FileSource(path="data/user_features.parquet", timestamp_field="event_timestamp")
course_source = FileSource(path="data/course_features.parquet", timestamp_field="event_timestamp")

user_features = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=7),
    schema=[Field(name="views_7d", dtype=Int64), Field(name="enrollments_30d", dtype=Int64), Field(name="preferred_category", dtype=String)],
    source=user_source,
    online=True,
)
course_features = FeatureView(
    name="course_features",
    entities=[course],
    ttl=timedelta(days=1),
    schema=[Field(name="popularity_7d", dtype=Int64), Field(name="completion_rate", dtype=Float32)],
    source=course_source,
    online=True,
)
recommendation_features_v1 = FeatureService(name="recommendation_features_v1", features=[user_features, course_features])
