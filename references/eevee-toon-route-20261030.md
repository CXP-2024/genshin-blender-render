# Blender 5.2 EEVEE 自定义卡通路线（《愛包ダンスホール》v35）

2026-10-30 实际成片路线：双人、整首歌 6581 帧、1080p30 渲染，再超分插帧到 4K60。下列数值从交付工程读取，用于复现这个外观。

这不是原神着色器。它没有 Lightmap、FaceSDF、Shadow Ramp、金属 Matcap 和头部方向驱动。不要称它为游戏材质移植，也不要把下文的阈值套回 Festivity 路线。

## 什么时候用

| 输入 | 路线 |
|---|---|
| 官方 PMX，有配套游戏贴图，要游戏质感 | Festivity（[配方](recipe.md)）或下文 HoyoToon 路线 |
| Tripo、VRM 或自建模型，只有 BaseColor | 本路线 |
| 已认可的场景接续 | 沿用该场景，不换路线 |

## 版本与渲染设置

- Blender 5.2.1 LTS，EEVEE。材质里有 Shader to RGB，不能切 Cycles。
- 1920×1080，30 fps，Filter 1.5，色彩管理 Standard、Look None、Exposure 0、Gamma 1。
- 成片 32 采样。工程内保存的是 64，打包时改成 32；32 与 64 的 PSNR 不低于 51.9 dB，耗时减半。
- `shadow_pool_size = '2048'`，Raytracing 开（Screen），Fast GI 开，Motion Blur 关。
- 景深关闭：相机 `use_dof=False`。工程里留有 f/3.0、7 叶的参数和对焦关键帧，但没有生效。要景深时先渲几帧对比，再整片打开。
- 背景色 (0.03, 0.05, 0.12)，强度 0.6。

## 材质

角色材质最终输出 Emission，明暗在节点里算好，不靠 BSDF 直接出图。

```text
Diffuse BSDF → Shader to RGB → 亮度 → Map Range(SMOOTHSTEP) → t
颜色 = 贴图色 × mix(Shadow, 白, t)
再按 Layer Weight 的 Facing 叠加边缘光 → Emission
```

| 节点组 | 用于 | 明暗阈值 | 贴图 Gamma | 边缘光 |
|---|---|---|---|---|
| AiboToon | 皮肤、头发 | 0.03 → 0.09 | 头发 0.8，皮肤不加 | Blend 0.5，Power 3，强度 0.55，乘 Remap(t, 0.35–1)，颜色 (1, .96, .94)，ADD |
| AiboToonCloth | 衣物、配饰 | 0.03 → 0.12 | 0.7 | Blend 0.35，Power 1.6，强度 0.22，乘 t，颜色为 Gamma 后的贴图色与 (.75, .8, 1) 的混合，SCREEN |

| 类别 | Shadow 颜色 |
|---|---|
| 皮肤 | (0.98, 0.74, 0.70)，部分皮肤 (0.99, 0.86, 0.83) |
| 头发 | (0.86, 0.92, 0.99) |
| 衣物 | (0.84, 0.86, 0.94) |

- 眼白和虹膜不套卡通节点：虹膜保留多层贴图、透明混合和 Emission。
- 阈值和主光强度是一起调出来的，换灯光强度后要重新确认。
- 材质开 `use_transparent_shadow`。
- 新加的配件（如尾巴）复制同模型一个配件的材质，换贴图，这样色调和描边都一致。

## 灯光

- 主光 `AiboKeyDS`：Sun，强度 π，角度 1.5°，方向 (-0.85, 0.30, -0.45)。
- 灯光链接：主光的 receiver 和 blocker 都是角色集合，场景灯的 receiver 是场景集合 `AiboSetRecv`。`ToonKey` 不参与渲染。
- 第二位舞者用真实物体副本。镜像的集合实例会逃出灯光链接，着色会不同。

## 描边

- 用 mmd_tools 原生 `mmd_edge_preview`（Solidify 法线外扩），不叠加第二套描边。
- MMD 描边是屏幕定宽，Solidify 是世界单位。用驱动保持屏幕宽度：

```text
thickness = T0 * min(3, max(0.2, k * d / lens))
k = lens_ref / d_ref
```

  `d` 是相机到该舞者头部的距离，`T0` 和 `k` 在参考帧（本片 937）量取。两位舞者分别量。
- 眼周描边关闭。新配件的描边权重 = 蝴蝶结的权重中位数 ÷ 物体缩放，否则会变粗。
- 没有这个驱动的模型（如 Reset 精简版）thickness 是常量，换镜头距离后要重新看线宽。

## 合成

`Render Layers → Glare → Blur → Mix → Color Balance → 输出`

- Glare：Bloom，High，Threshold 0.95，Strength 0.3，Size 0.7。
- Blur：Gaussian，23 px。
- Mix：SCREEN，系数 0.16，A 是 Glare 结果，B 是模糊结果。
- Color Balance：Lift (0.95, 0.97, 1.08)，Gain (1.02, 1.00, 0.97)。

## 渲染前检查

- 逐帧扫描每个 MDD 的范围和位移。v31 的裙子有 7 处短暂炸开，渲染后才发现，代价是重渲。
- 穿插检查同时看 EEVEE 和灰色白模。
- 打包后本地渲一帧与原工程对比（本次最大差 1/255），上云后再对一帧（平均差 0.01/255）。
- Blender 必须加 `-y`，否则脚本驱动失效，描边宽度和表情都会错。
- 交付的 .blend 存在第 0 帧。

## 整片流程与成本

1. 打包：贴图内嵌，缓存改相对路径，32 采样，保存第 0 帧。
2. 云端：RTX PRO 6000 Spot，2 个 Blender 进程，约 2.2 帧/秒。进程数和下载细节见 gcp-blender-render。
3. 回传：在云端按 300 帧分段压成 `libx264rgb -crf 12 -pix_fmt rgb24`，不下载 PNG。本片 22 段约 1.7 GB，平均 47.5 dB。
4. 本地：解段 → Real-CUGAN 2 倍 → RIFE 2 倍 → NVENC，见 [超分与插帧](upscale-interpolate.md)。
5. 合成音轨：`-c:v copy` 拼接，音频按首帧偏移，不加 `-shortest`。

v35 实测云端约 1.05 小时，机器约 1.7 美元，加下载估算合计约 2 美元。实际金额以账单为准。

## 已知限制

- 脸部没有 SDF，阴影随法线走。
- 两个模型的版本不等价：`DeepSeek_Reset_4K_Lite` 用的是另一套 Genshin Lighting 材质，色调与本路线不完全相同。

## HoyoToon 路线（官方 PMX，2026-10-16 原型）

需要接近游戏的材质时，可在 Blender 5.2 用 gacha-setup（内置 Festivity PrimoToon v4）处理 PMX。这是原型记录，没有经过整片验证。

- 贴图和材质 JSON 取自 HoyoToon 资源站的角色包。
- PMX 通常直接使用游戏 diffuse 图集，用图像相关性把材质槽对应到游戏部件，改名为 `<前缀>_Mat_<部件>`，并合并成每材质一个槽。重复或空槽会让向导分割失败，身体变粉或变黑。
- 添加 `UV0`、`UV1` 两层（复制主 UV，原来的 UV1 先改名），不要添加白色顶点色 `Col`。
- 眼、眉、嘴层保留 MMD 配方，名字加 `HoYoverse - Genshin MMDEYE ` 前缀，让向导跳过。
- 没有绑定时向导会跳过灯光面板，要对每个 Light Vectors 修改器手动调用 `set_up_lighting_panel`，否则全黑。
- 描边 GN 关闭 `Toggle Vertex Colors`，PMX 没有游戏顶点色。
