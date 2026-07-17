#!/usr/bin/env python3
"""
compress_pdf.py - 压缩PDF到指定大小以内（默认2MB）
用法: python compress_pdf.py <input.pdf> [output.pdf] [--max-size MB]
"""
import sys
import os
import subprocess
import pymupdf

MAX_SIZE_MB = 2
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024


def get_file_size(path):
    return os.path.getsize(path)


def compress_with_ffmpeg(input_path, output_path):
    """使用ffmpeg压缩PDF（转换为低质量PDF再转回）"""
    # ffmpeg将PDF转为图片再转回，低CRF=高压缩
    tmp_dir = output_path + "_tmp_frames"
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        # 提取PDF页面为图片
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-vsync", "0", "-fps_mode", "copy",
            os.path.join(tmp_dir, "page_%04d.png")
        ], capture_output=True, check=True)

        # 获取页数
        pages = sorted([f for f in os.listdir(tmp_dir) if f.endswith(".png")])

        # 重新编码为PDF
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", "1",
            "-i", os.path.join(tmp_dir, "page_%04d.png"),
            "-vcodec", "libx264",
            "-crf", "28",  # 0=无损, 23=默认, 28=高压缩
            "-pix_fmt", "yuv420p",
            output_path
        ], capture_output=True, check=True)

    finally:
        # 清理临时文件
        import shutil
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

    return output_path


def compress_with_gs(input_path, output_path, quality="ebook"):
    """使用Ghostscript压缩PDF"""
    quality_presets = {
        "screen": ["-dNOPAUSE", "-dBATCH", "-dQUIET", "-dCompatibilityLevel=1.3",
                   "-dPDFSETTINGS=/screen", "-dColorImageResolution=72",
                   "-dGrayImageResolution=72", "-dMonoImageResolution=72"],
        "ebook": ["-dNOPAUSE", "-dBATCH", "-dQUIET", "-dCompatibilityLevel=1.5",
                  "-dPDFSETTINGS=/ebook", "-dColorImageResolution=150",
                  "-dGrayImageResolution=150", "-dMonoImageResolution=150"],
        "printer": ["-dNOPAUSE", "-dBATCH", "-dQUIET",
                    "-dPDFSETTINGS=/printer", "-dColorImageResolution=300"],
        "prepress": ["-dNOPAUSE", "-dBATCH", "-dQUIET",
                     "-dPDFSETTINGS=/prepress", "-dColorImageResolution=300"],
    }

    cmd = [
        "gs", "-sDEVICE=pdfwrite",
        *quality_presets.get(quality, quality_presets["ebook"]),
        f"-sOutputFile={output_path}",
        input_path
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript failed: {result.stderr.decode()}")

    return output_path


def compress_pymupdf(input_path, output_path):
    """使用PyMuPDF进行轻量级压缩（图片质量调整）"""
    doc = pymupdf.open(input_path)
    for page in doc:
        # 获取页面中的图片列表并降低质量
        for img in page.get_images():
            xref = img[0]
            base_image = doc.extract_image(xref)
            # 压缩图片：如果太大就降低采样率
            # 这里我们通过整体保存时控制
            pass

    # 使用mupdf的PDF压缩
    doc.save(output_path, garbage=3, deflate=True, clean=True)
    doc.close()
    return output_path


def compress_pdf(input_path, output_path=None, max_size_mb=MAX_SIZE_MB):
    """主压缩函数，尝试多种方法直到文件小于max_size_mb"""
    if output_path is None:
        output_path = input_path

    max_bytes = max_size_mb * 1024 * 1024
    current_size = get_file_size(input_path)
    print(f"Input size: {current_size / 1024 / 1024:.2f} MB")

    if current_size <= max_bytes:
        print(f"[SKIP] File already <= {max_size_mb}MB, copying...")
        if output_path != input_path:
            import shutil
            shutil.copy2(input_path, output_path)
        return output_path

    # 方法1：Ghostscript（最快，质量好）
    tmp1 = output_path + ".tmp1.pdf"
    try:
        print("[TRY] Ghostscript compression (ebook quality)...")
        compress_with_gs(input_path, tmp1, quality="ebook")
        if get_file_size(tmp1) <= max_bytes:
            os.replace(tmp1, output_path)
            print(f"[OK] Compressed: {get_file_size(output_path) / 1024 / 1024:.2f} MB")
            return output_path
        else:
            print(f"[FAIL] Still too large: {get_file_size(tmp1) / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"[FAIL] Ghostscript error: {e}")

    # 方法2：Ghostscript（screen quality，极限压缩）
    tmp2 = output_path + ".tmp2.pdf"
    try:
        print("[TRY] Ghostscript compression (screen quality)...")
        compress_with_gs(input_path, tmp2, quality="screen")
        if get_file_size(tmp2) <= max_bytes:
            os.replace(tmp2, output_path)
            if os.path.exists(tmp1):
                os.remove(tmp1)
            print(f"[OK] Compressed: {get_file_size(output_path) / 1024 / 1024:.2f} MB")
            return output_path
    except Exception as e:
        print(f"[FAIL] Ghostscript screen error: {e}")

    # 方法3：ffmpeg重新编码
    tmp3 = output_path + ".tmp3.pdf"
    try:
        print("[TRY] ffmpeg re-encoding...")
        compress_with_ffmpeg(input_path if (os.path.exists(tmp1) and os.path.exists(tmp2)) else input_path, tmp3)
        if get_file_size(tmp3) <= max_bytes:
            for t in [tmp1, tmp2]:
                if os.path.exists(t):
                    os.remove(t)
            os.replace(tmp3, output_path)
            print(f"[OK] Compressed: {get_file_size(output_path) / 1024 / 1024:.2f} MB")
            return output_path
    except Exception as e:
        print(f"[FAIL] ffmpeg error: {e}")

    # 最后手段：取最小的那个
    candidates = [c for c in [tmp1, tmp2, tmp3] if os.path.exists(c)]
    if candidates:
        best = min(candidates, key=get_file_size)
        if get_file_size(best) <= max_bytes:
            for c in candidates:
                if c != best:
                    os.remove(c)
            os.replace(best, output_path)
            print(f"[OK] Final size: {get_file_size(output_path) / 1024 / 1024:.2f} MB")
            return output_path
        else:
            print(f"[WARN] Could not compress below {max_size_mb}MB")
            print(f"       Smallest achievable: {get_file_size(best) / 1024 / 1024:.2f} MB")
            # Still use the smallest available
            os.replace(best, output_path)
            for c in candidates:
                if c != best:
                    os.remove(c)
            return output_path

    print("[ERROR] All compression methods failed")
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("-o", "--output", help="Output PDF file")
    parser.add_argument("--max-size", type=float, default=MAX_SIZE_MB, help=f"Max file size in MB (default: {MAX_SIZE_MB})")
    args = parser.parse_args()

    output = args.output or args.input.replace(".pdf", "_compressed.pdf")
    result = compress_pdf(args.input, output, args.max_size)
    if result:
        print(f"Output: {result}")
        sys.exit(0)
    else:
        sys.exit(1)
