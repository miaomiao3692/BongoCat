from __future__ import annotations

from pathlib import Path

import pandas as pd
import rasterio
from rasterio.transform import Affine


def export_png_figure(fig, out_path: Path) -> None:
    """导出matplotlib图为PNG。"""
    fig.savefig(out_path, dpi=180, bbox_inches="tight")


def make_stats_csv_bytes(df: pd.DataFrame) -> bytes:
    """将统计表转为UTF-8带BOM，兼容Windows Excel。"""
    return df.to_csv(index=False).encode("utf-8-sig")


def export_change_mask_geotiff(
    out_path: Path,
    mask,
    transform: Affine,
    crs,
    nodata: int = 0,
) -> None:
    """导出变化掩膜为GeoTIFF。"""
    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=mask.shape[0],
        width=mask.shape[1],
        count=1,
        dtype="uint8",
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress="lzw",
    ) as dst:
        dst.write(mask.astype("uint8"), 1)
