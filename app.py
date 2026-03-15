import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.change_detection import compute_change_products, suggest_default_threshold
from src.data_utils import (
    AnalysisError,
    ensure_tiff_upload,
    load_aoi_geometry,
    read_raster_from_upload,
)
from src.export_utils import (
    export_change_mask_geotiff,
    export_png_figure,
    make_stats_csv_bytes,
)
from src.preprocess import align_and_prepare_datasets
from src.visualization import (
    plot_binary_mask,
    plot_change_map,
    plot_rgb_preview,
)

st.set_page_config(page_title="土地变化监测MVP", layout="wide")
st.title("🛰️ 土地变化监测小程序（本地版）")
st.caption("面向新手：上传两期GeoTIFF，自动对齐、检测变化并导出结果。")


def _save_uploaded_file(uploaded_file, suffix: str) -> Path:
    """将上传文件写入临时文件并返回路径。"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return Path(tmp.name)


with st.sidebar:
    st.header("1) 上传数据")
    t1_file = st.file_uploader("上传第一期影像（GeoTIFF）", type=["tif", "tiff"])
    t2_file = st.file_uploader("上传第二期影像（GeoTIFF）", type=["tif", "tiff"])
    aoi_file = st.file_uploader("可选：上传研究区边界（.shp/.geojson/.zip）", type=["shp", "geojson", "json", "zip"])

    st.header("2) 参数设置")
    threshold_override = st.number_input(
        "变化阈值（留空默认自动建议）",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.01,
        help="阈值越小，检测越敏感。建议先用默认值，再微调。",
    )
    use_manual_threshold = st.checkbox("使用手动阈值", value=False)

    run_clicked = st.button("🚀 开始分析", type="primary")

st.info(
    "默认流程：若未上传研究区，程序自动使用两期影像重叠区域；"
    "若可计算NDVI，则优先使用NDVI差分，否则退化为变化强度法。"
)

if run_clicked:
    try:
        if t1_file is None or t2_file is None:
            raise AnalysisError("请先上传两期GeoTIFF影像。")

        ensure_tiff_upload(t1_file)
        ensure_tiff_upload(t2_file)

        t1_path = _save_uploaded_file(t1_file, suffix="_t1.tif")
        t2_path = _save_uploaded_file(t2_file, suffix="_t2.tif")

        with st.spinner("正在读取影像并自动对齐，请稍候..."):
            ds1 = read_raster_from_upload(t1_path)
            ds2 = read_raster_from_upload(t2_path)
            aoi_geom = load_aoi_geometry(aoi_file) if aoi_file else None
            prep = align_and_prepare_datasets(ds1, ds2, aoi_geom)

        suggested = suggest_default_threshold(prep.change_source)
        threshold = threshold_override if use_manual_threshold else suggested

        with st.spinner("正在执行变化检测..."):
            result = compute_change_products(prep, threshold=threshold)

        st.success("分析完成！")
        st.write(f"**变化指标来源：** {prep.change_source}")
        st.write(f"**使用阈值：** {threshold:.4f}")

        col1, col2 = st.columns(2)
        with col1:
            fig1 = plot_rgb_preview(prep.arr_t1, title="第一期影像预览")
            st.pyplot(fig1, use_container_width=True)
        with col2:
            fig2 = plot_rgb_preview(prep.arr_t2, title="第二期影像预览")
            st.pyplot(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            fig3 = plot_change_map(result.change_metric, prep.change_source)
            st.pyplot(fig3, use_container_width=True)
        with col4:
            fig4 = plot_binary_mask(result.binary_mask)
            st.pyplot(fig4, use_container_width=True)

        stats_df = pd.DataFrame(
            [
                {
                    "指标来源": prep.change_source,
                    "阈值": threshold,
                    "变化面积(平方米)": result.changed_area_m2,
                    "研究区面积(平方米)": result.total_area_m2,
                    "变化占比(%)": result.changed_ratio * 100,
                }
            ]
        )
        st.subheader("变化统计")
        st.dataframe(stats_df, use_container_width=True)

        out_dir = Path("outputs")
        out_dir.mkdir(parents=True, exist_ok=True)

        png_path = out_dir / "变化结果预览.png"
        export_png_figure(fig4, png_path)

        geotiff_path = out_dir / "变化掩膜.tif"
        export_change_mask_geotiff(
            geotiff_path,
            result.binary_mask,
            prep.transform,
            prep.crs,
            prep.nodata,
        )

        csv_bytes = make_stats_csv_bytes(stats_df)
        st.download_button(
            "下载统计CSV",
            data=csv_bytes,
            file_name="变化统计.csv",
            mime="text/csv",
        )

        with open(geotiff_path, "rb") as f:
            st.download_button(
                "下载变化掩膜GeoTIFF",
                data=f.read(),
                file_name=geotiff_path.name,
                mime="image/tiff",
            )

        with open(png_path, "rb") as f:
            st.download_button(
                "下载结果PNG",
                data=f.read(),
                file_name=png_path.name,
                mime="image/png",
            )

    except AnalysisError as e:
        st.error(f"分析失败：{e}")
    except Exception as e:
        st.exception(e)
else:
    st.write("请在左侧上传数据并点击 **开始分析**。")

st.markdown("---")
st.markdown("**新手提示：** 可先运行 `generate_demo_data.py` 生成演示数据，再上传测试。")
