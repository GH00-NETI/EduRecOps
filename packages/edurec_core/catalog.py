from .domain import Course

CATALOG: tuple[Course, ...] = (
    Course("c-101", "Python Foundations", "programming", 1, ("python",), quality_score=0.88, popularity_score=0.94),
    Course("c-102", "SQL for Data Analysis", "data", 1, ("sql",), quality_score=0.91, popularity_score=0.86),
    Course("c-103", "Applied Machine Learning", "ai", 2, ("ml",), (("python", 0.55),), 0.84, 0.81),
    Course("c-104", "Docker for Data Engineers", "devops", 2, ("docker",), (("linux", 0.40),), 0.82, 0.70),
    Course("c-105", "Data Systems Design", "data", 3, ("data-modeling", "distributed-systems"), (("sql", 0.60),), 0.89, 0.61),
    Course("c-106", "MLOps: From Model to Production", "ai", 3, ("mlops",), (("ml", 0.55), ("docker", 0.50)), 0.86, 0.78),
    Course("c-107", "Kafka and Stream Processing", "data", 3, ("streaming",), (("python", 0.50),), 0.85, 0.65),
    Course("c-108", "Production FastAPI", "programming", 2, ("api",), (("python", 0.60),), 0.90, 0.72),
    Course("c-109", "Practical Linux", "devops", 1, ("linux",), quality_score=0.83, popularity_score=0.68),
    Course("c-110", "Probability for Machine Learning", "ai", 2, ("probability",), quality_score=0.87, popularity_score=0.58),
    Course("c-111", "Feature Stores with Feast", "mlops", 3, ("feature-store",), (("python", 0.55), ("ml", 0.50)), 0.85, 0.55),
    Course("c-112", "System Observability with Prometheus", "devops", 2, ("observability",), (("linux", 0.40),), 0.88, 0.60),
)
