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
    ANALYSIS_THRESHOLD = 0.80  # 80% of data for analysis
    TOP_N_PROBLEMS = 20  # Fallback if needed
    TOP_N_BRANDS = 5     # Fallback if needed
    
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
  medstata-typst: default
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

## Data Standardization and Fuzzy Matching

The analysis employs fuzzy matching algorithms to standardize manufacturer and brand names, addressing inconsistencies in naming conventions across reports. FDA MAUDE reports often contain variations in manufacturer and brand name spelling, capitalization, and formatting (e.g., "MEDTRONIC INC", "Medtronic Inc.", "MEDTRONIC").

**Fuzzy String Matching Approach**: Textually similar names are identified and grouped using the Levenshtein distance algorithm, which calculates the minimum number of single-character edits needed to transform one string into another. This standardization process uses the **RapidFuzz** library with partial ratio matching.

**Matching Thresholds**: Manufacturer names with ≥65% similarity and brand names with ≥75% similarity are consolidated under a canonical representation (typically the shortest variant). This reduces artificial fragmentation in the data and provides more accurate reporting volume estimates per manufacturer and brand.

## Problem Classification and Data Quality Filters

Patient and product problems are extracted and categorized, excluding non-informative categories to focus on meaningful data patterns.

**Key Considerations:**

- Individual reports may list multiple product problems per incident
- Individual reports may list multiple patient problems per incident
- Total problem occurrences can exceed the total number of reports
- Each problem occurrence is counted separately to identify the most frequent failure modes and issues

Non-informative categories are excluded from both patient and product problem analyses. For the complete list of excluded categories, see @sec-exclusion-criteria in the Technical Appendix.

## 80% Concentration Analysis

This analysis employs a concentration-based approach to identify the critical few problems, manufacturers, and brands that account for the majority of occurrences. Rather than arbitrarily selecting a fixed number (e.g., "top 10"), we dynamically identify categories that collectively represent approximately 80% of all reported occurrences.

**Implementation**: For each category (problems, manufacturers, brands), items are ranked by frequency and cumulative percentages calculated. Items are included in the main analysis if the previous item's cumulative percentage was below 80%. This ensures complete categories are included—no category is split between the main analysis and "Other".

**Key Features**: The exact percentage may exceed 80% to maintain category integrity. All categories meeting the threshold are listed, not just a predetermined number. The "Other" category provides perspective on the long-tail distribution of remaining items.

## Statistical Analysis of Temporal Trends

**Variability Metrics**: Standard Deviation (SD) measures the typical spread of monthly reports around the average. Coefficient of Variation (CV) expresses SD as a percentage of the mean (CV = SD/Mean × 100), enabling relative comparison. CV < 15% indicates low variability, 15-30% moderate, and >30% high variability in reporting patterns.

**Outlier Detection**: Z-scores measure how many standard deviations each month's report count deviates from the mean. Months with z-scores ≥ |2| are flagged as statistically significant outliers (p < 0.05), indicating unusually high (peaks) or low (valleys) reporting activity beyond approximately 95% of normal distribution.

```{{=typst}}
#set page(
  flipped: true,
)
```

# Temporal Trend Analysis

## Overall Reporting Trends

```{{r temporal-analysis}}
#| label: fig-temporal-trends
#| fig-cap: "Monthly trend of FDA MAUDE reports"
#| fig-width: 10
#| fig-height: 5

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
  geom_line(color = colors$primary, linewidth = 1, alpha = 0.3) +
  geom_point(color = colors$primary, size = 1, alpha = 0.3) +
  geom_smooth(
    method = "loess", 
    se = TRUE, 
    color = colors$primary, 
    fill = colors$accent, 
    alpha = 0.2
  ) +
  scale_x_date(date_breaks = date_breaks, date_labels = date_labels) +
  scale_y_continuous(breaks = pretty_breaks()) +
  labs(
    subtitle = paste(format(date_min, "%B %Y"), "-", format(date_max, "%B %Y")),
    x = "Month",
    y = "Number of Reports",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

```{{r compute-trend-stats}}
#| echo: false

# Statistical analysis for peak detection
mean_monthly <- mean(monthly_plot_data$n)
sd_monthly <- sd(monthly_plot_data$n)

# Calculate z-scores for each month
monthly_plot_data <- monthly_plot_data %>%
  mutate(
    z_score = (n - mean_monthly) / sd_monthly,
    deviation = n - mean_monthly,
    is_significant = abs(z_score) >= 2  # 95% confidence level (2 standard deviations)
  )

# Identify statistically significant peaks (positive outliers)
significant_peaks <- monthly_plot_data %>%
  filter(z_score >= 2) %>%  # Above 2 standard deviations (p < 0.05)
  arrange(desc(z_score)) %>%
  mutate(
    month_label = format(year_month, "%B %Y"),
    z_score_rounded = round(z_score, 2),
    deviation_pct = round(100 * deviation / mean_monthly, 1)
  )

# Identify statistically significant valleys (negative outliers)
significant_valleys <- monthly_plot_data %>%
  filter(z_score <= -2) %>%
  arrange(z_score) %>%
  mutate(
    month_label = format(year_month, "%B %Y"),
    z_score_rounded = round(abs(z_score), 2),
    deviation_pct = round(100 * abs(deviation) / mean_monthly, 1)
  )

n_significant_peaks <- nrow(significant_peaks)
n_significant_valleys <- nrow(significant_valleys)

# Format peak and valley lists
if(n_significant_peaks > 0) {{
  peak_details <- significant_peaks %>%
    mutate(detail = sprintf("%s (%s reports, z=%.2f, +%s%%)", 
                           month_label, 
                           format(n, big.mark = ","),
                           z_score_rounded,
                           deviation_pct)) %>%
    pull(detail)
  peak_list <- paste(peak_details, collapse = "; ")
}} else {{
  peak_list <- "None detected"
}}

if(n_significant_valleys > 0) {{
  valley_details <- significant_valleys %>%
    mutate(detail = sprintf("%s (%s reports, z=%.2f, -%s%%)", 
                           month_label, 
                           format(n, big.mark = ","),
                           z_score_rounded,
                           deviation_pct)) %>%
    pull(detail)
  valley_list <- paste(valley_details, collapse = "; ")
}} else {{
  valley_list <- "None detected"
}}

sd_monthly_rounded <- round(sd_monthly, 1)
cv <- round(100 * sd_monthly / mean_monthly, 1)  # Coefficient of variation
```
```{{=typst}}
#set page(
  flipped: false,
)
```


## Statistical Trend Analysis

**Reporting Variability:** The average monthly reporting rate is **`r avg_monthly_reports`** reports (SD = **`r sd_monthly_rounded`**, CV = **`r cv`%**).

**Statistically Significant Peaks** (≥2 SD above mean, p < 0.05):

```{{r peaks-bullets}}
#| echo: false
#| results: asis

if(n_significant_peaks > 0) {{
  cat(sprintf("\n%d month(s) identified:\n\n", n_significant_peaks))
  for(i in 1:nrow(significant_peaks)) {{
    cat(sprintf("- **%s**: %s reports (z=%.2f, +%s%%)\n",
                significant_peaks$month_label[i],
                format(significant_peaks$n[i], big.mark = ","),
                significant_peaks$z_score_rounded[i],
                significant_peaks$deviation_pct[i]))
  }}
}} else {{
  cat("\nNo statistically significant peaks detected at 95% confidence level.\n")
}}
```

**Statistically Significant Valleys** (≥2 SD below mean, p < 0.05):

```{{r valleys-bullets}}
#| echo: false
#| results: asis

if(n_significant_valleys > 0) {{
  cat(sprintf("\n%d month(s) identified:\n\n", n_significant_valleys))
  for(i in 1:nrow(significant_valleys)) {{
    cat(sprintf("- **%s**: %s reports (z=%.2f, -%s%%)\n",
                significant_valleys$month_label[i],
                format(significant_valleys$n[i], big.mark = ","),
                significant_valleys$z_score_rounded[i],
                significant_valleys$deviation_pct[i]))
  }}
}} else {{
  cat("\nNo statistically significant valleys detected at 95% confidence level.\n")
}}
```


```{{=typst}}
#set page(
  flipped: true,
)
```

## Cumulative Reports Over Time



```{{r cumulative-plot}}
#| label: fig-cumulative-reports
#| fig-cap: "Cumulative FDA MAUDE reports over time"
#| fig-width: 10
#| fig-height: 5

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
  geom_point(color = colors$primary, size = 0.5, shape = 4, alpha = 0.3) +
  scale_x_date(date_breaks = date_breaks, date_labels = date_labels) +
  scale_y_continuous(breaks = pretty_breaks(n = 10)) +
  labs(
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

# Get all product problems sorted by frequency
product_problems_all <- tibble(problems = product_problems_vector) %>%
  filter(
    !is.na(problems) &
    problems != "" &
    !problems %in% PRODUCT_EXCLUSIONS
  ) %>%
  count(problems, sort = TRUE)

total_all_product_problems <- sum(product_problems_all$n)

# Calculate cumulative percentage for 80% analysis
product_problems_all <- product_problems_all %>%
  mutate(
    cumulative_n = cumsum(n),
    cumulative_pct = cumulative_n / total_all_product_problems
  )

# Get items that account for 80% of data
# Use lag to check if previous row was < 0.80, ensuring we include the item that crosses 80%
product_problems_80 <- product_problems_all %>%
  mutate(prev_pct = lag(cumulative_pct, default = 0)) %>%
  filter(prev_pct < 0.80) %>%
  select(-prev_pct)

# Ensure we have at least one item
if(nrow(product_problems_80) == 0) {{
  product_problems_80 <- product_problems_all %>% slice_head(n = 1)
}}

# Calculate "Other" category
other_problems_n <- total_all_product_problems - sum(product_problems_80$n)

# Add "Other" row for plotting
product_problems_plot <- product_problems_80 %>%
  bind_rows(tibble(problems = "Other", n = other_problems_n)) %>%
  mutate(problems = factor(problems, levels = c("Other", rev(product_problems_80$problems))))

n_80_problems <- nrow(product_problems_80)
total_80_product_problems <- sum(product_problems_80$n)
pct_80 <- round(100 * total_80_product_problems / total_all_product_problems, 1)
other_pct <- round(100 * other_problems_n / total_all_product_problems, 1)
```

## Product Problems Analysis

```{{r product-problems-plot}}
#| label: fig-product-problems
#| fig-cap: !expr sprintf("Product problems representing approximately 80%% of problem occurrences (%s%%), plus 'Other' category", pct_80)
#| fig-width: 8
#| fig-height: !expr max(10, (n_80_problems + 1) * 0.4)

ggplot(product_problems_plot, aes(x = problems, y = n)) +
  geom_col(aes(fill = problems == "Other"), alpha = 0.8, show.legend = FALSE) +
  scale_fill_manual(values = c("FALSE" = colors$highlight, "TRUE" = "gray70")) +
  geom_text(aes(label = n), hjust = -0.2, size = 3.5) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(
    subtitle = paste0("(", format(date_min, "%B %Y"), 
                     " - ", format(date_max, "%B %Y"), ")"),
    x = "Product Problem",
    y = "Number of Occurrences",
    caption = "Source: FDA MAUDE Database | Note: Reports may contain multiple problems"
  ) +
  theme(axis.text.y = element_text(size = 8))
```

A total of **`r n_80_problems`** product problem type(s) account for **`r pct_80`%** of all reported problem occurrences (**`r format(total_80_product_problems, big.mark = ",")`** occurrences).

The remaining **`r format(other_problems_n, big.mark = ",")`** problem occurrences (**`r other_pct`%**) are categorized as "Other".

**All Product Problems Representing `r pct_80`% of Data:**

```{{r all-product-table}}
#| echo: false
#| results: asis

all_80_product <- product_problems_80 %>%
  mutate(
    pct = sprintf("%.1f%%", 100 * n / total_all_product_problems)
  )

for(i in 1:nrow(all_80_product)) {{
  cat(sprintf("%d. **%s** - %s occurrences (%s)\n", 
              i, 
              all_80_product$problems[i], 
              format(all_80_product$n[i], big.mark = ","),
              all_80_product$pct[i]))
}}
```

# Patient Problem Analysis

```{{r compute-patient-problems}}
#| echo: false

# Extract and count patient problems
patient_problems_vector <- parse_problem_lists(data$patient_problems)

# Get all patient problems sorted by frequency
patient_problems_all <- tibble(problems = patient_problems_vector) %>%
  filter(
    !is.na(problems) &
    problems != "" &
    !problems %in% PATIENT_EXCLUSIONS
  ) %>%
  count(problems, sort = TRUE)

total_all_patient_problems <- sum(patient_problems_all$n)

# Calculate cumulative percentage for 80% analysis
patient_problems_all <- patient_problems_all %>%
  mutate(
    cumulative_n = cumsum(n),
    cumulative_pct = cumulative_n / total_all_patient_problems
  )

# Get items that account for 80% of data
# Use lag to check if previous row was < 0.80, ensuring we include the item that crosses 80%
patient_problems_80 <- patient_problems_all %>%
  mutate(prev_pct = lag(cumulative_pct, default = 0)) %>%
  filter(prev_pct < 0.80) %>%
  select(-prev_pct)

# Ensure we have at least one item
if(nrow(patient_problems_80) == 0) {{
  patient_problems_80 <- patient_problems_all %>% slice_head(n = 1)
}}

# Calculate "Other" category
other_patient_problems_n <- total_all_patient_problems - sum(patient_problems_80$n)

# Add "Other" row for plotting
patient_problems_plot <- patient_problems_80 %>%
  bind_rows(tibble(problems = "Other", n = other_patient_problems_n)) %>%
  mutate(problems = factor(problems, levels = c("Other", rev(patient_problems_80$problems))))

n_80_patient_problems <- nrow(patient_problems_80)
total_80_patient_problems <- sum(patient_problems_80$n)
pct_80_patient <- round(100 * total_80_patient_problems / total_all_patient_problems, 1)
other_patient_pct <- round(100 * other_patient_problems_n / total_all_patient_problems, 1)
```

## Patient Problems Analysis

```{{r patient-problems-plot}}
#| label: fig-patient-problems
#| fig-cap: !expr sprintf("Patient problems representing approximately 80%% of problem occurrences (%s%%), plus 'Other' category", pct_80_patient)
#| fig-width: 8
#| fig-height: !expr max(10, (n_80_patient_problems + 1) * 0.4)

ggplot(patient_problems_plot, aes(x = problems, y = n)) +
  geom_col(aes(fill = problems == "Other"), alpha = 0.8, show.legend = FALSE) +
  scale_fill_manual(values = c("FALSE" = colors$info, "TRUE" = "gray70")) +
  geom_text(aes(label = n), hjust = -0.2, size = 3.5) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  labs(
    subtitle = "Clinical outcomes and adverse events",
    x = "Patient Problem",
    y = "Number of Occurrences",
    caption = "Source: FDA MAUDE Database | Note: Reports may contain multiple problems"
  ) +
  theme(axis.text.y = element_text(size = 8))
```

A total of **`r n_80_patient_problems`** patient problem type(s) account for **`r pct_80_patient`%** of all reported patient problem occurrences (**`r format(total_80_patient_problems, big.mark = ",")`** occurrences).

The remaining **`r format(other_patient_problems_n, big.mark = ",")`** problem occurrences (**`r other_patient_pct`%**) are categorized as "Other".

**All Patient Problems Representing `r pct_80_patient`% of Data:**

```{{r all-patient-table}}
#| echo: false
#| results: asis

all_80_patient <- patient_problems_80 %>%
  mutate(
    pct = sprintf("%.1f%%", 100 * n / total_all_patient_problems)
  )

for(i in 1:nrow(all_80_patient)) {{
  cat(sprintf("%d. **%s** - %s occurrences (%s)\n", 
              i, 
              all_80_patient$problems[i], 
              format(all_80_patient$n[i], big.mark = ","),
              all_80_patient$pct[i]))
}}
```

# Manufacturer Analysis

## Top Manufacturers

```{{r compute-manufacturers}}
#| echo: false

# Calculate manufacturer statistics with 80% analysis
manufacturers_all <- data %>%
  count(manufacturer_std, sort = TRUE)

total_all_manufacturers <- sum(manufacturers_all$n)

manufacturers_all <- manufacturers_all %>%
  mutate(
    cumulative_n = cumsum(n),
    cumulative_pct = cumulative_n / total_all_manufacturers
  )

# Get manufacturers that account for 80% of data
# Use lag to check if previous row was < 0.80, ensuring we include the manufacturer that crosses 80%
manufacturers_80 <- manufacturers_all %>%
  mutate(prev_pct = lag(cumulative_pct, default = 0)) %>%
  filter(prev_pct < 0.80) %>%
  select(-prev_pct)

# Ensure we have at least one manufacturer
if(nrow(manufacturers_80) == 0) {{
  manufacturers_80 <- manufacturers_all %>% slice_head(n = 1)
}}

# Calculate "Other" category
other_manufacturers_n <- total_all_manufacturers - sum(manufacturers_80$n)

# Add "Other" row for plotting
top_manufacturers <- manufacturers_80 %>%
  bind_rows(tibble(manufacturer_std = "Other", n = other_manufacturers_n)) %>%
  mutate(manufacturer_std = factor(manufacturer_std, levels = c("Other", rev(manufacturers_80$manufacturer_std))))

n_80_manufacturers <- nrow(manufacturers_80)
total_80_manufacturer_reports <- sum(manufacturers_80$n)
pct_80_manufacturer <- round(100 * total_80_manufacturer_reports / total_reports, 1)
other_manufacturer_pct <- round(100 * other_manufacturers_n / total_reports, 1)

top_manufacturer <- manufacturers_80$manufacturer_std[1]
top_manufacturer_count <- manufacturers_80$n[1]
top_manufacturer_pct <- round(100 * top_manufacturer_count / total_reports, 1)

# Table data (without Other)
manufacturers_table_data <- manufacturers_80
```

```{{r manufacturer-plot}}
#| label: fig-manufacturers
#| fig-cap: !expr sprintf("Manufacturers representing approximately 80%% of reports (%s%%), plus 'Other' category", pct_80_manufacturer)
#| fig-width: 8
#| fig-height: !expr max(6.5, (n_80_manufacturers + 1) * 0.35)

ggplot(top_manufacturers, aes(x = manufacturer_std, y = n)) +
  geom_col(aes(fill = manufacturer_std == "Other"), alpha = 0.8, show.legend = FALSE) +
  scale_fill_manual(values = c("FALSE" = colors$secondary, "TRUE" = "gray70")) +
  geom_text(aes(label = n), hjust = -0.2, size = 3.5) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(
    x = "Manufacturer",
    y = "Number of Reports",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(axis.text.y = element_text(size = 8))
```

A total of **`r n_80_manufacturers`** manufacturer(s) account for **`r pct_80_manufacturer`%** of all reports (**`r format(total_80_manufacturer_reports, big.mark = ",")`** reports).

The remaining **`r format(other_manufacturers_n, big.mark = ",")`** reports (**`r other_manufacturer_pct`%**) are from other manufacturers.

The top manufacturer, **`r top_manufacturer`**, accounts for **`r format(top_manufacturer_count, big.mark = ",")`** reports (**`r top_manufacturer_pct`%** of total).

```{{r manufacturer-table}}
#| label: tbl-manufacturers
#| tbl-cap: !expr sprintf("Manufacturer(s) representing %s%% of reports", pct_80_manufacturer)

manufacturer_table <- manufacturers_table_data %>%
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



```{{r compute-brands}}
#| echo: false

# Calculate brand statistics with 80% analysis
brands_all <- data %>%
  count(brand_std, sort = TRUE)

total_all_brands <- sum(brands_all$n)

brands_all <- brands_all %>%
  mutate(
    cumulative_n = cumsum(n),
    cumulative_pct = cumulative_n / total_all_brands
  )

# Get brands that account for 80% of data
# Use lag to check if previous row was < 0.80, ensuring we include the brand that crosses 80%
brands_80 <- brands_all %>%
  mutate(prev_pct = lag(cumulative_pct, default = 0)) %>%
  filter(prev_pct < 0.80) %>%
  select(-prev_pct)

# Ensure we have at least one brand
if(nrow(brands_80) == 0) {{
  brands_80 <- brands_all %>% slice_head(n = 1)
}}

# Calculate "Other" category
other_brands_n <- total_all_brands - sum(brands_80$n)

# Add "Other" row for plotting
top_brands <- brands_80 %>%
  bind_rows(tibble(brand_std = "Other", n = other_brands_n)) %>%
  mutate(brand_std = factor(brand_std, levels = c("Other", rev(brands_80$brand_std))))

n_80_brands <- nrow(brands_80)
total_80_brand_reports <- sum(brands_80$n)
pct_80_brand <- round(100 * total_80_brand_reports / total_reports, 1)
other_brand_pct <- round(100 * other_brands_n / total_reports, 1)

# Keep top 5 for cumulative analysis
top_5_brands <- brands_80 %>% head(5)

top_brand <- brands_80$brand_std[1]
top_brand_count <- brands_80$n[1]
top_brand_pct <- round(100 * top_brand_count / total_reports, 1)

# Table data (without Other)
brands_table_data <- brands_80
```



```{{r brand-plot}}
#| label: fig-brands
#| fig-cap: !expr sprintf("Device brands representing approximately 80%% of reports (%s%%), plus 'Other' category", pct_80_brand)
#| fig-width: 10
#| fig-height: !expr max(6, (n_80_brands + 1) * 0.35)

ggplot(top_brands, aes(x = brand_std, y = n)) +
  geom_col(aes(fill = brand_std == "Other"), alpha = 0.8, show.legend = FALSE) +
  scale_fill_manual(values = c("FALSE" = colors$primary, "TRUE" = "gray70")) +
  geom_text(aes(label = n), hjust = -0.3, size = 3.5) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.1))) +
  labs(
    x = "Brand",
    y = "Number of Reports",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(axis.text.y = element_text(size = 7))
```



A total of **`r n_80_brands`** device brand(s) account for **`r pct_80_brand`%** of all reports (**`r format(total_80_brand_reports, big.mark = ",")`** reports).

The remaining **`r format(other_brands_n, big.mark = ",")`** reports (**`r other_brand_pct`%**) are from other brands.

The top device brand, **`r top_brand`**, accounts for **`r format(top_brand_count, big.mark = ",")`** reports (**`r top_brand_pct`%** of total).

```{{=typst}}
#set page(
  flipped: false,
)
```

```{{r brand-table}}
#| label: tbl-brands
#| tbl-cap: !expr sprintf("Device brand(s) representing %s%% of reports", pct_80_brand)

brand_table <- brands_table_data %>%
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
    x = "Date Received",
    y = "Cumulative Reports",
    color = "Brand Name",
    caption = "Source: FDA MAUDE Database"
  ) +
  theme(
    legend.position = c(0.02, 0.98),
    legend.justification = c(0, 1),
    legend.background = element_rect(fill = "white", color = "black", linewidth = 0.3),
    legend.margin = margin(4, 6, 4, 6)
  )
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

## Exclusion Criteria {{#sec-exclusion-criteria}}

**Patient Problems Excluded:**

- No Code Available
- No Known Impact Or Consequence To Patient
- Symptoms or Conditions
- No Information
- No Consequences Or Impact To Patient
- Appropriate Clinical Signs
- No Clinical Signs
- Conditions Term / Code Not Available
- Appropriate Term / Code Not Available
- Insufficient Information
- No Patient Involvement
- Reaction
- Patient Problem/Medical Problem

**Product Problems Excluded:**

- Adverse Event Without Identified Device or Use Problem
- Appropriate Term/Code Not Available
- Appropriate Term / Code Not Available
- Unknown (for use when the device problem is not known)
- Insufficient Information
- No Apparent Adverse Event

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