---
name: genshin-blender-render
description: 使用 Blender 与 Morningstar Festivity 复现原神人物三渲二材质、脸部阴影、眼睛与 MMD 细描边，接续无界面 PMX 衣发物理、原 VMD 运镜，以及动漫超分和插帧视频交付。同时记录 Blender 5.2 EEVEE 自定义卡通路线，用于 Tripo、VRM 等没有游戏贴图的模型。云端机器管理另用对应 render skill。
---

# 原神角色三渲二渲染

先从全新模型导入建立可复现基线，再做艺术微调。保留原始文件，输出独立目录，不覆盖用户认可的场景。

## 先选路线

- 官方 PMX + 游戏贴图：走下文 Festivity 流程，需要更接近游戏时看 HoyoToon 原型。
- Tripo、VRM 等只有 BaseColor 的模型：走 [Blender 5.2 EEVEE 自定义卡通路线](references/eevee-toon-route-20261030.md)，这是《愛包》v35 成片的做法，不是原神着色器。
- 已认可的场景：沿用原路线，不互相混用参数。

## 接续已认可的成片

复现天天天国 2026-10-18 最终混合版时，先读 [最终外观与混合物理配方](references/final-recipe-20261018.md)，再读安装内的 `local/reproduction-20261018.md` 和资产哈希清单。该版本采用 R9 材质/灯光与 R11 局部衣带物理，不能从早期静态默认参数或全量重解物理替代。通用新角色导入仍按下文；本片的身体索引与时间段不可套到其他模型。

## 1. 锁定输入

- 阅读 [配方与根因](references/recipe.md) 和 [验收清单](references/acceptance.md)。本配方验证组合为 Blender 4.2.23 LTS、Morningstar v1.0.2.1 内置 Festivity v3.4、mmd_tools；其他版本先做兼容试片。
- 从作者发布页取得插件、官方模型及该角色/服装对应游戏纹理。来源在 [第三方说明](THIRD_PARTY_NOTICES.md)。用户已有合法本地资源时直接使用。不要把模型、贴图或第三方着色器再发布到公开仓库。
- 记录 Blender、插件和 mmd_tools 版本/文件哈希，PMX 和全部输入贴图 SHA-256。下载校验与材质正确性是两回事。
- 用 PMX 是为了复用本流程的 MMD 权重、表情和原生描边；原神渲染本身并非必须 PMX。FBX 需独立验证材质、眼睛与描边，不能声称等价。

## 2. 先检查再绑定

- 按实际像素、UV 与游戏材质族建立 diffuse → Lightmap → Shadow Ramp 映射；不能凭中文“体/裙”或文件编号猜。示例配置在 examples/，路径均相对配置文件，可改为绝对路径。
- 脸部 UV 只统计脸部材质实际使用的 loops。检查 UVMap、UV1、UV2 的范围；Native SDF UV 混合用到的层必须非退化。有常量层则保留有效 UVMap，不强制套教程 UV 分界值。
- `_FaceSdfMap`、Face01/02_Shadow 遮罩与旧 Festivity Face Factor 输入含义不同。未经解包/坐标/通道验证，不替换旧采样器的输入。
- 每个衣服材质逐层检查 `Shadow Ramp` 的纹理节点，必须有图。此版本的采样器使用 256×20 Shadow_Ramp；256×8 Packed_Ramp 不能直接代替。共享节点组先复制，防止串角色/衣料。
- 保留眼睛各层 alpha 与顺序，检查 morningstar_eye_mode。角色别名支持透明眼睛不等于完整支持所有新角色特性。只剩紫色渐变不算修好。

## 3. 执行配方

1. 复制示例 JSON 到工程目录，填写本地依赖、PMX、贴图、明确的脸材质原名、脸类型与输出路径。先检查模型真实脸 UV，更新配置。不要从身高猜 Face Type。
2. 执行 `blender --background --python-exit-code 1 --python scripts/build_character.py -- /absolute/config.json`。脚本会重置当前后台进程场景，不能用于未保存的交互会话。
3. 默认使用 EEVEE；Shader to RGB 不可因有 OptiX GPU 就切换 Cycles。更换版本/引擎/云端之前复核同一试片。
4. 对 MMD 人物优先原生细描边：关闭作者 GN 描边后调用 mmd_tools.edge_preview_setup，保留模型 edge_scale。二者不叠加。边宽与颜色是可调整的艺术参数。
5. 输出 audit.json、输入 manifest、打包 review.blend，以及正面/55°/280°光向的全身与脸部图。先低分辨率检查资源和管线，再出可审核尺寸。

## 4. 验收后再扩展

逐张查看全身、脸、眼睛、衣料、金属、发丝与描边；按验收清单记录实际通过范围。光向相同的修复前后图才可比较。不要靠关闭金属/AO/阴影或整体提亮掩盖缺图。

用户认可静态结果后再扩展舞蹈、表情、眨眼、转头、物理与动画时序。静态通过不代表完整游戏视差和物理通过。

## 5. 从认可场景接续动画

- 用户要求保持材质、打光、动作或运镜时，从认可场景副本接续，不重新跑材质转换。记录节点、人体动作曲线与相机动画指纹，物理回灌只替换动态骨。
- 衣发解算读 [无界面物理](references/headless-physics.md)：已验证路线为 evaluated FK → 原 PMX 刚体/关节 → VMDPhysicsBake / Ammo.js → 位置与旋转 JSON → Blender 动态骨曲线。它是 MMD 兼容实现，不称为官方 MMD.exe。
- 超分与插帧读 [4K / 60fps 后处理](references/upscale-interpolate.md)。采用已有匹配模型；切镜保留硬切。超分不是原生高分辨率重渲染，插帧也不会修复物理穿模。
- 用户限制本机 GUI 或 GPU 时，导出、解算、校验用无界面 CPU；图形渲染及 GPU 后处理交给已获授权的远端。不要因检测到本地 GPU 空闲而改变约定。
- 2026-10-17 的两人独立解算预览及其 4K / 60fps 试版已获用户认可，见 [动画验证记录](references/animation-validation-20261017.json)。快速飘带仍有少量插帧重影；双人同场物理被用户暂缓，不作为默认扩展或已验收能力。
- 若当前安装附带 `local/profile.md`，接续同一工程时先读其中的已验证脚本和资源路径；该文件仅保存本机索引，不随公开仓库发布。

本地调度读取 render-submit-queue；Paratera/GCP 分别读取对应 skill。先验证场景并打包资源，再提交既有队列。费用、实例启动/停止及 GPU 占用检查遵守对应技能和当前用户授权。
