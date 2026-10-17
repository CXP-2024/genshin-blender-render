## 原神 / MMD 材质提交前检查

涉及原神角色时，先使用 [genshin-blender-render](https://github.com/CXP-2024/genshin-blender-render) 建立材质与多光向试片基线，再使用本 skill 的队列/实例流程。

- 锁定 Blender、Morningstar/Festivity、mmd_tools 版本和输入哈希；冻结引擎。Shader to RGB 配方使用 EEVEE，不能因 OptiX 可用就换 Cycles。
- 检查脸部实际 UV 范围、眼睛透明层和衣料 Shadow Ramp 子节点图像。Packed_Ramp 与 Shadow_Ramp 按具体采样器区分，不能凭文件名相近混用。
- 保留原始模型；记录材质转换前后网格数量；MMD 原生细描边与 GN 描边只开一套。
- 提交前打包外部资源；云端相同版本先出一帧与本地对照，再扩展任务。全身及脸部、正面及侧光必须有图。
- 保存 audit/config/输入清单/日志/输出 SHA-256。generated 只表示生成完毕，通过视觉验收才是 accepted；静态结果不代表动画物理和眼睛视差通过。
- GPU 占用、计费预算、停止/删除实例、队列恢复仍按本 skill 和当前用户授权执行。本检查不启动机器或下载模型。

现有 bench_scene.py / GCP OptiX 示例仅测试硬件，不用于转换原神场景。提交已打包 review.blend 时使用固定版本 Blender 的 `--background scene.blend --python-exit-code 1 --render-frame 1`，不传 `--engine CYCLES`；先确认后台 EGL/OpenGL 可用及 EEVEE 实际使用 GPU。
