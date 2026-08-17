import numpy as np
import pandas as pd

# Every feature the model sees. Kept as an explicit list (not "all columns")
# so training and inference are guaranteed to use the exact same inputs in
# the exact same order.
FEATURE_COLUMNS = [
    "ret_1", "ret_3", "ret_6", "ret_12",
    "sma_10_ratio", "sma_30_ratio",
    "rsi_14", "volatility_12", "volume_zscore_20", "bb_width_20",
]


def klines_to_df(raw_klines: list) -> pd.DataFrame:
    """raw_klines is Binance's raw kline array format (see
    market.binance_public.klines): [open_time, open, high, low, close,
    volume, close_time, quote_volume, trades, taker_base, taker_quote,
    ignore]."""
    cols = ["open_time", "open", "high", "low", "close", "volume", "close_time",
            "quote_volume", "trades", "taker_base", "taker_quote", "ignore"]
    df = pd.DataFrame(raw_klines, columns=cols)
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = df[c].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Plain, well-understood technical indicators — nothing exotic, so the
    model's inputs are auditable. All are computed from price/volume alone;
    none use future data (every window only looks backward), which matters
    for avoiding leakage when this is used for training."""
    close = df["close"]
    out = pd.DataFrame(index=df.index)

    out["ret_1"] = close.pct_change(1)
    out["ret_3"] = close.pct_change(3)
    out["ret_6"] = close.pct_change(6)
    out["ret_12"] = close.pct_change(12)

    sma10 = close.rolling(10).mean()
    sma30 = close.rolling(30).mean()
    out["sma_10_ratio"] = close / sma10 - 1
    out["sma_30_ratio"] = close / sma30 - 1

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi_14"] = 100 - (100 / (1 + rs))

    out["volatility_12"] = close.pct_change().rolling(12).std()

    vol = df["volume"]
    vol_mean = vol.rolling(20).mean()
    vol_std = vol.rolling(20).std()
    out["volume_zscore_20"] = (vol - vol_mean) / vol_std.replace(0, np.nan)

    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    out["bb_width_20"] = (4 * bb_std) / bb_mid

    return out


def build_labeled_dataset(df: pd.DataFrame, horizon: int = 4, threshold_pct: float = 0.0) -> pd.DataFrame:
    """Label = 1 (UP) if price is more than threshold_pct higher `horizon`
    candles later, else 0 (DOWN/flat). Rows near the end (no future data
    yet) and near the start (indicators not warmed up) are dropped."""
    features = compute_features(df)
    future_close = df["close"].shift(-horizon)
    fwd_return = (future_close - df["close"]) / df["close"] * 100
    data = features.copy()
    data["fwd_return_pct"] = fwd_return
    data["label"] = (fwd_return > threshold_pct).astype("Int64")
    data = data.dropna()
    return data
