from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from rasterio.warp import transform_geom

from src.data_utils import AnalysisError


@dataclass
class PreparedData:
    arr_t1: np.ndarray
    arr_t2: np.ndarray
    transform: rasterio.Affine
    crs: rasterio.crs.CRS
    nodata: float
    pixel_area_m2: float
    valid_mask: np.ndarray
    change_source: str


def _reproject_geom(geom: BaseGeometry, src_crs, dst_crs) -> BaseGeometry:
    if src_crs == dst_crs:
        return geom
    g = transform_geom(src_crs, dst_crs, geom.__geo_interface__)
    from shapely.geometry import shape
    return shape(g)


def _choose_overlap_geom(ds1, ds2) -> BaseGeometry:
    """计算两期影像在目标坐标系下的重叠区域。"""
    b1 = box(*ds1.bounds)
    b2 = box(*ds2.bounds)
    if ds1.crs != ds2.crs:
        b2 = _reproject_geom(b2, ds2.crs, ds1.crs)
    inter = b1.intersection(b2)
    if inter.is_empty:
        raise AnalysisError("两期影像没有重叠区域，无法分析。")
    if inter.area < b1.area * 0.01:
        raise AnalysisError("两期影像重叠范围过小（小于1%），请更换数据。")
    return inter


def _align_to_reference(ds_ref, ds_target) -> np.ndarray:
    """将目标影像按参考影像网格重采样对齐。"""
    out = np.zeros((ds_target.count, ds_ref.height, ds_ref.width), dtype=np.float32)
    for i in range(1, ds_target.count + 1):
        reproject(
            source=rasterio.band(ds_target, i),
            destination=out[i - 1],
            src_transform=ds_target.transform,
            src_crs=ds_target.crs,
            dst_transform=ds_ref.transform,
            dst_crs=ds_ref.crs,
            resampling=Resampling.bilinear,
        )
    return out


def align_and_prepare_datasets(ds1, ds2, aoi_geom: Optional[BaseGeometry]) -> PreparedData:
    """完成投影统一、分辨率统一、掩膜裁剪，并判断变化检测策略。"""
    overlap_geom = _choose_overlap_geom(ds1, ds2)
    if aoi_geom is not None:
        # 这里假设用户上传边界默认与第一期坐标一致；若不同可在实际项目中扩展CRS读取。
        overlap_geom = overlap_geom.intersection(aoi_geom)
        if overlap_geom.is_empty:
            raise AnalysisError("研究区边界与影像无交集，请检查数据范围。")

    arr1 = ds1.read().astype(np.float32)
    arr2 = _align_to_reference(ds1, ds2)

    geo_mask = geometry_mask(
        [overlap_geom],
        transform=ds1.transform,
        invert=True,
        out_shape=(ds1.height, ds1.width),
    )

    # 基础nodata处理
    nodata1 = ds1.nodata if ds1.nodata is not None else np.nan
    nodata2 = ds2.nodata if ds2.nodata is not None else np.nan

    valid_mask = geo_mask.copy()
    if not np.isnan(nodata1):
        valid_mask &= arr1[0] != nodata1
    if not np.isnan(nodata2):
        valid_mask &= arr2[0] != nodata2

    if valid_mask.sum() < 100:
        raise AnalysisError("有效像元过少，无法稳定分析，请检查影像质量。")

    # 自动策略：>=4个波段视为可尝试NDVI
    change_source = "NDVI差分" if min(ds1.count, ds2.count) >= 4 else "变化强度（像元差分）"

    pixel_area_m2 = abs(ds1.transform.a * ds1.transform.e)

    return PreparedData(
        arr_t1=arr1,
        arr_t2=arr2,
        transform=ds1.transform,
        crs=ds1.crs,
        nodata=0,
        pixel_area_m2=float(pixel_area_m2),
        valid_mask=valid_mask,
        change_source=change_source,
    )
