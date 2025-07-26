# Bangladesh Freedom Fighter Database 🇧🇩

A static, comprehensive database of Bangladesh Liberation War (1971) freedom fighters scraped from the official Ministry of Liberation War Affairs (MOLWA) website.

[![Data Source](https://img.shields.io/badge/Source-MOLWA%20Bangladesh-green)](https://mis.molwa.gov.bd)
[![Disclaimer](https://img.shields.io/badge/Legal-See%20Disclaimer-red)](LICENSE)

## 📊 Dataset Overview

This dataset contains detailed information about **205,280 Bangladesh Liberation War freedom fighters** extracted from the official government database. The data includes personal information, location details, supporting documents, and family/heir information. **No photos are included in this release, but photo URLs are provided.**

### Key Points
- **Total Records:** 205,280 (fixed, official list)
- **Data Format:** One JSON file per fighter
- **Photos:** Not included (only URLs provided)
- **Data Size:** <300MB (JSON only)
- **Source:** https://mis.molwa.gov.bd
- **Terms:** See LICENSE file for important disclaimer

## 📁 Dataset Structure

```
final_code/
├── fighters/                # All JSON files (one per fighter)
├── README.md                # This file
├── CHANGELOG.md             # Release notes
├── LICENSE                  # Legal disclaimer and terms
├── data-schema.json         # JSON schema
├── sample-analysis.ipynb    # Example analysis notebook
└── location_data.json       # District/location mapping
```

### JSON Schema
Each fighter record (`fighters/{fighter_id}.json`) contains:
```json
{
  "fighter_number": "০১২৬০০০০০১৭",
  "detail_url": "https://mis.molwa.gov.bd/freedom-fighter-list/details/01260000017",
  "fighter_photo_url": "https://mis.molwa.gov.bd/uploads/ffbeneficiary/photo-1595152259.png",
  "basic_info": { ... },
  "prove_documents": [ ... ],
  "waris_info": [ ... ],
  "scraped_at": "2025-07-25T19:32:24.490947"
}
```

## 🏗️ Data Fields
- **fighter_number**: Unique ID (Bengali numerals)
- **detail_url**: Source page
- **fighter_photo_url**: Photo URL (not downloaded)
- **basic_info**: Name, parents, district, upazila, post office, village
- **prove_documents**: List of supporting documents
- **waris_info**: List of heirs/family (with relationship, photo URL)
- **scraped_at**: Timestamp

## 📊 Example Analysis (Python)
```python
import json
import pandas as pd
from pathlib import Path

files = list(Path('fighters').glob('*.json'))
data = [json.load(open(f, encoding='utf-8')) for f in files]
df = pd.json_normalize(data)
print(df.head())
```

## 📥 How to Use
- **GitHub**: Download or clone the `final_code/` folder. All data and documentation are included.
- **Fighters.zip**: This is a compressed archive containing all fighter JSON files. You can download it from the [releases page](https://github.com/abusayed0206/fflist/releases).
- **Kaggle**: The dataset is also available on Kaggle. Click [here](https://www.kaggle.com/datasets/abusayed0206/bangladesh-freedom-fighter-database) to access it.

## ⚖️ Legal Disclaimer
**IMPORTANT**: This dataset is provided for educational and research purposes only. The original data belongs to the Government of Bangladesh and was collected from their publicly accessible website. See the `LICENSE` file for detailed terms of use, disclaimers, and restrictions. Users must respect the dignity of freedom fighters and comply with applicable laws. Commercial use is prohibited.

## 📄 Citation
If you use this dataset, please cite:
```
Bangladesh Freedom Fighter Database (2025)
Source: Ministry of Liberation War Affairs, Bangladesh
https://mis.molwa.gov.bd
```

## 🏆 Acknowledgments
- Ministry of Liberation War Affairs, Bangladesh (original data)
- All freedom fighters of Bangladesh

---

**This dataset is static and will not be updated. The list of freedom fighters is fixed and complete as of July 2025.**
