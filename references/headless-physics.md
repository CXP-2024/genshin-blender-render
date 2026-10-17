# 无界面 PMX 衣发解算

这是已在奥黛塔与沃雅妮莎短片上验证的 MMD 兼容流程：Node / MMDLoader / MMDAnimationHelper / Ammo.js 读取 PMX 刚体和关节，Blender 仅导出和回放。无需启动 MMD、浏览器或 Blender GUI；不叠加 Blender 刚体/布料。官方 MMD.exe 的结果不能据此宣称逐位一致。

## 依赖与输入

上游为 https://github.com/yyc-git/VMDPhysicsBake ，但本次使用的是已有工作环境中的 `src/tool/bake-fixed-timeline.mjs` 及其配套修改版 `lib/MMDLoader.js`、`lib/MMDAnimationHelper.js`、`lib/MMDPhysics.js`。不能用重新下载的默认 `yarn bake` 入口替代并假定等价。先查工程已有交接文档、源文件哈希与成功输出；缺少匹配实现时，明确依赖差异，再做短片兼容性验证。

冻结原始 PMX、认可的无物理场景、人体动作、相机 VMD 和版本。动态骨集合来自 `rigids.mode != 0` 的 bone 索引，不能仅凭“裙/髪”名称猜。源 PMX 不覆写，处理用代理副本；保存代理前后逐项比较刚体和关节，不能只比较文件大小。

## 动作对齐后再解算

直接把含脚 IK 的原配布 VMD 交给另一个 Helper，可能得到与既有 Blender 画面不同的身体碰撞姿态。本次曾观察到约 16.7cm 偏差，已拒绝该分支。已验证方案：

1. 在每个输出时刻读取 Blender **evaluated** 的最终姿态，包含 IK、父骨和 grant 的结果。
2. 转成 PMX 原始、局部轴为单位矩阵的 FK 骨架。设 `C=((1,0,0),(0,0,-1),(0,1,0))`，导入比例为 `s`；本片 `s=.08`。`D` 为 evaluated pose 矩阵，`R` 为 Blender rest 矩阵：
   - `skin = D.rotation @ inverse(R.rotation)`；Node 世界旋转为 `transpose(C) @ skin @ C`。
   - Node 世界骨头位置为 `transpose(C) @ D.translation / s`。本片 armature 世界矩阵为 identity；其他工程须先显式消除 armature 变换，不可直接套用。
   - 对每骨先算 `inverse(parent_world) @ child_world`，局部平移再减去 PMX 局部 rest offset。PMX 坐标转 Node 时翻转 Z；写 VMD 时位置 `(x,y,-z)`、四元数 `(-x,-y,z,w)`。
3. 所有骨名用可逆 ASCII 短名映射，避开 VMD 骨名 15 字节的限制。FK 输入只写非物理骨，人体和物理不要双重驱动。
4. 已烘焙的非物理骨在代理 PMX 中撤去重复 grant / IK 语义。动态骨保留原有语义；本次两个模型没有动态 grant。不要把这种特例推广成任意模型都删 grant。
5. 关闭 Helper 的 IK，因为输入已是最终 FK。保存静态身体碰撞骨世界位置样本，与 Node 输出反向换算比较，通过后才回灌。

## 实际配置与时间轴

本次参考配置：`useLoader=true`、`ammoSource=npm`、`frameCount=421`；`unitStep=1/65`、`maxStepNum=3`、`gravity=[0,-98,0]`、`solverIterations=10`、`warmupFrames=60`、`physicsUpdateInterval=1`。三条输入/输出路径使用绝对路径；该入口的相对路径基准是工具脚本目录，未必是配置文件目录。

- Helper 首次 `play()` 时先到动作首帧，再 reset / warmup；不能在 T-pose 预热后瞬跳到动作首帧。
- 第 0 帧预热后采样，每后续输出帧调用两次 `helper.update(1/60)`，实际输出固定 30fps。Bullet 的 `1/65` 内部子步与 Helper 的 60Hz 推进不同。
- 预热 60 次不是 60 张 30fps 成片。不要每帧 reset，不要跳帧推进，也不要单改配置中的 `fixedFPS/frameRate` 就宣称改变了硬编码采样循环。
- 本次增加 solver 到 60，或改成 1/120 子步没有改善稳定性，未用于交付。更大数值不自动代表更好；保留失败对照，不盲目加精度。
- 该入口实际输出 JSON，即使变量沿用 VMD_OUT_PATH；必须保留位置和旋转，不能采用“只导出旋转、位置恒零”的旧路径。

## 回灌与验证

用 `mmd_tools.core.vmd.importer.BoneConverter(pose_bone, s)` 转换 JSON 的局部位置与旋转。反向短名映射须全部命中。只替换动态骨的 loc/rotation 曲线，四元数保持相邻符号连续，烘焙曲线使用 LINEAR；保留原始人体动作、morph、材质及相机。最终 `scene.rigidbody_world` 应为空，避免二次解算。

Node 的 RH 世界位置 `(x,y,z)` 对应 Blender `(x,-z,y)*s`。本片数值容差采用 `1e-4m`，实际误差约 `2e-6m`；容差须结合工程比例判断。可使用：

```text
python scripts/verify_physics.py physics.json aliases.json --repeat repeated.json --body-samples body_samples.json --scale .08 --import-audit import_audit.json
```

验证同输入重复输出、有限坐标、单位四元数、骨集合、静态碰撞骨对齐、回灌世界坐标，以及人体曲线指纹前后一致。数值通过后仍需连续播放，检查全身与脸部，定位加速度/转角突跳的极端帧。

网格 BVH 只能作为定位工具：统计蒙皮区域时排除描边权重等非骨骼 vertex group；检查几何时排除描边壳。服装分层、混合权重边界与配饰接触会产生相交计数，不能把计数直接称为可见穿模数量。单骨转角也不能代表整段物理已通过。

## 原运镜与已验收范围

完整导入原 camera VMD，保留位置、旋转、FOV 和切镜，不用几张静态相机代替。本片保留同一个 `Z=-.20m` 高度 wrapper；它是工程适配值，不是通用值。认可光向是 `Light Direction` Euler `(-65,0,18)` 度，不添加普通灯光去改变已认可 shader。

本次渲染 241..420 帧，对应原动作 8..14 秒；此前完整解算 421 帧，截取结果时无需在 GPU 上再次模拟预滚。两人独立解算的 6 秒预览已获认可。双人同场刚体互撞测试被用户暂缓，交付没有混入该实验结果；今后是否需要共享物理世界，应结合镜头里的真实交互与用户范围决定，不默认扩测。
