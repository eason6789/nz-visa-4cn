# Custom NZ Visa PDF Generation Pattern

This reference documents the real-world approach to generating NZ visa PDFs from actual scanned documents.

## Key Architecture

```python
# 1. Font Registration (don't rely on local OTF files!)
CN_FONT = None
for fp in ["/System/Library/Fonts/STHeiti Light.ttc", "/Library/Fonts/Arial Unicode.ttf"]:
    if os.path.exists(fp):
        if fp.endswith('.ttc'):
            pdfmetrics.registerFont(TTFont("CN", fp, subfontIndex=0))
        else:
            pdfmetrics.registerFont(TTFont("CN", fp))
        CN_FONT = "CN"
        break
if not CN_FONT: CN_FONT = "Helvetica"

# 2. Image processing: HEIC conversion + EXIF stripping (TWO failure modes!)

def proc_img(path, max_s=2000, user_rotate=None):
    pil = Image.open(path)

    # Mode A: normal EXIF-based rotation (e.g. camera JPG with orientation tag)
    pil = ImageOps.exif_transpose(pil)

    # Mode B: iPhone HEIC→JPG conversion — EXIF is stripped, but pixels ARE rotated!
    # HEIC: sensor writes landscape, EXIF=6 (rotate 90°CW), macOS converts to portrait pixels
    # JPG after conversion: portrait pixels + NO EXIF tag → exif_transpose() does nothing
    # Fix: if width>height AND long_edge>3000 AND no EXIF tag → rotate back 90°CW
    # EXIF Orientation tag (0x0112) - use getexif(), NOT get_ifd
    exif_tag = pil.getexif().get(0x0112)  # 0x0112 = Orientation tag
    if pil.size[0] > pil.size[1] and max(pil.size) > 3000 and not exif_tag:
        pil = pil.transpose(Image.ROTATE_90)

    # Mode C: user-requested final rotation (e.g. ROTATE_270 for CCW 90°)
    if user_rotate:
        pil = pil.transpose(user_rotate)

    data = pil.tobytes()                    # strip EXIF completely
    pil = Image.frombytes('RGB', pil.size, data)
    w, h = pil.size
    if max(w, h) > max_s:
        r = max_s / max(w, h)
        pil = pil.resize((int(w*r), int(h*r)), Image.LANCZOS)
    return pil

# Usage with rotation:
#   ROTATE_90  = clockwise 90°
#   ROTATE_270 = counterclockwise 90° (user says "图片逆时针旋转90度" → ROTATE_270)

# 3. Aspect-ratio-preserving RLImage (no stretch!)
def img_keep_ratio(path, max_w_mm=130, max_h_mm=140):
    pil = proc_img(path)
    w, h = pil.size
    s = min((max_w_mm*mm)/w, (max_h_mm*mm)/h, 1.0)
    return RLImage(tmpf(pil), width=w*s, height=h*s)

# 4. Paragraph helper for all Chinese-containing cells
def Pcn(text):
    return Paragraph(text, ParagraphStyle("cn", fontName=CN_FONT, fontSize=8, textColor=C_DT))

# 5. Bank transaction translator (sorted by key length DESC)
def cn2en(text):
    if not text: return text
    if not re.search(r'[\u4e00-\u9fff]', text): return text
    result = text
    items = sorted(TX_CN_EN.items(), key=lambda x: -len(x[0]))
    for cn, en in items:
        result = result.replace(cn, en)
    return result

# 6. All Chinese text = Paragraph with CN_FONT
tx_data = [["Date", "Amount", "Summary"]] + raw_rows
# WRONG: plain strings in table cells
table_data = tx_data
# RIGHT: wrap every cell in Paragraph
table_data = [[Pcn(c) for c in row] for row in tx_data]
```

## Document Order
- 04 Household Register: **Personal Info Page first (!)**, Cover second
- 03 Employment: **PageBreak** between Part 1 (employment) and Part 2 (business license)
- 10 Assets: **PageBreak** between Part 1 (property) and Part 2 (loan certificate)

## DPI Balance
- Multi-page docs (bank statement, 19 pages): dpi=1.5 to stay under 10MB
- Single-page docs (loan cert, 1 page): dpi=3.0 for readability
