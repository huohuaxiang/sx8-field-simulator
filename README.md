# SX-8 Field Simulator

浏览器内运行的3D机械蜘蛛场域模拟器。单个HTML文件、three.js 0.170（importmap从unpkg加载）、全部几何体由代码生成，没有任何外部模型。

角色为虚构公司**Saltus Field Robotics**的八腿勘测机器人**SX-8**，造型参考跳蛛。

## 打开方式

双击 `sx8-field-simulator.html` 即可在 Chrome / Edge / Safari 中运行（首次加载需联网取 three.js）。

- `?t=12.5` 从指定源时间开始
- `?hud=0` 隐藏 HUD
- `?q=low` 低画质（关闭 GTAO）
- `?capture=1` 采集模式（配合 `window.SX8` 逐帧渲染）

## 机器人构成

| 部位 | 内容 |
| --- | --- |
| 头胸部 | 椭球壳体 + 6片铰接甲壳（可开启）+ 顶部舱盖与激光雷达 |
| 主眼 ×2 | 三级伸缩镜筒、9叶虹膜快门、发光传感器与柠檬色环 |
| 副眼 ×6 | 环绕布置的小型镜头 |
| 螯肢 | 钛合金螯牙、针式取芯器、持续摆动的触肢 |
| 腹部 | 弧形甲板带 SX-8 标记与柠檬箭纹；尾部花瓣展开露出丝线卷轴、电池堆、三喷嘴纺丝器 |
| 腿部 ×8 | 基节→股节→膝→胫节→跖节→跗节（带爪），每腿2根液压杆实时跟随关节 |

所有零件都是独立可动体，可整体拆解（teardown）再重组。

## 渲染

PBR 材质（壳体带 clearcoat）、RoomEnvironment 环境光、软阴影、GTAO（背景/地面/测量环/接触阴影排除在 AO 通道外）、NeutralToneMapping；地面有细测量环与点阵。

## 动画时间轴（30 秒确定性循环）

`rappel → touchdown → walk → crouch+leap → optics → carapace → LEG L2 → abdomen → fangs → full teardown on a turntable → reassembly → ascend`

三连杆腿 IK、对角步态、脚不打滑；每个场景独立机位并平滑过渡。

## 操作

| 按键 | 作用 |
| --- | --- |
| `空格` | 播放 / 暂停 |
| `1`–`6` | HERO / OPTICS / CARAPACE / LEG L2 / SPINNERET / FANGS |
| `E` `L` `S` `T` | 拆解 / 标注 / 丝线 / 转台 |
| `C` | 回到自动机位 |
| `←` `→` | ±0.4 s |
| `↑` `↓` | ±0.08 s |

鼠标拖拽自由环绕，双击画布回自动机位；点任意按钮即进入手动模式。底部时间轴可拖动定位。

## 采集接口

```js
SX8.ready            // true 表示场景就绪
SX8.seek(t)          // 跳到源时间 t
SX8.advance(dt)      // 推进一步并渲染
SX8.prefill(t)       // 预热液压曲线
SX8.readJPEG(0.95)   // 取当前画布 JPEG dataURL
SX8.setBuffer(w,h)   // 改用小缓冲渲染，由 CSS 拉伸
SX8.stateAt(t)       // 该时刻的相位 / 机体位姿 / 丝线长度
```

## 视频

`media/SX8_field_simulator_20s_1080p60.mp4`

20.000 s · 1920×1080 · 60 fps · H.264 CRF 16 · AAC 48 kHz · 实测 −23.1 LUFS。源时间轴 30 s 按 1.5 倍速剪成 20 s，配乐为纯 numpy 合成的 A 小调 120 BPM，落地、开甲壳、拆解、上升等音效按帧对齐。

## 工具链

| 文件 | 用途 |
| --- | --- |
| `tools/score.py` | 纯 numpy 合成配乐（20 s / 48 kHz / 立体声） |
| `tools/render_video.py` | Playwright 逐帧采集（1280×720 缓冲，60 fps 输出） |
| `tools/encode.sh` | ffmpeg 编码 + 两遍 loudnorm 归一 + 混流 |
| `tools/shot.py` | 指定时刻截图，用于检查构图 |
| `tools/test_controls.py` | 用 `SX8.advance()` 泵帧验证按键与 HUD 状态 |
| `tools/responsive.py` | 移动端竖屏布局检查 |

```bash
python3 tools/score.py media/score.wav
python3 tools/render_video.py 0 1200
bash tools/encode.sh
```

## 说明

- 成片为纯画布画面，不含 HUD；HUD 在网页里实时可用。
- 内部以 1280×720 缓冲区渲染再升采样到 1080p（无头 SwiftShader 下单帧成本决定的）。
