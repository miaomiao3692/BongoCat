from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.preprocess import PreparedData


@dataclass
class ChangeResult:
    change_metric: np.ndarray
    binary_mask: np.ndarray
    changed_area_m2: float
    total_area_m2: float
    changed_ratio: float


def _safe_ndvi(arr: np.ndarray, red_idx: int = 2, nir_idx: int = 3) -> np.ndarray:
    """计算NDVI，默认使用第3波段红光和第4波段近红外（1基索引）。"""
    red = arr[red_idx]
    nir = arr[nir_idx]
    den = nir + red
    den[den == 0] = np.nan
    return (nir - red) / den


def suggest_default_threshold(change_source: str) -> float:
    """给新手一个稳定、可解释的默认阈值。"""
    if change_source == "NDVI差分":
        return 0.15
    return 0.20


def compute_change_products(prep: PreparedData, threshold: float) -> ChangeResult:
    """根据策略计算变化指标、二值掩膜和面积统计。"""
    valid = prep.valid_mask

    if prep.change_source == "NDVI差分":
        ndvi1 = _safe_ndvi(prep.arr_t1)
        ndvi2 = _safe_ndvi(prep.arr_t2)
        metric = np.abs(ndvi2 - ndvi1)
    else:
        # 退化方案：前三个波段做归一化差分强度
        b = min(3, prep.arr_t1.shape[0], prep.arr_t2.shape[0])
        diff = np.abs(prep.arr_t2[:b] - prep.arr_t1[:b])
        metric = np.nanmean(diff, axis=0)
        p98 = np.nanpercentile(metric[valid], 98)
        if p98 > 0:
            metric = metric / p98
        metric = np.clip(metric, 0, 1)

    metric[~valid] = np.nan
    binary = (metric >= threshold) & valid

    changed_area_m2 = float(binary.sum() * prep.pixel_area_m2)
    total_area_m2 = float(valid.sum() * prep.pixel_area_m2)
    changed_ratio = changed_area_m2 / total_area_m2 if total_area_m2 > 0 else 0.0

    return ChangeResult(
        change_metric=metric,
        binary_mask=binary.astype(np.uint8),
        changed_area_m2=changed_area_m2,
        total_area_m2=total_area_m2,
        changed_ratio=changed_ratio,
    )
