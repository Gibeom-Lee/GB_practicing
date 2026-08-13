import os
from itertools import cycle

import matplotlib.pyplot as plt
import pandas as pd


PLOT_COLORS = [
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#ff7f0e",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def load_multichannel_csv(file_path, *, header=None, skiprows=0, current_scale=None):
    df = pd.read_csv(file_path, header=header, skiprows=skiprows)
    df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")

    if df.shape[1] < 2:
        raise ValueError("At least 2 columns are required: Time + 1 channel.")

    df.columns = ["Time"] + [f"Ch{i}" for i in range(1, df.shape[1])]
    df = df.dropna(subset=["Time"]).reset_index(drop=True)

    if current_scale is not None:
        signal_cols = list(df.columns[1:])
        df.loc[:, signal_cols] = df.loc[:, signal_cols] * float(current_scale)

    return df


def filter_time_range(df, time_range, *, shift_to_zero=False):
    if time_range is None:
        return df.copy()

    if len(time_range) != 2:
        raise ValueError("time_range must be None or a tuple like (start, end).")

    start, end = map(float, time_range)
    filtered = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()

    if filtered.empty:
        raise ValueError(f"No data found in time range {time_range}.")

    filtered.reset_index(drop=True, inplace=True)

    if shift_to_zero:
        filtered.loc[:, "Time"] = filtered["Time"] - float(filtered.loc[0, "Time"])

    return filtered


def save_cut_csv(df, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False, header=False, encoding="utf-8-sig")


def plot_multichannel_overview(
    df,
    *,
    title,
    ylabel,
    figsize=(10, 5),
    y_range=None,
    legend=True,
):
    plt.figure(figsize=figsize)
    color_iter = cycle(PLOT_COLORS)

    for channel in df.columns[1:]:
        plt.plot(df["Time"], df[channel], label=channel, color=next(color_iter), linewidth=1.0)

    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    plt.title(title)

    if y_range is not None:
        plt.ylim(y_range)

    plt.grid(True)

    if legend:
        plt.legend()

    plt.tight_layout()
    plt.show()
