"""音频处理器"""

import numpy as np
from scipy import signal
from ..utils import AudioRecordingError, app_logger


class AudioProcessor:
    """音频预处理和格式转换"""
    
    def __init__(self):
        pass
    
    def resample_to_16khz(self, audio_data: np.ndarray, original_rate: int = 44100) -> np.ndarray:
        """重采样到16kHz"""
        if original_rate == 16000:
            return audio_data
        
        try:
            # 计算重采样比例
            resample_ratio = 16000 / original_rate
            new_length = int(len(audio_data) * resample_ratio)
            
            # 使用scipy的resample函数
            resampled = signal.resample(audio_data, new_length)
            
            app_logger.log_audio_event("Audio resampled", {
                "original_rate": original_rate,
                "target_rate": 16000,
                "original_length": len(audio_data),
                "new_length": len(resampled)
            })
            
            return resampled.astype(np.float32)
            
        except Exception as e:
            raise AudioRecordingError(f"Failed to resample audio: {e}")
    
    def normalize_audio(self, audio_data: np.ndarray, target_level: float = 0.8) -> np.ndarray:
        """音频标准化"""
        try:
            if len(audio_data) == 0:
                return audio_data
            
            # 计算RMS
            rms = np.sqrt(np.mean(audio_data**2))
            
            if rms > 0:
                # 计算增益
                gain = target_level / rms
                # 限制增益避免过度放大
                gain = min(gain, 10.0)
                normalized = audio_data * gain
                
                # 防止削波
                max_val = np.max(np.abs(normalized))
                if max_val > 1.0:
                    normalized = normalized / max_val
                
                app_logger.log_audio_event("Audio normalized", {
                    "original_rms": float(rms),
                    "gain": float(gain),
                    "final_max": float(np.max(np.abs(normalized)))
                })
                
                return normalized.astype(np.float32)
            else:
                return audio_data
                
        except Exception as e:
            raise AudioRecordingError(f"Failed to normalize audio: {e}")
    
    def remove_silence(self, audio_data: np.ndarray, threshold: float = 0.01, 
                      min_silence_duration: float = 0.5, sample_rate: int = 16000) -> np.ndarray:
        """移除静音部分"""
        try:
            if len(audio_data) == 0:
                return audio_data
            
            # 计算每个样本的能量
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.01 * sample_rate)     # 10ms hop
            
            frames = []
            for i in range(0, len(audio_data) - frame_length, hop_length):
                frame = audio_data[i:i + frame_length]
                energy = np.sqrt(np.mean(frame**2))
                frames.append(energy > threshold)
            
            # 找到语音段
            voice_frames = np.array(frames)
            min_silence_frames = int(min_silence_duration / (hop_length / sample_rate))
            
            # 简单的语音活动检测
            voice_segments = []
            start = None
            
            for i, is_voice in enumerate(voice_frames):
                if is_voice and start is None:
                    start = i
                elif not is_voice and start is not None:
                    if i - start > min_silence_frames:
                        voice_segments.append((start * hop_length, i * hop_length))
                    start = None
            
            # 如果录音结束时还在说话
            if start is not None:
                voice_segments.append((start * hop_length, len(audio_data)))
            
            # 合并语音段
            if voice_segments:
                result = []
                for start_idx, end_idx in voice_segments:
                    result.extend(audio_data[start_idx:end_idx])
                
                trimmed = np.array(result, dtype=np.float32)
                
                app_logger.log_audio_event("Silence removed", {
                    "original_length": len(audio_data),
                    "trimmed_length": len(trimmed),
                    "voice_segments": len(voice_segments)
                })
                
                return trimmed
            else:
                # 没有检测到语音，返回原始音频
                return audio_data
                
        except Exception as e:
            app_logger.log_error(e, "remove_silence")
            return audio_data  # 发生错误时返回原始音频
    
    def apply_noise_reduction(self, audio_data: np.ndarray) -> np.ndarray:
        """简单的噪声减少"""
        try:
            if len(audio_data) == 0:
                return audio_data
            
            # 简单的高通滤波器去除低频噪音
            sos = signal.butter(4, 80, 'hp', fs=16000, output='sos')
            filtered = signal.sosfilt(sos, audio_data)
            
            app_logger.log_audio_event("Noise reduction applied", {
                "original_length": len(audio_data),
                "filtered_length": len(filtered)
            })
            
            return filtered.astype(np.float32)
            
        except Exception as e:
            app_logger.log_error(e, "apply_noise_reduction")
            return audio_data  # 发生错误时返回原始音频
    
    def convert_to_whisper_format(self, audio_data: np.ndarray, sample_rate: int = 16000, remove_silence: bool = False) -> np.ndarray:
        """转换为Whisper所需的格式"""
        try:
            # Whisper期望16kHz, float32, 单声道, 范围[-1, 1]
            processed = audio_data.copy()
            
            # 确保是float32
            if processed.dtype != np.float32:
                processed = processed.astype(np.float32)
            
            # 确保在正确范围内
            if np.max(np.abs(processed)) > 1.0:
                processed = processed / np.max(np.abs(processed))
            
            # Apply audio processing pipeline
            processed = self.normalize_audio(processed)
            processed = self.apply_noise_reduction(processed)
            
            # Only remove silence if explicitly requested (disabled by default)
            if remove_silence:
                processed = self.remove_silence(processed, sample_rate=sample_rate)
            
            app_logger.log_audio_event("Audio converted for Whisper", {
                "final_length": len(processed),
                "final_duration": len(processed) / sample_rate,
                "final_range": [float(np.min(processed)), float(np.max(processed))]
            })
            
            return processed
            
        except Exception as e:
            raise AudioRecordingError(f"Failed to convert audio for Whisper: {e}")
    
    def get_audio_statistics(self, audio_data: np.ndarray, sample_rate: int = 16000) -> dict:
        """获取音频统计信息"""
        if len(audio_data) == 0:
            return {}
        
        return {
            "duration": len(audio_data) / sample_rate,
            "sample_count": len(audio_data),
            "sample_rate": sample_rate,
            "rms": float(np.sqrt(np.mean(audio_data**2))),
            "peak": float(np.max(np.abs(audio_data))),
            "zero_crossings": int(np.sum(np.diff(np.signbit(audio_data)))),
            "mean": float(np.mean(audio_data)),
            "std": float(np.std(audio_data))
        }