# 已验证配方与故障根因

2026-10-17，奥黛塔、沃雅妮莎全新 PMX 导入 + Morningstar v1.0.2.1 + Blender 4.2.23 LTS，静态材质试片获用户认可。本技能提取本轮自编排脚本，不包含第三方模型或节点库。

## 基线与作者教程

- 发布版：https://github.com/AstraMorningstar/Morningstar-Festivity-render-assistant/releases/tag/v1.0.2.1
- 更新示范：https://www.youtube.com/watch?v=Duq_vHFx71I （示范角色为薇斯纳）
- 基础教程：https://www.youtube.com/watch?v=89WUcWfqa2s
- 中文入口：https://www.bilibili.com/video/BV1Dae26iENj/
- 原版历史 shader：https://github.com/festivities/Blender-miHoYo-Shaders

这些是复现基线，不能永久称“最新版”。新任务如需最新版本应查作者发布记录。新版插件封装日期不表示内置 shader 已全面更新。保留作者 addon 源码不改；适配在工程脚本内完成。

## 本轮证据

|问题|观察|已采用修正|
|---|---|---|
|奥黛塔整脸阴影|脸部 UV1/UV2 全为 (0,1)，UVMap 非退化|新导入后跳过 Native UV1 混合，保留 UVMap|
|沃雅妮莎衣服、领口、花饰黑块|Body 02 的 Shadow Ramp 子节点 image=None|按对应 Lightmap 材质族显式绑定 256×20 Shadow_Ramp|
|材质族错配风险|奥黛塔“体/裙”对应 Body/Body01，沃雅妮莎顺序相反|通过 diffuse 像素对比确认，不能抄角色编号|
|眼睛异常|旧转换只剩 diffuse 渐变，透明层丢失|保留作者对这些角色的 blended eye 分层|
|描边|作者 GN 与 MMD 描边会重复|关闭 GN 后创建 mmd_tools 原生 edge_preview|

重新下载的奥黛塔 53 个、沃雅妮莎 47 个配套文件均与旧资源 SHA-256 一致。下载损坏不是本轮根因。关闭金属、关闭顶点 AO 的单变量试验未去除黑块；仅补齐 Ramp 即消除，所以保留金属、AO、阴影。

`face_type=3`、UV split=0、描边权重 .45、颜色 (.12,.08,.13,1) 是这次两个输入模型的试片参数，不是所有原神角色通用设置。新的模型修订要重新测量。

## 操作顺序

原始 PMX → mmd_tools 导入 → 选中 Mesh 转 Principled → 选 Armature → 作者环境 → 分配材质 → 配套贴图 → 光向 → 按实测选择脸 UV → 显式核查 Ramp → 表情层 → 后期 → 头部锚点 → 单一描边系统 → 打包 → 多光向试片。

自动材质转换会删除部分 MMD 高光/SP 覆盖面：本轮奥黛塔减少 22,193 面，沃雅妮莎减少 15,623 面。这是该输入的观察，不能当作每个角色的固定目标。必须记录前后网格和材质，保留源 PMX，检查衣服是否仍完整；不允许把任意删衣料当修复。

## 遇到失败

先冻结输入与失败场景，检查缺图、UV、节点、alpha、材质族、引擎版本。每次只改变一个因素，使用同一灯光和相机。模型同名不证明文件相同；来源相同不证明映射正确。新 packed FaceSDF 直接塞旧 Face Factor 已测试失败，不作为默认步骤。

本次只通过静态材质试片。完整动画眼睛视差、转头 SDF、表情与物理仍待验证。
