"""
OpenFDA Medical Device Adverse Event Analysis
Refactored for modularity and functional programming principles
"""

import pandas as pd
from collections import Counter
import re
from rapidfuzz import fuzz
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from typing import List, Dict, Tuple, Optional


# =========================================================
# CONFIGURATION
# =========================================================
class Config:
    """Centralized configuration"""
    DATA_PATH = "saved_csv/event_data.csv"
    OUTPUT_DIR = Path("./plots")
    DELIMITER = "|"
    
    # Thresholds
    MANUFACTURER_THRESHOLD = 65
    BRAND_THRESHOLD = 75
    
    # Display settings
    FONT_FAMILY = "Arial"
    FONT_SIZE = 12
    TITLE_FONT_SIZE = 16
    PLOT_HEIGHT = 600
    LINE_WIDTH = 3
    
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
    # Normalize all values
    cleaned = series.fillna("").astype(str).apply(normalize_text)
    
    # Get unique values and group them
    uniques = cleaned.unique()
    groups = fuzzy_group(uniques, threshold)
    
    # Create mapping (shortest name in each group becomes canonical)
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
# PROBLEM LIST PARSING
# =========================================================
def parse_problem_lists(series: pd.Series) -> List[str]:
    """Parse problem lists from string representation"""
    problems = []
    for item in series:
        if isinstance(item, str):
            parsed = item.strip('][').replace("'", "").split(', ')
            problems.extend(parsed)
    return problems


def create_problem_dataframe(problems: List[str], 
                             exclusions: List[str],
                             top_n: int = 20) -> pd.DataFrame:
    """Create and filter problem frequency dataframe"""
    # Count frequencies
    counts = Counter(problems)
    df = pd.DataFrame.from_dict(counts, orient='index', columns=['n'])
    
    # Filter exclusions
    df = df[~df.index.isin(exclusions)]
    
    # Get top N and sort
    df = df.nlargest(top_n, 'n').sort_values(by='n')
    df = df.reset_index().rename(columns={'index': 'problem'})
    
    return df


# =========================================================
# PLOTTING UTILITIES
# =========================================================
def create_bar_chart(df: pd.DataFrame, 
                     x: str, 
                     y: str,
                     title: str,
                     color: str = "lightgray",
                     orientation: str = 'h') -> go.Figure:
    """Create a styled bar chart"""
    fig = px.bar(
        df,
        x=x if orientation == 'h' else y,
        y=y if orientation == 'h' else x,
        orientation=orientation,
        template="simple_white",
        title=title
    )
    
    fig.update_traces(
        marker_line_color="black", 
        marker_line_width=1, 
        marker_color=color
    )
    
    fig.update_layout(font_family=Config.FONT_FAMILY)
    
    return fig


def shorten_brand_name(brand: str, max_words: int = 4) -> str:
    """Create shorter, more readable brand labels"""
    words = brand.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words])
    return brand


def save_plot(fig: go.Figure, filename: str, auto_open: bool = False):
    """Save plot to output directory"""
    output_path = Config.OUTPUT_DIR / filename
    fig.write_html(str(output_path), auto_open=auto_open)
    print(f"✓ Saved plot: {output_path}")


# =========================================================
# VISUALIZATION FUNCTIONS
# =========================================================
def plot_manufacturer_brand(df: pd.DataFrame, auto_open: bool = False):
    """Plot manufacturer vs brand distribution"""
    fig = px.bar(
        df,
        x="manufacturer_std",
        color="brand_std",
        color_discrete_sequence=px.colors.sequential.Cividis,
        template="simple_white",
        title=f"OpenFDA Standardized Manufacturer and Brand Names ({len(df):,} reports)"
    )
    
    fig.update_traces(marker_line_color="black", marker_line_width=1)
    fig.update_layout(font_family=Config.FONT_FAMILY)
    
    save_plot(fig, "manufacturer_brand_standardized.html", auto_open)


def plot_patient_problems(df: pd.DataFrame, auto_open: bool = False):
    """Plot top patient problems"""
    problems = parse_problem_lists(df["patient_problems"])
    problem_df = create_problem_dataframe(
        problems, 
        Config.PATIENT_EXCLUSIONS, 
        top_n=20
    )
    
    fig = create_bar_chart(
        problem_df,
        x='n',
        y='problem',
        title=f"OpenFDA Patient Problems ({len(df):,} reports)",
        orientation='h'
    )
    
    fig.update_layout(yaxis_title="", xaxis_title="Number of Reports")
    
    save_plot(fig, "patient_problems.html", auto_open)


def plot_product_problems(df: pd.DataFrame, auto_open: bool = False):
    """Plot top product problems"""
    problems = parse_problem_lists(df["product_problems"])
    problem_df = create_problem_dataframe(
        problems, 
        Config.PRODUCT_EXCLUSIONS, 
        top_n=21
    )
    
    fig = create_bar_chart(
        problem_df,
        x='n',
        y='problem',
        title=f"OpenFDA Product Problems ({len(df):,} reports)",
        orientation='h'
    )
    
    fig.update_layout(yaxis_title="", xaxis_title="Number of Reports")
    
    save_plot(fig, "product_problems.html", auto_open)


def plot_cumulative_reports(df: pd.DataFrame, 
                           top_n: int = 5, 
                           log_scale: bool = False,
                           auto_open: bool = False):
    """Plot cumulative reports over time for top brands"""
    # Prepare data
    df = df.copy()
    
    # Convert date only if not already datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date_received']):
        df['date_received'] = pd.to_datetime(df['date_received'].astype(str), format='%Y%m%d')
    
    # Get top N brands
    top_brands = df['brand_std'].value_counts().nlargest(top_n).index.tolist()
    
    print(f"\n✓ Top {top_n} brands by report volume:")
    for i, (brand, count) in enumerate(df['brand_std'].value_counts().head(top_n).items(), 1):
        print(f"  {i}. {brand}: {count:,} reports")
    
    # Filter and compute cumulative
    df_top = df[df['brand_std'].isin(top_brands)].copy()
    df_top = df_top.sort_values(['brand_std', 'date_received'])
    df_top['cumulative'] = df_top.groupby('brand_std').cumcount() + 1
    
    # Create readable labels
    label_map = {brand: shorten_brand_name(brand).title() 
                 for brand in df_top['brand_std'].unique()}
    df_top['brand_label'] = df_top['brand_std'].map(label_map)
    
    # Create plot
    title_suffix = " (Log Scale)" if log_scale else ""
    fig = px.line(
        df_top,
        x='date_received',
        y='cumulative',
        color='brand_label',
        title=f'Cumulative Adverse Event Reports by Medical Device Brand{title_suffix}',
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Bold,
        log_y=log_scale
    )
    
    # Style updates
    fig.update_layout(
        xaxis_title="Date Received",
        yaxis_title=f"Cumulative Reports{' (log scale)' if log_scale else ''}",
        legend_title="Brand Name",
        font=dict(size=Config.FONT_SIZE, family=Config.FONT_FAMILY),
        title_font=dict(size=Config.TITLE_FONT_SIZE, family=Config.FONT_FAMILY),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="gray",
            borderwidth=1
        ),
        hovermode='x unified',
        height=Config.PLOT_HEIGHT,
        margin=dict(r=150)
    )
    
    fig.update_traces(
        line=dict(width=Config.LINE_WIDTH),
        hovertemplate='<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Reports: %{y}<extra></extra>'
    )
    
    fig.update_xaxes(rangeslider_visible=True)
    
    filename = "cumulative_reports_log.html" if log_scale else "cumulative_reports.html"
    save_plot(fig, filename, auto_open)


def print_summary_statistics(df: pd.DataFrame):
    """Print summary statistics of the dataset"""
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"Total Reports: {len(df):,}")
    print(f"Date Range: {df['date_received'].min()} to {df['date_received'].max()}")
    print(f"Unique Manufacturers: {df['manufacturer_std'].nunique():,}")
    print(f"Unique Brands: {df['brand_std'].nunique():,}")
    print(f"\nTop 5 Manufacturers:")
    for i, (mfr, count) in enumerate(df['manufacturer_std'].value_counts().head(5).items(), 1):
        print(f"  {i}. {mfr}: {count:,} reports")
    print(f"\nTop 5 Brands:")
    for i, (brand, count) in enumerate(df['brand_std'].value_counts().head(5).items(), 1):
        print(f"  {i}. {brand}: {count:,} reports")
    print("="*60 + "\n")


# =========================================================
# MAIN PIPELINE
# =========================================================
def run_analysis(data_path: str = Config.DATA_PATH, 
                 auto_open: bool = False,
                 create_log_plot: bool = True):
    """Run complete analysis pipeline"""
    print("\n" + "="*60)
    print("STARTING FDA ADVERSE EVENT ANALYSIS")
    print("="*60 + "\n")
    
    # Load and prepare data
    df = load_data(data_path, Config.DELIMITER)
    df = add_standardized_columns(
        df, 
        Config.MANUFACTURER_THRESHOLD, 
        Config.BRAND_THRESHOLD
    )
    
    # Convert date once for all subsequent operations
    if 'date_received' in df.columns:
        df['date_received'] = pd.to_datetime(df['date_received'].astype(str), format='%Y%m%d')
        print(f"✓ Converted date_received to datetime format")
    
    # Print statistics
    print_summary_statistics(df)
    
    # Generate all plots
    print("Generating visualizations...")
    plot_manufacturer_brand(df, auto_open)
    plot_patient_problems(df, auto_open)
    plot_product_problems(df, auto_open)
    plot_cumulative_reports(df, top_n=5, log_scale=False, auto_open=auto_open)
    
    if create_log_plot:
        plot_cumulative_reports(df, top_n=5, log_scale=True, auto_open=auto_open)
    
    print("\n" + "="*60)
    print("✓ ANALYSIS COMPLETE")
    print("="*60 + "\n")
    
    return df


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    # Run the complete analysis
    analyzed_data = run_analysis(auto_open=False, create_log_plot=True)
    
    # Optional: Save standardized data
    # analyzed_data.to_csv("saved_csv/event_data_standardized.csv", sep="|", index=False)
    # print("✓ Saved standardized data")

# open all html plots in plots folder using plotly in default browser
import webbrowser
import os

plots_path = Config.OUTPUT_DIR
for file in os.listdir(plots_path):
    if file.endswith(".html"):
        webbrowser.open_new_tab(os.path.join(plots_path, file))
