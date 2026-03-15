# 土地变化监测小程序（本地MVP）

这是一个**可本地运行、适合新手、尽量一次就能跑起来**的土地变化监测示例项目。
你只需要上传两期同一区域GeoTIFF，程序会自动完成对齐、变化检测，并导出结果。

---

## 1. 功能概览

- 上传两期遥感影像（GeoTIFF）
- 可选上传研究区边界（shp / geojson / zip）
- 自动检查并处理坐标系、分辨率、网格对齐
- 优先执行 NDVI 差分变化检测（当波段数 >= 4）
- 若无法NDVI，自动使用像元差分变化强度方案
- 支持阈值调节
- 输出：
  - 两期影像预览图
  - 变化指标图（NDVI差分或变化强度）
  - 二值变化掩膜图
  - 变化面积与占比统计
  - 导出 PNG / CSV / GeoTIFF

---

## 2. 环境要求

- Python 3.11（推荐）
- Windows 10/11 普通电脑可运行

---

## 3. 安装依赖

在项目根目录执行：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> 如果你在 PowerShell 中执行激活命令：
> `.\venv\Scripts\Activate.ps1`

---

## 4. 生成最小可运行示例数据（推荐先做）

如果你手里没有真实遥感数据，先运行：

```bash
python generate_demo_data.py
```

会生成：

- `sample_data/demo_t1.tif`
- `sample_data/demo_t2.tif`
- `sample_data/demo_aoi.geojson`

然后用这三份文件直接测试整套流程。

---

## 5. 启动程序

```bash
streamlit run app.py
```

浏览器打开后按界面提示操作：

1. 上传第一期影像 `demo_t1.tif`
2. 上传第二期影像 `demo_t2.tif`
3. 可选上传 `demo_aoi.geojson`
4. 点击“开始分析”
5. 下载 PNG / CSV / GeoTIFF

---

## 6. 上传你自己的数据

### 6.1 影像要求

- 格式：GeoTIFF（`.tif` / `.tiff`）
- 两期影像建议覆盖同一区域
- 建议有投影坐标（CRS）
- 建议波段说明：
  - 若有红光 + 近红外（一般第3和第4波段）可做NDVI
  - 若没有，会自动切换到变化强度方案

### 6.2 研究区边界要求（可选）

- 支持 `.shp`、`.geojson`、`.json`、`.zip`
- zip应包含完整shapefile组件（.shp/.dbf/.shx 等）
- 若不上传边界，默认使用两期影像重叠区域

---

## 7. 常见报错与处理

1. **上传文件为空**

   - 重新选择有效文件。

2. **影像无法打开**

   - 检查是否真的是GeoTIFF，或文件是否损坏。

3. **波段数不够**

   - 至少需要1个波段；少于4个波段时无法做NDVI，会自动降级到差分法。

4. **研究区边界无效**

   - 检查矢量是否为空、几何是否损坏、自相交等。

5. **两期重叠范围过小**

   - 更换覆盖范围更一致的影像。

6. **导入shp失败**
   - 尝试改为GeoJSON，或将完整shp打包为zip后上传。

---

## 8. 项目结构

```text
.
├── app.py
├── generate_demo_data.py
├── requirements.txt
├── README.md
├── src
│   ├── __init__.py
│   ├── data_utils.py
│   ├── preprocess.py
│   ├── change_detection.py
│   ├── visualization.py
│   └── export_utils.py
├── sample_data
│   └── README.md
└── outputs
    └── README.md
```

---

## 9. 默认策略说明

- 不上传研究区边界：使用两期影像重叠范围
- 阈值不手动设置：自动推荐默认阈值（NDVI=0.15，差分=0.20）
- 优先保证“能跑通、能出结果、流程清晰”

祝你使用顺利！
