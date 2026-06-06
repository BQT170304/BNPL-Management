"""Train a Logistic Regression PD (Probability of Default) model on the
Taiwan Credit Card Default dataset (UCI, 30K samples, real default labels).

Features derived from data, no hand-crafted weights:
  - util_ratio    : BILL_AMT1 / (LIMIT_BAL + 1)          — credit utilisation
  - max_dpd       : max repayment-delay across 6 months   — worst DPD ever
  - avg_dpd       : mean repayment-delay across 6 months  — average behaviour
  - pay_coverage  : PAY_AMT1 / (|BILL_AMT1| + 1), capped — payment coverage ratio
  - log_limit     : log1p(LIMIT_BAL)                      — creditworthiness proxy

Output: models/pd_model.pkl — dict with keys "pipeline" and "features".
The pipeline is sklearn Pipeline(StandardScaler → LogisticRegression).
"""
from __future__ import annotations

import argparse
import pathlib
import pickle

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

TARGET = "default payment next month"
PAY_COLS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
FEATURES = ["util_ratio", "max_dpd", "avg_dpd", "pay_coverage", "log_limit"]


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["util_ratio"] = df["BILL_AMT1"] / (df["LIMIT_BAL"].abs() + 1)
    df["max_dpd"] = df[PAY_COLS].max(axis=1)
    df["avg_dpd"] = df[PAY_COLS].mean(axis=1)
    df["pay_coverage"] = (df["PAY_AMT1"] / (df["BILL_AMT1"].abs() + 1)).clip(0, 3)
    df["log_limit"] = np.log1p(df["LIMIT_BAL"])
    return df


def main(xlsx_path: str, output_path: str, c: float) -> None:
    print(f"Loading {xlsx_path} …")
    raw = pd.read_excel(xlsx_path, header=1)
    print(f"  rows={len(raw)}  default_rate={raw[TARGET].mean():.3f}")

    df = engineer(raw)
    X = df[FEATURES].values.astype(float)
    y = raw[TARGET].values

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(C=c, max_iter=2000, solver="lbfgs",
                                  class_weight="balanced", random_state=42)),
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    auc_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
    print(f"CV AUC: {auc_scores.mean():.4f} ± {auc_scores.std():.4f}")

    pipeline.fit(X, y)
    lr = pipeline.named_steps["lr"]
    print("\nLearned coefficients (β from data, not hand-crafted):")
    for feat, coef in zip(FEATURES, lr.coef_[0]):
        print(f"  {feat:20s}  β={coef:+.4f}")
    print(f"  intercept             β₀={lr.intercept_[0]:+.4f}")

    y_pred_prob = pipeline.predict_proba(X)[:, 1]
    print(f"\nTrain AUC: {roc_auc_score(y, y_pred_prob):.4f}")
    print(classification_report(y, pipeline.predict(X), target_names=["no default", "default"]))

    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump({"pipeline": pipeline, "features": FEATURES}, f)
    print(f"\nSaved PD model → {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PD Logistic Regression on Taiwan dataset")
    parser.add_argument("--data", default="data/default of credit card clients.xls",
                        help="Path to UCI Taiwan Credit Card Default xlsx")
    parser.add_argument("--output", default="models/pd_model.pkl")
    parser.add_argument("--C", dest="c", type=float, default=1.0,
                        help="Inverse regularisation strength (sklearn LogisticRegression)")
    args = parser.parse_args()
    main(args.data, args.output, args.c)
