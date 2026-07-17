# Deploy: Visa Docs (Multi-Country)

## Type

Claude Skill -- deployed via GitHub, no server needed. The skill is invoked by Claude Code or the Claude Agent runtime on the user's local machine.

## Prerequisites

- Python 3.8+ with packages: `pymupdf`, `reportlab`, `Pillow`
- Ghostscript installed (`brew install ghostscript` on macOS)
- (Optional) Zhipu API key for GLM-4V OCR (`ZHIPU_API_KEY` env var)

## How to Use

1. **Install the skill** in Claude Code (add to your skills directory)
2. **Set up environment** -- ensure Python deps are installed, Ghostscript is available
3. **Invoke the skill** -- tell Claude you want to generate NZ visa documents, then upload your source photos
4. Follow the **pre-flight checklist** prompts: travel plan, trip type, translator info
5. The skill generates all PDFs into an `output/` subdirectory alongside your source files

## Key Config

| Variable | Required | Description |
|----------|----------|-------------|
| `ZHIPU_API_KEY` | Optional | Zhipu GLM-4V API key for OCR. Without it, manual data entry is needed. |

## Output

A complete set of bilingual PDFs ready for upload to the Immigration New Zealand website:

```
output/
├── 01_passport_护照.pdf
├── 02_national_id_身份证.pdf
├── 03_employment_verification_在职证明.pdf
├── 04_household_register_户口本.pdf
├── 05_bank_statements_银行证明.pdf
├── 06_travel_itinerary_旅行计划.pdf
├── 07_statement_multiple_journeys_入境陈述.pdf  (multiple entry only)
├── 08_subsequent_journey_plan_后续旅行计划.pdf  (multiple entry only)
├── 10_proof_of_assets_资产证明.pdf
└── _MANIFEST.txt
```

## Notes

- All PDFs are generated locally; no data leaves the machine (except OCR API calls if configured)
- Each PDF is kept under 10MB via image scaling and Ghostscript compression
- The skill processes source photos placed in any directory -- output is always in `output/` alongside the sources
