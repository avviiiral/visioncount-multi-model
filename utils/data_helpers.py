"""
utils/data_helpers.py
Pandas helpers for reading and slicing counts.csv.
"""
import os
import pandas as pd
from config import CSV_PATH


def load_df() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=["cam_name", "count", "date", "time_hour", "min", "sec"])
    df = pd.read_csv(CSV_PATH, dtype=str)
    for col in ["count", "time_hour", "min", "sec"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"])


def daily_totals(df: pd.DataFrame, date) -> pd.DataFrame:
    day = pd.Timestamp(date).normalize()
    sub = df[df["date"].dt.normalize() == day]
    return sub.groupby("cam_name")["count"].sum().reset_index().rename(columns={"count": "total"})


def hourly_counts(df: pd.DataFrame, date, cam_name: str = None) -> pd.DataFrame:
    day = pd.Timestamp(date).normalize()
    sub = df[df["date"].dt.normalize() == day]
    if cam_name:
        sub = sub[sub["cam_name"] == cam_name]
    return sub.groupby("time_hour")["count"].sum().reset_index()


def monthly_totals(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    sub = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]
    result = sub.groupby(df["date"].dt.day)["count"].sum().reset_index()
    result.columns = ["day", "total"]
    return result


def camera_daily_series(df: pd.DataFrame, cam_name: str) -> pd.DataFrame:
    sub = df[df["cam_name"] == cam_name].copy()
    sub["day"] = sub["date"].dt.normalize()
    return sub.groupby("day")["count"].sum().reset_index()
