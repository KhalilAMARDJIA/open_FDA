"""
OpenFDA Medical Device Adverse Event Analysis - Quarto Report Generator
Python script that generates a Quarto report using R code chunks for visualization
"""

import pandas as pd
from collections import Counter
import re
from rapidfuzz import fuzz
from pathlib import Path
from typing import List, Dict
from datetime import datetime


# =========================================================
# CONFIGURATION
# =========================================================
class Config:
    """Centralized configuration"""
    DATA_PATH = "saved_csv/event_data.csv"
    OUTPUT_DIR = Path("./plots")
    REPORT_DIR = Path("./report")
    DELIMITER = "|"
    
    # Thresholds
    MANUFACTURER_THRESHOLD = 65
    BRAND_THRESHOLD = 75
    
    # Display settings
    TOP_N_PROBLEMS = 20
    TOP_N_BRANDS = 5
    
    # Exclusion lists
    PATIENT_EXCLUSIONS = [
        "No Code Available",
        "No Known Impact Or Consequence To Patient",
        "Symptoms or Conditions",
        "No Information",
        "No Consequences Or Impact To Patient",
        "Appropriate Clinical Signs",
        "No Clinical Signs",
        "Conditions Term / Code Not Available",
        "Insufficient Information",
        "No Patient Involvement",
        "Reaction",
        "Patient Problem/Medical Problem"
    ]
    
    PRODUCT_EXCLUSIONS = [
        "Adverse Event Without Identified Device or Use Problem",
        "Appropriate Term/Code Not Available",
        "Unknown (for use when the device problem is not known)",
        "Insufficient Information",
        "No Apparent Adverse Event"
    ]

Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
Config.REPORT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# DATA LOADING
# =========================================================
def load_data(filepath: str, delimiter: str = "|") -> pd.DataFrame:
    """Load and clean FDA event data"""
    df = pd.read_csv(filepath, sep=delimiter)
    df = df.dropna(subset=["manufacturer_g1_name", "brand_name"])
    print(f"✓ Loaded {len(df):,} records from {filepath}")
    return df


# =========================================================
# TEXT NORMALIZATION & FUZZY MATCHING
# =========================================================
def normalize_text(text: str) -> str:
    """Normalize text for consistent matching"""
    if pd.isna(text):
        return ""
    text = str(text).upper()
    text = re.sub(r"[^A-Z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fuzzy_group(values: List[str], threshold: int = 85) -> List[List[str]]:
    """Group similar strings using fuzzy matching"""
    groups = []
    for value in values:
        if not value:
            continue
        
        matched = False
        for group in groups:
            if fuzz.partial_ratio(value, group[0]) > threshold:
                group.append(value)
                matched = True
                break
        
        if not matched:
            groups.append([value])
    
    return groups


def standardize_series(series: pd.Series, threshold: int = 85) -> pd.Series:
    """Standardize a pandas series using fuzzy matching"""
    cleaned = series.fillna("").astype(str).apply(normalize_text)
    uniques = cleaned.unique()
    groups = fuzzy_group(uniques, threshold)
    
    mapping = {}
    for group in groups:
        canonical = min(group, key=len)
        for item in group:
            mapping[item] = canonical
    
    return cleaned.map(mapping)


def add_standardized_columns(df: pd.DataFrame, 
                             manufacturer_threshold: int = 75,
                             brand_threshold: int = 75) -> pd.DataFrame:
    """Add standardized manufacturer and brand columns"""
    df = df.copy()
    df["manufacturer_std"] = standardize_series(
        df["manufacturer_g1_name"], 
        threshold=manufacturer_threshold
    )
    df["brand_std"] = standardize_series(
        df["brand_name"], 
        threshold=brand_threshold
    )
    
    print(f"✓ Standardized {df['manufacturer_std'].nunique()} manufacturers")
    print(f"✓ Standardized {df['brand_std'].nunique()} brands")
    
    return df


# =========================================================
# DATA PREPARATION FOR R
# =========================================================
def prepare_data_for_r(df: pd.DataFrame, output_dir: Path = Config.REPORT_DIR):
    """Save processed data for R to read"""
    # Save processed data (date should already be converted)
    output_path = output_dir / "processed_data.csv"
    df.to_csv(output_path, index=False)
    print(f"✓ Saved processed data to {output_path}")
    
    return output_path


def get_summary_statistics(df: pd.DataFrame) -> Dict:
    """Get summary statistics as a dictionary"""
    return {
        'total_reports': len(df),
        'date_range_start': df['date_received'].min().strftime('%Y-%m-%d'),
        'date_range_end': df['date_received'].max().strftime('%Y-%m-%d'),
        'unique_manufacturers': df['manufacturer_std'].nunique(),
        'unique_brands': df['brand_std'].nunique(),
        'top_manufacturers': df['manufacturer_std'].value_counts().head(5).to_dict(),
        'top_brands': df['brand_std'].value_counts().head(5).to_dict()
    }


# =========================================================
# R CODE GENERATION HELPERS
# =========================================================
def generate_r_exclusion_list(exclusions: List[str]) -> str:
    """Generate R code for exclusion list"""
    formatted = ['  "' + item + '"' for item in exclusions]
    return "c(\n" + ",\n".join(formatted) + "\n)"


# =========================================================
# QUARTO REPORT GENERATION
# =========================================================
def generate_quarto_report(df: pd.DataFrame, 
                          stats: Dict,
                          output_path: Path = Config.REPORT_DIR / "fda_analysis_report.qmd"):
    """Generate Quarto markdown file with R code chunks"""
    
    # Prepare data for R
    data_path = prepare_data_for_r(df)
    
    # Generate exclusion lists for R
    patient_exclusions_r = generate_r_exclusion_list(Config.PATIENT_EXCLUSIONS)
    product_exclusions_r = generate_r_exclusion_list(Config.PRODUCT_EXCLUSIONS)
    
    # Generate Quarto document
    qmd_content = f'''---
title: "OpenFDA Medical Device Adverse Event Analysis"
subtitle: "Analysis of FDA Medical Device Adverse Event Reports"
author: "FDA Data Analysis Team"
date: today
format:
    typst: default
execute:
  echo: false
  warning: false
  message: false
  freeze: auto
---

```{{r setup}}
#| include: false
library(tidyverse)
library(scales)
library(knitr)
library(lubridate)

# Load processed data
df <- read_csv("processed_data.csv", show_col_types = FALSE)

# Configuration
PATIENT_EXCLUSIONS <- {patient_exclusions_r}

PRODUCT_EXCLUSIONS <- {product_exclusions_r}

# Helper functions
parse_problem_lists <- function(series) {{
  series %>%
    str_remove_all("\\\\[|\\\\]|'") %>%
    str_split(", ") %>%
    unlist()
}}

shorten_brand_name <- function(brand, max_words = 4) {{
  words <- str_split(brand, " ")[[1]]
  if (length(words) > max_words) {{
    paste(words[1:max_words], collapse = " ")
  }} else {{
    brand
  }}
}}
```

## Executive Summary

This report presents an analysis of **{stats['total_reports']:,}** FDA medical device adverse event reports collected between {stats['date_range_start']} and {stats['date_range_end']}.

### Dataset Overview

- **Total Reports**: {stats['total_reports']:,}
- **Date Range**: {stats['date_range_start']} to {stats['date_range_end']}
- **Unique Manufacturers**: {stats['unique_manufacturers']:,}
- **Unique Device Brands**: {stats['unique_brands']:,}

---

## Methodology

### Data Standardization

The analysis employs fuzzy matching algorithms to standardize manufacturer and brand names, addressing inconsistencies in naming conventions across reports. This standardization process uses the **RapidFuzz** library with partial ratio matching to group similar names under a canonical representation.

### Problem Classification

Patient and product problems are extracted and categorized, excluding non-informative categories to focus on meaningful data patterns.

---

## Analysis Results

### Manufacturer and Brand Distribution

```{{r fig-manufacturer-brand}}
#| fig-cap: "Distribution of adverse event reports by standardized manufacturer and brand names"
#| fig-height: 6

top_mfrs <- df %>%
  count(manufacturer_std, sort = TRUE) %>%
  slice_head(n = 10) %>%
  pull(manufacturer_std)

plot_data <- df %>%
  filter(manufacturer_std %in% top_mfrs) %>%
  count(manufacturer_std, brand_std) %>%
  group_by(manufacturer_std) %>%
  mutate(
    manufacturer_std = fct_reorder(manufacturer_std, n, .fun = sum)
  )

ggplot(plot_data, aes(x = manufacturer_std, y = n, fill = brand_std)) +
  geom_col() +
  scale_fill_viridis_d(option = "cividis") +
  scale_y_continuous(labels = comma) +
  labs(
    title = sprintf("Top 10 Manufacturers and Associated Brands (%s reports)", 
                   format(nrow(df), big.mark = ",")),
    x = NULL,
    y = "Number of Reports",
    fill = "Brand"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "right",
    plot.title = element_text(face = "bold", size = 14)
  )
```

---

### Patient Problem Analysis

```{{r fig-patient-problems}}
#| fig-cap: "Top 20 patient problems reported in medical device adverse events"
#| fig-height: 7

problems <- parse_problem_lists(df$patient_problems)

problem_df <- tibble(problem = problems) %>%
  filter(!problem %in% PATIENT_EXCLUSIONS) %>%
  count(problem, sort = TRUE) %>%
  slice_head(n = 20) %>%
  mutate(problem = fct_reorder(problem, n))

ggplot(problem_df, aes(x = n, y = problem)) +
  geom_col(fill = "steelblue", color = "black", linewidth = 0.3) +
  scale_x_continuous(labels = comma, expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = sprintf("Top Patient Problems (%s reports)", format(nrow(df), big.mark = ",")),
    x = "Number of Reports",
    y = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 14),
    panel.grid.major.y = element_blank()
  )
```

\\newpage

### Product Problem Analysis

```{{r fig-product-problems}}
#| fig-cap: "Top 20 product problems identified in adverse event reports"
#| fig-height: 7

problems <- parse_problem_lists(df$product_problems)

problem_df <- tibble(problem = problems) %>%
  filter(!problem %in% PRODUCT_EXCLUSIONS) %>%
  count(problem, sort = TRUE) %>%
  slice_head(n = 20) %>%
  mutate(problem = fct_reorder(problem, n))

ggplot(problem_df, aes(x = n, y = problem)) +
  geom_col(fill = "coral", color = "black", linewidth = 0.3) +
  scale_x_continuous(labels = comma, expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = sprintf("Top Product Problems (%s reports)", format(nrow(df), big.mark = ",")),
    x = "Number of Reports",
    y = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 14),
    panel.grid.major.y = element_blank()
  )
```

\\newpage

### Temporal Trends

#### Cumulative Report Growth (Linear Scale)

```{{r fig-cumulative-linear}}
#| fig-cap: "Cumulative adverse event reports over time for top 5 brands (linear scale)"
#| fig-height: 5

top_brands <- df %>%
  count(brand_std, sort = TRUE) %>%
  slice_head(n = 5) %>%
  pull(brand_std)

plot_data <- df %>%
  filter(brand_std %in% top_brands) %>%
  arrange(brand_std, date_received) %>%
  group_by(brand_std) %>%
  mutate(
    cumulative = row_number(),
    brand_label = str_to_title(map_chr(brand_std, shorten_brand_name))
  ) %>%
  ungroup()

ggplot(plot_data, aes(x = date_received, y = cumulative, color = brand_label)) +
  geom_line(linewidth = 1.2) +
  scale_color_brewer(palette = "Set1") +
  scale_x_date(date_labels = "%Y-%m", date_breaks = "6 months") +
  scale_y_continuous(labels = comma) +
  labs(
    title = "Cumulative Adverse Event Reports by Medical Device Brand",
    x = "Date Received",
    y = "Cumulative Reports",
    color = "Brand Name"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "right",
    plot.title = element_text(face = "bold", size = 14)
  )
```

#### Cumulative Report Growth (Logarithmic Scale)

```{{r fig-cumulative-log}}
#| fig-cap: "Cumulative adverse event reports over time for top 5 brands (log scale)"
#| fig-height: 5

ggplot(plot_data, aes(x = date_received, y = cumulative, color = brand_label)) +
  geom_line(linewidth = 1.2) +
  scale_color_brewer(palette = "Set1") +
  scale_x_date(date_labels = "%Y-%m", date_breaks = "6 months") +
  scale_y_log10(labels = comma) +
  labs(
    title = "Cumulative Adverse Event Reports by Medical Device Brand (Log Scale)",
    x = "Date Received",
    y = "Cumulative Reports (log scale)",
    color = "Brand Name"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "right",
    plot.title = element_text(face = "bold", size = 14)
  )
```

---

## Top Manufacturers

```{{r table-manufacturers}}
top_mfr_data <- df %>%
  count(manufacturer_std, sort = TRUE) %>%
  slice_head(n = 5) %>%
  mutate(
    Rank = row_number(),
    Manufacturer = manufacturer_std,
    Reports = format(n, big.mark = ","),
    `% of Total` = sprintf("%.2f%%", n / nrow(df) * 100)
  ) %>%
  select(Rank, Manufacturer, Reports, `% of Total`)

kable(top_mfr_data, align = c("c", "l", "r", "r"))
```

---

## Top Device Brands

```{{r table-brands}}
top_brand_data <- df %>%
  count(brand_std, sort = TRUE) %>%
  slice_head(n = 5) %>%
  mutate(
    Rank = row_number(),
    Brand = brand_std,
    Reports = format(n, big.mark = ","),
    `% of Total` = sprintf("%.2f%%", n / nrow(df) * 100)
  ) %>%
  select(Rank, Brand, Reports, `% of Total`)

kable(top_brand_data, align = c("c", "l", "r", "r"))
```

---

## Technical Appendix

### Data Source

- **Database**: OpenFDA Medical Device Adverse Events
- **API Access**: [https://open.fda.gov/apis/device/event/](https://open.fda.gov/apis/device/event/)

### Analysis Tools

- **Python 3.x** with pandas and rapidfuzz for data processing
- **R** with tidyverse and ggplot2 for visualization
- **Fuzzy Matching**: RapidFuzz library for text standardization
- **Visualization**: ggplot2 for statistical graphics
- **Report Generation**: Quarto for reproducible analytics

### Exclusion Criteria

**Patient Problems Excluded:**

```
No Code Available, No Known Impact, Symptoms or Conditions,
No Information, No Consequences, Insufficient Information
```

**Product Problems Excluded:**

```
Adverse Event Without Identified Device, No Apparent Adverse Event,
Appropriate Term/Code Not Available, Unknown, Insufficient Information
```

---

## Report Metadata

- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Dataset Version**: {stats['date_range_end']}
- **Analysis Pipeline**: OpenFDA Medical Device Adverse Event Analysis v2.0
'''
    
    # Write Quarto file
    with open(output_path, 'w') as f:
        f.write(qmd_content)
    
    print(f"✓ Generated Quarto report: {output_path}")
    
    return output_path


# =========================================================
# MAIN PIPELINE
# =========================================================
def run_analysis_with_report(data_path: str = Config.DATA_PATH):
    """Run complete analysis pipeline and generate Quarto report"""
    print("\n" + "="*60)
    print("STARTING FDA ADVERSE EVENT ANALYSIS WITH REPORT GENERATION")
    print("="*60 + "\n")
    
    # Load and prepare data
    df = load_data(data_path, Config.DELIMITER)
    df = add_standardized_columns(
        df, 
        Config.MANUFACTURER_THRESHOLD, 
        Config.BRAND_THRESHOLD
    )
    
    # Convert date
    if 'date_received' in df.columns:
        df['date_received'] = pd.to_datetime(df['date_received'].astype(str), format='%Y%m%d')
        print(f"✓ Converted date_received to datetime format")
    
    # Get statistics
    stats = get_summary_statistics(df)
    
    # Generate Quarto report
    report_path = generate_quarto_report(df, stats)
    
    print("\n" + "="*60)
    print("✓ ANALYSIS COMPLETE")
    print("="*60)
    print(f"\nTo render the PDF report, run:")
    print(f"  quarto render {report_path} --to pdf")
    print(f"\nTo render HTML report, run:")
    print(f"  quarto render {report_path} --to html")
    print(f"\nOr preview:")
    print(f"  quarto preview {report_path}")
    print("\n" + "="*60)
    print("NOTE: PDF rendering requires:")
    print("  - A LaTeX distribution (TinyTeX, TeX Live, or MikTeX)")
    print("  - R packages: tidyverse, scales, knitr, lubridate")
    print("  - Install with: install.packages(c('tidyverse', 'scales', 'knitr', 'lubridate'))")
    print("="*60 + "\n")
    
    return df, report_path


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    analyzed_data, report_path = run_analysis_with_report()
