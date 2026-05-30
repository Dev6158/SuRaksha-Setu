import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

DATASET_PATH = "synthetic_behavior_data.csv"
MODEL_PATH = "behavior_model.joblib"


def load_dataset():

    df = pd.read_csv(DATASET_PATH)

    return df


def prepare_features(df):

    feature_columns = [
        "swipe_velocity",
        "tap_force",
        "gyro_x",
        "gyro_y",
        "gyro_z"
    ]

    X = df[feature_columns]

    return X


def build_pipeline():

    pipeline = Pipeline(
        [
            (
                "scaler",
                StandardScaler()
            ),
            (
                "detector",
                IsolationForest(
                    n_estimators=200,
                    contamination=0.05,
                    random_state=42
                )
            )
        ]
    )

    return pipeline


def train_model():

    df = load_dataset()

    X = prepare_features(df)

    pipeline = build_pipeline()

    pipeline.fit(X)

    return pipeline


def evaluate_model(
    model,
    X
):

    predictions = model.predict(X)

    anomalies = (predictions == -1).sum()

    print(
        f"Detected anomalies: {anomalies}"
    )

    return anomalies


def persist_model(model):

    joblib.dump(
        model,
        MODEL_PATH
    )

    print(
        f"Model saved to {MODEL_PATH}"
    )


def main():

    df = load_dataset()

    X = prepare_features(df)

    model = train_model()

    evaluate_model(
        model,
        X
    )

    persist_model(
        model
    )


if __name__ == "__main__":
    main()