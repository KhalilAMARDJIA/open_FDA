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
author: BVI Medical
date: today
lof: true
lot: true
toc: true
version: 1.0
format:
  medstata-typst:
    default-image-extension: svg
execute:
  echo: false
  warning: false
  message: false
  fig-width: 7
  fig-height: 5
  freeze: auto
---

```{{r setup}}
#| echo: false
#| results: 'hide'
#| message: false

# Load required libraries
library(tidyverse)
library(lubridate)
library(scales)
library(knitr)

# Custom ggplot2 theme matching base R aesthetics
theme_baseR <- function(base_size = 12) {{
  theme_classic(base_size = base_size) %+replace%
    theme(
      panel.grid = element_blank(),
      panel.border = element_rect(color = "black", fill = NA, linewidth = 0.5),
      axis.line = element_blank(),
      axis.ticks = element_line(color = "black"),
      plot.title = element_text(
        hjust = 0.5,
        face = "bold",
        margin = margin(b = 20, t = 10)
      ),
      plot.margin = unit(c(1.5, 1.5, 1, 1.5), "lines"),
      plot.title.position = "plot"
    )
}}
theme_set(theme_baseR())

# Save current locale and set to English
original_locale <- Sys.getlocale("LC_TIME")
Sys.setlocale("LC_TIME", "C")

# Color palette using brewer colors
brbg_colors <- scales::brewer_pal(palette = "BrBG")(6)
colors <- list(
  primary   = brbg_colors[1],
  secondary = brbg_colors[2],
  accent    = brbg_colors[3],
  highlight = brbg_colors[4],
  warning   = brbg_colors[5],
  info      = brbg_colors[6]
)

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

```{{r load-data}}
#| echo: false

# Read the data
data <- read_csv("processed_data.csv", show_col_types = FALSE)
```

```{{r compute-summary-stats}}
#| echo: false

# Compute all summary statistics
total_reports <- nrow(data)
date_min <- min(data$date_received, na.rm = TRUE)
date_max <- max(data$date_received, na.rm = TRUE)
duration_days <- as.numeric(date_max - date_min)
duration_months <- round(duration_days / 30.44, 1)

unique_manufacturers <- n_distinct(data$manufacturer_std)
unique_brands <- n_distinct(data$brand_std)

# Patient problems statistics
patient_problems_all_list <- parse_problem_lists(data$patient_problems)

reports_with_patient_problems <- sum(
  !patient_problems_all_list %in% PATIENT_EXCLUSIONS
)

# Monthly statistics
monthly_counts <- data %>%
  mutate(year_month = floor_date(date_received, "month")) %>%
  count(year_month) %>%
  arrange(year_month)

avg_monthly_reports <- round(mean(monthly_counts$n), 1)
max_monthly_reports <- max(monthly_counts$n)
max_month <- monthly_counts %>%
  filter(n == max_monthly_reports) %>%
  pull(year_month) %>%
  format("%B %Y")
```

# Executive Summary

This report analyzes **`r format(total_reports, big.mark=",")`** FDA medical device adverse event reports submitted between **`r format(date_min, "%B %d, %Y")`** and **`r format(date_max, "%B %d, %Y")`** (a period of **`r duration_months`** months). The dataset includes **`r format(unique_manufacturers, big.mark=",")`** unique manufacturers and **`r format(unique_brands, big.mark=",")`** unique device brands. The average reporting rate was **`r avg_monthly_reports`** reports per month, with peak reporting of **`r max_monthly_reports`** reports in **`r max_month`**.

```{{r summary-table}}
#| label: tbl-summary-stats
#| tbl-cap: "Summary statistics of FDA MAUDE reports"

summary_stats <- tibble(
  Metric = c(
    "Total Reports",
    "Date Range",
    "Reporting Duration",
    "Unique Manufacturers",
    "Unique Device Brands",
    "Average Monthly Reports",
    "Maximum Monthly Reports"
  ),
  Value = c(
    format(total_reports, big.mark = ","),
    paste(format(date_min, "%B %d, %Y"), "to", format(date_max, "%B %d, %Y")),
    paste(duration_days, "days (", duration_months, "months)"),
    format(unique_manufacturers, big.mark = ","),
    format(unique_brands, big.mark = ","),
    paste(avg_monthly_reports, "reports/month"),
    paste(max_monthly_reports, "reports in", max_month)
  )
)

kable(summary_stats, align = c("l", "l"))
```

# Methodology

## Data Source

The search of the FDA Manufacturer and User Facility Device Experience (MAUDE) database was conducted using the openFDA Device Event API. Retrieved JSON-formatted data were downloaded directly from the API and subsequently processed and cleaned for analysis.

## Data Standardization

The analysis employs fuzzy matching algorithms to standardize manufacturer and brand names, addressing inconsistencies in naming conventions across reports. This standardization process uses the **RapidFuzz** library with partial ratio matching to group similar names under a canonical representation.

## Problem Classification

Patient and product problems are extracted and categorized, excluding non-informative categories to focus on meaningful data patterns.

# Temporal Trend Analysis

## Overall Reporting Trends

```{{r temporal-analysis}}
#| label: fig-temporal-trends
#| fig-cap: "Monthly trend of FDA MAUDE reports"
#| fig-width: 8
#| fig-height: 6

monthly_plot_data <- data %>%
  mutate(year_month = floor_date(date_received, "month")) %>%
  count(year_month)

# Calculate appropriate date breaks based on data range
date_range_years <- as.numeric(difftime(max(data$date_received), 
                                        min(data$date_received), 
                                        units = "days")) / 365.25

if(date_range_years > 2) {{
  date_labels <- "%Y"
  date_breaks <- "1 year"
}} else {{
  date_labels <- "%b %Y"
  date_breaks <- "3 months"
}}

ggplot(monthly_plot_data, aes(x = year_month, y = n)) +
  geom_line(color = colors$primary, linewidth = 1.2) +
  geom_point(color = colors$primary, size = 3) +
  geom_smooth(
    method = "loess", 
    se = TRUE, 
    color = colors$secondary, 
    fill = colors$accent, 
    alpha = 0.2
  ) +
  scale_x_date(date_breaks = date_breaks, date_labels = date_labels) +
  scale_y_continuous(breaks = pretty_breaks()) +
  labs(
    title = "Monthly FDA MAUDE Reports",
    subtitle = paste(format(date_min, "%B %Y"), "-", format(date_max, "%B %Y")),
    x = "Month",
    y = "Number of Reports",
    caption = "Source: FDA MAUDE Database"
  )
```

```{{r compute-trend-stats}}
#| echo: false

# Identify peaks (above 75th percentile)
threshold <- quantile(monthly_plot_data$n, 0.75)
peak_months <- monthly_plot_data %>%
  filter(n > threshold) %>%
  arrange(desc(n)) %>%
  mutate(month_label = format(year_month, "%B %Y"))

peak_list <- paste(peak_months$month_label, collapse = ", ")
sd_monthly <- round(sd(monthly_plot_data$n), 1)
```

::: {{.callout-note}}
## Trend Observation
The reporting shows variability across months, with notable peaks in **`r peak_list`**. The average monthly reporting rate is **`r avg_monthly_reports`** reports, with a standard deviation of **`r sd_monthly`** reports.
:::

## Cumulative Reports Over Time

```{{=typst}}
#set page(
  flipped: true,
)
```

```{{r cumulative-plot}}
#| label: fig-cumulative-reports
#| fig-cap: "Cumulative FDA MAUDE reports over time"
#| fig-width: 10
#| fig-height: 6

cumulative_data <- data %>%
  arrange(date_received) %>%
  mutate(cumulative_count = row_number())

# Calculate appropriate date breaks
date_range_years <- as.numeric(difftime(max(data$date_received), 
                                        min(data$date_received), 
                                        units = "days")) / 365.25

if(date_range_years > 2) {{
  date_labels <- "%Y"
  date_breaks <- "1 year"
}} else {{
  date_labels <- "%b %Y"
  date_breaks <- "3 months"
}}

ggplot(cumulative_data, aes(x = date_received, y = cumulative_count)) +
  geom_line(color = colors$warning, linewidth = 1) +
  geom_point(color = colors$primary, size = 2, shape = 4) +
  scale_x_date(date_breaks = date_breaks, date_labels = date_labels) +
  scale_y_continuous(breaks = pretty_breaks(n = 10)) +
  labs(
    title = "Cumulative FDA MAUDE Reports",
    subtitle = "Growing trend analysis",
    x = "Date",
    y = "Cumulative Number of Reports",
    caption = "Source: FDA MAUDE Database"
  )
```

```{{=typst}}
#set page(
  flipped: false,
)
```

# Product Problem Analysis

```{{r compute-product-problems}}
#| echo: false

# Extract and count individual product problems
product_problems_vector <- parse_problem_lists(data$product_problems)

product_problems <- tibble(problems = product_problems_vector) %>%
  filter(
    !is.na(problems) &
    problems != "" &
    !problems %in% PRODUCT_EXCLUSIONS
  ) %>%
  count(problems, sort = TRUE) %>%
  slice_head(n = 20)

top_3_problems <- product_problems %>%
  head(3) %>%
  pull(problems)

total_product_problems <- sum(product_problems$n)
```

## Top Product Problems

```{{r product-problems-plot}}
#| label: fig-product-problems
#| fig-cap: "Most frequently reported product problems"
#| fig-width: 8
#| fig-height: 10

ggplot(product_problems, aes(x = reorder(problems, n), y = n)) +
  geom_col(fill = colors$highlight, alpha = 0.8) +
  geom_text(aes(label = n), hjust = -0.2, size = 3.5) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = "Top 20 Product Problems Reported",
    subtitle = paste0("(", format(date_min, "%B %Y"), 
                     " - ", format(date_max, "%B %Y"), ")"),
    x = "Product Problem",
    y = "Number of Reports",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(axis.text.y = element_text(size = 9))
```

::: {{.callout-warning}}
## Product Issues

The most frequently reported problems are:

1. **`r top_3_problems[1]`** - `r product_problems$n[1]` reports (`r round(100 * product_problems$n[1] / total_reports, 1)`%)
2. **`r top_3_problems[2]`** - `r product_problems$n[2]` reports (`r round(100 * product_problems$n[2] / total_reports, 1)`%)
3. **`r top_3_problems[3]`** - `r product_problems$n[3]` reports (`r round(100 * product_problems$n[3] / total_reports, 1)`%)

These top three issues account for **`r sum(product_problems$n[1:3])`** reports (**`r round(100 * sum(product_problems$n[1:3]) / total_reports, 1)`%** of all reports).
:::

# Patient Problem Analysis

```{{r compute-patient-problems}}
#| echo: false

# Extract and count patient problems
patient_problems_vector <- parse_problem_lists(data$patient_problems)

patient_problems <- tibble(problems = patient_problems_vector) %>%
  filter(
    !is.na(problems) &
    problems != "" &
    !problems %in% PATIENT_EXCLUSIONS
  ) %>%
  count(problems, sort = TRUE) %>%
  slice_head(n = 20)

total_patient_problems <- sum(patient_problems$n)
```

## Patient Problems Overview

```{{r patient-problems-plot}}
#| label: fig-patient-problems
#| fig-cap: "Patient problems reported in FDA MAUDE events"
#| fig-width: 8
#| fig-height: 10

ggplot(patient_problems, aes(x = reorder(problems, n), y = n)) +
  geom_col(fill = colors$info, alpha = 0.8) +
  geom_text(aes(label = n), hjust = -0.2, size = 3.5) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  labs(
    title = "Top 20 Patient Problems Reported",
    subtitle = "Clinical outcomes and adverse events",
    x = "Patient Problem",
    y = "Number of Reports",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(axis.text.y = element_text(size = 9))
```

# Manufacturer Analysis

## Top Manufacturers

```{{r compute-manufacturers}}
#| echo: false

# Calculate manufacturer statistics
top_manufacturers <- data %>%
  count(manufacturer_std, sort = TRUE) %>%
  slice_head(n = 10)

top_5_manufacturers <- top_manufacturers %>%
  head(5)

top_manufacturer <- top_5_manufacturers$manufacturer_std[1]
top_manufacturer_count <- top_5_manufacturers$n[1]
top_manufacturer_pct <- round(100 * top_manufacturer_count / total_reports, 1)
```

```{{r manufacturer-plot}}
#| label: fig-manufacturers
#| fig-cap: "Top 10 manufacturers by report volume"
#| fig-width: 8
#| fig-height: 6.5

ggplot(top_manufacturers, aes(x = reorder(manufacturer_std, n), y = n)) +
  geom_col(fill = colors$secondary, alpha = 0.8) +
  geom_text(aes(label = n), hjust = -0.2, size = 3.5) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = "Top 10 Manufacturers by Report Volume",
    x = "Manufacturer",
    y = "Number of Reports",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(axis.text.y = element_text(size = 9))
```

The top manufacturer, **`r top_manufacturer`**, accounts for **`r top_manufacturer_count`** reports (**`r top_manufacturer_pct`%** of total).

```{{r manufacturer-table}}
#| label: tbl-manufacturers
#| tbl-cap: "Top 5 manufacturers with report statistics"

manufacturer_table <- top_5_manufacturers %>%
  mutate(
    Rank = row_number(),
    Manufacturer = manufacturer_std,
    Reports = format(n, big.mark = ","),
    `% of Total` = sprintf("%.2f%%", n / total_reports * 100)
  ) %>%
  select(Rank, Manufacturer, Reports, `% of Total`)

kable(manufacturer_table, align = c("c", "l", "r", "r"))
```

# Device Brand Analysis

## Top Device Brands

```{{=typst}}
#set page(
  flipped: true,
)
```

```{{r compute-brands}}
#| echo: false

# Calculate brand statistics
top_brands <- data %>%
  count(brand_std, sort = TRUE) %>%
  slice_head(n = 10)

top_5_brands <- top_brands %>%
  head(5)

top_brand <- top_5_brands$brand_std[1]
top_brand_count <- top_5_brands$n[1]
top_brand_pct <- round(100 * top_brand_count / total_reports, 1)
```

```{{r brand-plot}}
#| label: fig-brands
#| fig-cap: "Top 10 device brands by report volume"
#| fig-width: 10
#| fig-height: 6

ggplot(top_brands, aes(x = reorder(brand_std, n), y = n)) +
  geom_col(fill = colors$primary, alpha = 0.8) +
  geom_text(aes(label = n), hjust = -0.3, size = 3.5) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.1))) +
  labs(
    title = "Top 10 Device Brands by Report Volume",
    x = "Brand",
    y = "Number of Reports",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(axis.text.y = element_text(size = 8))
```

```{{=typst}}
#set page(
  flipped: false,
)
```

The top device brand, **`r top_brand`**, accounts for **`r top_brand_count`** reports (**`r top_brand_pct`%** of total).

```{{r brand-table}}
#| label: tbl-brands
#| tbl-cap: "Top 5 device brands with report statistics"

brand_table <- top_5_brands %>%
  mutate(
    Rank = row_number(),
    Brand = brand_std,
    Reports = format(n, big.mark = ","),
    `% of Total` = sprintf("%.2f%%", n / total_reports * 100)
  ) %>%
  select(Rank, Brand, Reports, `% of Total`)

kable(brand_table, align = c("c", "l", "r", "r"))
```

## Brand Temporal Trends

```{{r brand-cumulative}}
#| label: fig-brand-cumulative
#| fig-cap: "Cumulative adverse event reports by top 5 brands"
#| fig-width: 8
#| fig-height: 6

brand_cumulative <- data %>%
  filter(brand_std %in% top_5_brands$brand_std) %>%
  arrange(brand_std, date_received) %>%
  group_by(brand_std) %>%
  mutate(
    cumulative = row_number(),
    brand_label = str_to_title(map_chr(brand_std, shorten_brand_name))
  ) %>%
  ungroup()

# Calculate appropriate date breaks
date_range_years <- as.numeric(difftime(max(data$date_received), 
                                        min(data$date_received), 
                                        units = "days")) / 365.25

if(date_range_years > 2) {{
  date_labels <- "%Y"
  date_breaks <- "1 year"
}} else {{
  date_labels <- "%b %Y"
  date_breaks <- "3 months"
}}

ggplot(brand_cumulative, aes(x = date_received, y = cumulative, color = brand_label)) +
  geom_line(linewidth = 1.2) +
  scale_color_brewer(palette = "BrBG") +
  scale_x_date(date_labels = date_labels, date_breaks = date_breaks) +
  scale_y_continuous(labels = comma, breaks = pretty_breaks()) +
  labs(
    title = "Cumulative Reports by Device Brand",
    x = "Date Received",
    y = "Cumulative Reports",
    color = "Brand Name",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(legend.position = "right")
```

# Technical Appendix

## Data Source

- **Database**: OpenFDA Medical Device Adverse Events
- **API Access**: [https://open.fda.gov/apis/device/event/](https://open.fda.gov/apis/device/event/)

## Analysis Tools

- **Python 3.x** with pandas and rapidfuzz for data processing
- **R** with tidyverse, ggplot2, and lubridate for visualization
- **Fuzzy Matching**: RapidFuzz library for text standardization
- **Visualization**: ggplot2 with custom base R theme
- **Report Generation**: Quarto for reproducible analytics

## Exclusion Criteria

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

## Report Metadata

- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Dataset Version**: {stats['date_range_end']}
- **Total Records Analyzed**: {stats['total_reports']:,}
- **Analysis Pipeline**: OpenFDA Medical Device Adverse Event Analysis v2.1
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