# Visa Docs (多国签证材料生成器)

Automatically generates visa application documents for multiple countries from Chinese-language source materials. Uses OCR (GLM-4V) to read scanned documents and produces formatted bilingual PDFs with original-image + English-translation side-by-side layouts.

## Supported Countries

| Country | Key | Visa Type |
|---------|-----|-----------|
| New Zealand | `nz` | Visitor Visa (INZ) |
| Australia | `au` | Visitor Visa Subclass 600 |

## Features

- **Multi-country support** — unified pipeline with country-specific output formats
- **OCR-powered data extraction** — reads Chinese text from photos/scans via Zhipu GLM-4V
- **Bilingual PDF output** — A4 landscape pages: original (left) + English translation (right)
- **EXIF-aware image orientation** — auto-corrects HEIC/JPG rotation issues
- **Bank statement parsing** — extracts transactions from CMB and other Chinese bank PDFs
- **Multi-column translation** — preserves table structure for tax records and similar documents
- **Smart image compression** — balances file size (NZ: 10MB, AU: 5MB) with readability

## Quick Start

```bash
pip install pymupdf reportlab Pillow openpyxl
```

Set environment variable `ZHIPU_API_KEY` for GLM-4V OCR (new users get free quota).

## Output Structure

### New Zealand
```
output/
├── 01_passport_护照.pdf
├── 02_national_id_身份证.pdf
├── 03_employment_verification_在职证明.pdf
├── 04_household_register_户口本.pdf
├── 05_bank_statements_银行证明.pdf
├── 06_travel_itinerary_旅行计划.pdf
├── 07_statement_multiple_journeys_入境陈述.pdf
├── 08_subsequent_journey_plan_后续旅行计划.pdf
├── 10_proof_of_assets_资产证明.pdf
```

### Australia
```
output/
├── 00_COVER_LETTER.pdf
├── A_Passport.pdf
├── B_Employment_Verification.pdf
├── C_Bank_Deposit_and_Wealth_Management.pdf
├── D_Tax_Payment_Records.pdf
├── E_Securities_Holdings.pdf
├── F_Property_Ownership_Certificate.pdf
├── G_Vehicle_Registration.pdf
├── H_Travel_Itinerary.pdf
├── I_Bank_Statements.pdf
```

## Project Structure

```
├── SKILL.md              # Skill definition (supports both NZ and AU)
├── README.md
├── templates/            # Translation templates for each document type
├── scripts/              # PDF generation and data extraction utilities
├── examples/             # NZ example outputs
├── references/           # Custom generation pattern reference
```

## Key Differences: NZ vs AU

| Aspect | NZ | AU |
|--------|-----|-----|
| File naming | Chinese filenames with underscore | English filenames with letter prefix |
| Max file size | 10MB | 5MB |
| Cover letter | Not required | Required (5-section structure) |
| Asset valuation | Not required | Required (CNY + AUD dual currency) |
| Multi-entry | Separate statement + plan | Integrated into cover letter |
| Translator note | Required on each page | Not required |

## License

MIT
