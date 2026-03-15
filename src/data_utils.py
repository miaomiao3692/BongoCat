from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import geopandas as gpd
import rasterio
from shapely.geometry.base import BaseGeometry


class AnalysisError(Exception):
    """业务级异常，给前端展示友好报错。"""


def ensure_tiff_upload(uploaded_file) -> None:
    """检查上传文件扩展名是否为GeoTIFF。"""
    if uploaded_file is None or uploaded_file.size == 0:
        raise AnalysisError("上传文件为空，请重新上传。")
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".tif", ".tiff"}:
        raise AnalysisError(f"文件 {uploaded_file.name} 不是GeoTIFF，请上传 .tif 或 .tiff。")


def read_raster_from_upload(path: Path) -> rasterio.io.DatasetReader:
    """读取栅格文件并校验基础合法性。"""
    try:
        ds = rasterio.open(path)
    except Exception as e:
        raise AnalysisError(f"影像无法打开：{path.name}，错误：{e}") from e

    if ds.count < 1:
        raise AnalysisError(f"影像 {path.name} 波段数不足（至少需要1个波段）。")
    return ds


def _read_aoi_vector(path: Path) -> BaseGeometry:
    """读取矢量边界并返回合并后的几何。"""
    try:
        gdf = gpd.read_file(path)
    except Exception as e:
        raise AnalysisError(f"研究区边界无法读取：{e}") from e

    if gdf.empty:
        raise AnalysisError("研究区边界为空。")

    geom = gdf.geometry.unary_union
    if geom is None or geom.is_empty or not geom.is_valid:
        raise AnalysisError("研究区边界无效，请检查几何是否合法。")
    return geom


def load_aoi_geometry(uploaded_file) -> Optional[BaseGeometry]:
    """支持读取shp/geojson/zip上传的研究区边界。"""
    if uploaded_file is None:
        return None

    if uploaded_file.size == 0:
        raise AnalysisError("研究区边界文件为空。")

    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix in {".geojson", ".json", ".shp"}:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            return _read_aoi_vector(Path(tmp.name))

    if suffix == ".zip":
        tmp_dir = Path(tempfile.mkdtemp())
        zip_path = tmp_dir / "aoi.zip"
        zip_path.write_bytes(uploaded_file.getbuffer())
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)
        shp_files = list(tmp_dir.glob("*.shp"))
        if not shp_files:
            raise AnalysisError("ZIP中未找到.shp文件，请上传完整shapefile压缩包。")
        return _read_aoi_vector(shp_files[0])

    raise AnalysisError("研究区边界仅支持 shp、geojson、json 或 zip。")
