"""
Media handling module (video, audio, images)
"""

import subprocess
from pathlib import Path
from typing import Optional


class MediaHandler:
    """媒体文件处理器 (截图、音频裁剪)"""
    
    @staticmethod
    def ms_to_s(ms: int) -> float:
        """毫秒转秒"""
        return ms / 1000.0
    
    @staticmethod
    def ensure_dir(p: Path) -> None:
        """确保目录存在"""
        p.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def run_ffmpeg(cmd: list) -> None:
        """执行 FFmpeg 命令"""
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise RuntimeError(
                f"FFmpeg failed: {' '.join(cmd)}\n{proc.stderr.decode('utf-8', 'ignore')}"
            )
    
    @staticmethod
    def screenshot(video: Path, t: float, out_jpg: Path, vf: Optional[str] = None) -> None:
        """截取视频帧并保存为 JPG (95% 质量)"""
        cmd = ["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(video)]
        if vf:
            cmd += ["-vf", vf]
        # 使用 JPEG 编码器,qscale:v 2 约等于 95% 质量
        cmd += ["-vframes", "1", "-c:v", "mjpeg", "-q:v", "2", str(out_jpg)]
        MediaHandler.run_ffmpeg(cmd)
    
    @staticmethod
    def cut_audio(video: Path, start: float, end: float, out_audio: Path) -> None:
        """裁剪音频片段"""
        dur = max(0.01, end - start)
        cmd = [
            "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
            "-i", str(video), "-vn", "-ac", "2", "-ar", "48000",
            "-c:a", "aac", "-b:a", "192k", str(out_audio)
        ]
        MediaHandler.run_ffmpeg(cmd)
    
    @staticmethod
    def file_to_base64(file_path: Path) -> str:
        """将文件转换为 Base64 编码字符串"""
        import base64
        
        if not file_path or not file_path.exists():
            return ""
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                b64 = base64.b64encode(data).decode('utf-8')
                
                # 添加 data URI scheme
                ext = file_path.suffix.lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                    mime_type = f"image/{ext[1:]}"
                    if ext == '.jpg':
                        mime_type = "image/jpeg"
                    return f"data:{mime_type};base64,{b64}"
                elif ext in ['.mp3', '.m4a', '.ogg', '.wav']:
                    mime_type = f"audio/{ext[1:]}"
                    if ext == '.m4a':
                        mime_type = "audio/mp4"
                    return f"data:{mime_type};base64,{b64}"
                else:
                    return f"data:application/octet-stream;base64,{b64}"
        except Exception as e:
            print(f"   ⚠️  读取文件失败 {file_path}: {e}")
            return ""
