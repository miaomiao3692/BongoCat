"""生成可直接用于本项目的两期演示GeoTIFF与研究区边界。"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box


def create_demo_raster(path: Path, arr: np.ndarray, transform, crs: str = "EPSG:3857") -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=arr.shape[1],
        width=arr.shape[2],
        count=arr.shape[0],
        dtype="float32",
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(arr.astype(np.float32))


def main() -> None:
    out_dir = Path("sample_data")
    out_dir.mkdir(parents=True, exist_ok=True)

    h, w = 256, 256
    transform = from_origin(500000, 4000000, 10, 10)  # 10m分辨率

    y, x = np.indices((h, w))

    # 构造四波段影像：B,G,R,NIR
    t1 = np.zeros((4, h, w), dtype=np.float32)
    t1[0] = 200 + 20 * np.sin(x / 20)
    t1[1] = 220 + 20 * np.cos(y / 25)
    t1[2] = 210 + 15 * np.sin((x + y) / 30)
    t1[3] = 300 + 40 * np.cos((x - y) / 35)

    t2 = t1.copy()
    change_zone = (x > 80) & (x < 180) & (y > 100) & (y < 220)
    # 模拟植被退化：红光升高、近红外降低
    t2[2][change_zone] += 35
    t2[3][change_zone] -= 60

    create_demo_raster(out_dir / "demo_t1.tif", t1, transform)
    create_demo_raster(out_dir / "demo_t2.tif", t2, transform)

    # 生成一个研究区边界（GeoJSON）
    aoi = box(500200, 3997600, 502000, 3999200)
    gdf = gpd.GeoDataFrame({"name": ["demo_aoi"]}, geometry=[aoi], crs="EPSG:3857")
    gdf.to_file(out_dir / "demo_aoi.geojson", driver="GeoJSON")

    print("演示数据生成完成：")
    print("- sample_data/demo_t1.tif")
    print("- sample_data/demo_t2.tif")
    print("- sample_data/demo_aoi.geojson")


if __name__ == "__main__":
    main()
