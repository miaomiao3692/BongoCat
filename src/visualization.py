from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def _stretch(arr: np.ndarray) -> np.ndarray:
    p2, p98 = np.nanpercentile(arr, [2, 98])
    if p98 <= p2:
        return np.zeros_like(arr)
    out = (arr - p2) / (p98 - p2)
    return np.clip(out, 0, 1)


def plot_rgb_preview(arr: np.ndarray, title: str):
    """绘制影像预览图：优先RGB，否则灰度。"""
    fig, ax = plt.subplots(figsize=(5, 4))
    if arr.shape[0] >= 3:
        rgb = np.dstack([_stretch(arr[2]), _stretch(arr[1]), _stretch(arr[0])])
        ax.imshow(rgb)
    else:
        ax.imshow(_stretch(arr[0]), cmap="gray")
    ax.set_title(title)
    ax.axis("off")
    return fig


def plot_change_map(metric: np.ndarray, source_name: str):
    """绘制变化指标图。"""
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(metric, cmap="RdYlGn_r")
    ax.set_title(f"{source_name} 图")
    ax.axis("off")
    plt.colorbar(im, ax=ax, fraction=0.045, pad=0.04)
    return fig


def plot_binary_mask(binary_mask: np.ndarray):
    """绘制二值变化掩膜图。"""
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(binary_mask, cmap="gray")
    ax.set_title("二值变化掩膜（白=变化）")
    ax.axis("off")
    return fig
