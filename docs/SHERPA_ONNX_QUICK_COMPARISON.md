# sherpa-onnx vs Faster Whisper 快速对比表

**最后更新**: 2025-11-11

---

## 一、核心指标对比

| 指标 | Faster Whisper | sherpa-onnx Paraformer | sherpa-onnx Zipformer |
|------|---------------|----------------------|---------------------|
| **安装包大小** | 1-2 GB (含CUDA) | 4 MB | 4 MB |
| **模型大小** | 1.5 GB (large-v3) | 226 MB (int8) | 112 MB (small int8) |
| **总部署大小** | ~2-3 GB | ~230 MB | ~116 MB |
| **CPU RTF** | 10-20 | 0.15 | 0.06-0.10 |
| **GPU 需求** | 必需 (或极慢) | 不需要 | 不需要 |
| **流式转录** | 不支持 | **原生支持** | **原生支持** |
| **中文准确率** | 良好 | 优秀 | 优秀 |
| **英文准确率** | 优秀 | 良好 | 良好 |
| **内存占用** | 3-6 GB | 500-800 MB | 300-500 MB |
| **启动时间** | 5-10 秒 | 1-2 秒 | <1 秒 |
| **安装复杂度** | 高 (需配置CUDA) | 极低 (pip安装) | 极低 (pip安装) |

---

## 二、使用场景推荐

### 场景 1: 默认推荐配置
**推荐方案**: **sherpa-onnx Paraformer int8**

**原因**:
- 模型大小适中 (226 MB)
- CPU 性能优秀 (RTF 0.15)
- 中英文准确率高
- 支持流式转录
- 无 CUDA 依赖

**适用用户**: 80% 的用户

### 场景 2: 极致轻量化
**推荐方案**: **sherpa-onnx Zipformer Small**

**原因**:
- 最小模型 (112 MB)
- 最快推理 (RTF ~0.10)
- 最低内存占用
- 适合低端设备

**适用用户**: 低配置电脑、嵌入式设备

### 场景 3: 多语言泛化
**推荐方案**: **保留 Faster Whisper (可选)**

**原因**:
- 支持 100+ 种语言
- 多语言混合识别
- 专业领域词汇识别

**适用用户**: 需要小语种支持的用户

---

## 三、性能数据详解

### RTF (Real-Time Factor) 说明
RTF = 处理时间 / 音频时长

示例：10 秒音频
- Faster Whisper large-v3 (CPU): RTF 15 → 需要 150 秒
- sherpa-onnx Paraformer: RTF 0.15 → 需要 1.5 秒
- sherpa-onnx Zipformer: RTF 0.06 → 需要 0.6 秒

**性能提升**: sherpa-onnx 比 Faster Whisper 快 **30-300 倍**

### 中文准确率 (aishell 测试集)
- Faster Whisper large-v3: ~2-3% WER
- sherpa-onnx Paraformer: ~2-3% WER
- sherpa-onnx Zipformer CTC: **1.74% WER** (最佳)

**结论**: sherpa-onnx 在中文场景下**不逊于甚至优于** Whisper

---

## 四、流式转录对比

### Faster Whisper (不支持流式)
```
[录音 30 秒] → [等待处理 5-15 分钟] → [显示结果]
用户体验: 漫长等待，无实时反馈
```

### sherpa-onnx (原生流式)
```
[录音中] → [实时显示文字] → [自动断句] → [即时完成]
用户体验: 边录边显示，无等待感
```

**体验提升**: 减少 **70-90%** 的感知延迟

---

## 五、安装对比

### Faster Whisper
```bash
# 需要手动配置 CUDA 环境
1. 安装 CUDA 11.8 (1.5 GB)
2. 安装 cuDNN 9 (500 MB)
3. pip install faster-whisper
4. 下载模型 (1.5 GB)
总时间: 30-60 分钟
总大小: ~3 GB
```

### sherpa-onnx
```bash
# 一键安装
1. pip install sherpa-onnx
2. 下载模型 (226 MB)
总时间: 5-10 分钟
总大小: ~230 MB
```

**安装简化**: sherpa-onnx 安装时间减少 **80%**，体积减少 **90%**

---

## 六、内存占用对比

| 阶段 | Faster Whisper | sherpa-onnx Paraformer | sherpa-onnx Zipformer |
|------|---------------|----------------------|---------------------|
| 模型加载 | 3-4 GB | 300 MB | 150 MB |
| 推理峰值 | 4-6 GB | 500-800 MB | 300-500 MB |
| 空闲状态 | 2-3 GB | 300 MB | 150 MB |

**内存优势**: sherpa-onnx 减少 **80-90%** 内存占用

---

## 七、推荐决策矩阵

| 用户需求 | Faster Whisper | sherpa-onnx Paraformer | sherpa-onnx Zipformer |
|---------|---------------|----------------------|---------------------|
| 快速部署 | ❌ | ✅✅✅ | ✅✅✅ |
| 轻量化 | ❌ | ✅✅ | ✅✅✅ |
| CPU 性能 | ❌ | ✅✅✅ | ✅✅✅ |
| 流式转录 | ❌ | ✅✅✅ | ✅✅✅ |
| 中文准确率 | ✅✅ | ✅✅✅ | ✅✅✅ |
| 英文准确率 | ✅✅✅ | ✅✅ | ✅✅ |
| 多语言支持 | ✅✅✅ | ✅ | ✅ |
| 小语种支持 | ✅✅✅ | ❌ | ❌ |

**图例**:
- ✅✅✅ = 优秀
- ✅✅ = 良好
- ✅ = 一般
- ❌ = 不支持/不适合

---

## 八、迁移建议

### 立即迁移场景 (优先级: 高)
- ✅ 新用户默认配置
- ✅ CPU-only 用户
- ✅ 低端设备用户
- ✅ 需要流式转录的用户
- ✅ 追求快速启动的用户

### 可选保留 Faster Whisper 的场景
- 多语言混合识别（中英日韩混合）
- 小语种支持（阿拉伯语、泰语等）
- 专业领域词汇（医疗、法律术语）
- 已有用户习惯保持向后兼容

### 推荐配置策略
```json
{
  "transcription": {
    "provider": "sherpa_onnx",  // 默认使用 sherpa-onnx
    "fallback_provider": "local",  // 失败时回退到 Faster Whisper
    
    "sherpa_onnx": {
      "model_type": "paraformer",
      "streaming_mode": true
    },
    
    "local": {
      "model": "large-v3-turbo",
      "use_gpu": true
    }
  }
}
```

---

## 九、关键要点总结

### 为什么选择 sherpa-onnx？

1. **轻量化**: 安装包 + 模型 < 250 MB (vs 2-3 GB)
2. **快速**: CPU 推理快 30-300 倍
3. **流式**: 原生支持边录边转，无等待
4. **简单**: pip install 即可，无 CUDA 依赖
5. **准确**: 中文场景不逊于 Whisper
6. **跨平台**: Windows、Linux、macOS 完美支持

### 何时保留 Faster Whisper？

- 需要 100+ 种语言支持
- 小语种识别（如泰语、阿拉伯语）
- 多语言混合场景
- 作为备选方案保证系统健壮性

---

## 十、快速决策指南

```
是否需要小语种支持（如泰语、阿拉伯语）？
├── 是 → 保留 Faster Whisper
└── 否 → 使用 sherpa-onnx
    │
    ├── 是否需要极致轻量化（< 150 MB）？
    │   ├── 是 → Zipformer Small (112 MB)
    │   └── 否 → Paraformer (226 MB) ← **推荐**
    │
    └── 是否需要流式转录？
        ├── 是 → sherpa-onnx ← **强烈推荐**
        └── 否 → 两者皆可，但 sherpa-onnx 更快
```

---

## 十一、参考链接

- 详细技术分析: `docs/SHERPA_ONNX_LIGHTWEIGHT_ANALYSIS.md`
- sherpa-onnx 官方文档: https://k2-fsa.github.io/sherpa/onnx/
- 模型下载: https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models

---

**文档结束**
