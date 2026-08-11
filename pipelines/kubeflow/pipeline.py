from kfp import dsl

@dsl.component(base_image="python:3.11-slim")
def validate_data(dataset_uri: str) -> str:
    print(f"validate {dataset_uri}")
    return dataset_uri

@dsl.component(base_image="python:3.11-slim")
def train_model(dataset_uri: str) -> str:
    print(f"train with {dataset_uri}")
    return "models:/edurec-two-tower@candidate"

@dsl.component(base_image="python:3.11-slim")
def evaluate_and_gate(model_uri: str, min_recall_at_50: float = 0.35) -> str:
    print(model_uri, min_recall_at_50)
    return "approved"

@dsl.pipeline(name="edurec-training", description="Validate → train → evaluate → register")
def edurec_pipeline(dataset_uri: str = "s3://edurec/features/latest.parquet"):
    validated = validate_data(dataset_uri=dataset_uri)
    trained = train_model(dataset_uri=validated.output)
    evaluate_and_gate(model_uri=trained.output)
