# genshin-blender-render

给 Codex 使用的原神 Blender 三渲二 skill：将一次实际修复整理为可复现的材质流程，覆盖脸 UV、眼睛透明层、服饰 Ramp 和 mmd_tools 原生细描边。

已验证：Blender 4.2.23 LTS + Morningstar v1.0.2.1（内置 Festivity v3.4）+ mmd_tools，奥黛塔与沃雅妮莎静态试片，以及使用无界面 PMX 衣发解算、原 Mio 运镜的 6 秒预览。该预览的 Real-CUGAN 超分 + RIFE 插帧 4K60 试版也已获用户认可。不是完整游戏着色器移植，亦不保证任意模型/动作无穿模或插帧伪影。

## 安装

克隆到 Codex skills 目录：

```powershell
git clone git@github.com:CXP-2024/genshin-blender-render.git "$env:USERPROFILE/.codex/skills/genshin-blender-render"
```

在新会话调用 `$genshin-blender-render`。也可直接阅读 [SKILL.md](SKILL.md)。第三方依赖与模型自行取得，见 [说明](THIRD_PARTY_NOTICES.md)。

## 渲染

复制 examples 中配置并填好路径、模型实际脸材质名称，先阅读 [配方](references/recipe.md)。所有路径相对配置文件解析。

```powershell
& 'D:/Blender/blender.exe' --background --python-exit-code 1 --python ./scripts/build_character.py -- ./character.local.json
```

默认全身 900×1400、脸 1000×1000，三种光向；初次检查可降低 resolution_scale。输出输入哈希、操作与材质审计、packed review.blend 和 PNG。第三方文件及这些渲染工程放在 gitignore 的 outputs 或仓库之外。

```powershell
python scripts/input_manifest.py D:/assets/character --output manifest.local.json
python tests/test_contract.py
```

[渲染技能衔接](references/render-integration.md) 同步应用于本地 render-submit-queue、Paratera 与 GCP skills。GPU/实例调度仍由相应 skill 管理。本工具不自动启动云端或产生云账单。

`integrations/` 保存三个 render skill 的同版新增说明：将 SKILL.addition.md 追加到对应 SKILL.md，并将 references/ 下文件复制到其 references/ 目录。不会覆盖私有机器配置。

认可场景接续动画，读 [无界面物理](references/headless-physics.md)；交付高分辨率/高帧率视频，读 [超分与插帧](references/upscale-interpolate.md)。验证记录在 [动画试版指标](references/animation-validation-20261017.json)。新增 `verify_physics.py` 检查 JSON 对齐与回灌，`vmd_camera_cuts.py` 提取插帧应保留的原相机硬切；它们均为无界面 CPU 工具，不自动启动渲染或实例。

1080p30 整首歌 → 4K60 的实测流程、切镜 SSIM 阈值，以及 x264 / NVENC（H.264、HEVC、AV1）编码器的速度与画质对比，见 [超分与插帧](references/upscale-interpolate.md) 末尾两节。新任务默认使用 NVENC，同一部片中途不换编码器。

## 当前成片路线

《愛包ダンスホール》v35 用的是 Blender 5.2.1 EEVEE 自定义卡通材质（Emission + Shader to RGB），不是 Festivity：1080p30、32 采样，屏幕定宽 MMD 描边，RTX PRO 6000 云端渲染分段回传，本地超分插帧到 4K60。材质、灯光、合成参数、检查项和成本见 [EEVEE 卡通路线](references/eevee-toon-route-20261030.md)。同一文档记录了只有 BaseColor 的模型如何选路线，以及 HoyoToon 原型。

复刻参考视频或另一角色的效果时，按 [严格复刻迭代方法](references/replicate-effect-iteration.md) 执行；`scripts/compare_frames.py` 生成同帧并排审核图。
