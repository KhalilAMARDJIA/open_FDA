// ============================================================================
// MEDSTATA TYPST TEMPLATE
// Professional Medical Device Report Template
// ============================================================================
//
// This template provides a comprehensive layout for medical device reports,
// clinical evaluation reports, and regulatory documentation.
//
// Features:
// - Custom branded cover page with version control
// - Automated table of contents with hierarchical styling
// - List of figures and tables
// - Professional color scheme with customizable branding
// - Responsive table styling with alternating row colors
// - Cross-reference support with custom styling
// - Multi-level heading hierarchy
// ============================================================================

// ============================================================================
// COLOR PALETTE CONFIGURATION
// ============================================================================

// Base colors
#let dark_blue = rgb(0, 85, 165)
#let light_blue = dark_blue.lighten(90%).desaturate(10%).rotate(270deg)

// Theme colors - customize these to match your brand
#let main_color = light_blue              // Primary background and accents
#let secondary_color = dark_blue          // Headers and emphasis
#let accent_color = rgb("#09c482")        // Highlights and interactive elements
#let cover_page_color = main_color.rotate(180deg).rotate(180deg).desaturate(50%)

// Text colors
#let dark_text = rgb(15, 10, 10)          // Body text
#let cover_page_text = main_color.negate().saturate(10%).rotate(180deg)
#let cover_page_line = cover_page_color.saturate(99%).rotate(180deg).negate().transparentize(50%)

// ============================================================================
// FONT CONFIGURATION
// ============================================================================

#let main_fonts = ("Latin Modern Roman 12","IBM Plex Serif","CMU Concrete", "STIX Two Text")  // Body text fonts
#let secondary_fonts = "IBM Plex Sans"              // Headers and UI elements
#let code_fonts = ("Iosevka NFM", "IBM Plex Mono", "Latin Modern Mono")                     // Code blocks

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/// Version box component
/// Displays version information with styled background
///
/// Parameters:
/// - body: Content to display (typically version number)
#let version_box(body) = {
  box(
    fill: main_color.lighten(90%),
    inset: 0.1em,
    outset: 0.1em,
    stroke: (paint: main_color, thickness: 0.3pt, dash: "solid"),
    radius: 0.3em,
    body,
  )
}

/// Blockquote styling
/// Creates a styled quote block with left border accent
///
/// Parameters:
/// - body: Quote content to display
#let blockquote(body) = {
  block(
    width: 100%,
    fill: dark_blue.lighten(95%),
    inset: (top: 1em, bottom: 1em, left: -3em, right: -3em),
    outset: (top: 0em, bottom: 0em, left: 3em, right: 3em),
    radius: 0.3em,
    stroke: (
      left: (paint: dark_blue, thickness: 3pt, dash: "solid"),
    ),
    body,
  )
}

// Apply blockquote styling to all quote elements
#show quote: it => {
  blockquote(
    text(
      it,
      size: 0.9em,
      weight: 300,
      font: secondary_fonts,
      fill: dark_text,
    ),
  )
}

// ============================================================================
// MAIN REPORT FUNCTION
// ============================================================================

/// Main report template function
///
/// Parameters:
/// - title: Report title (required)
/// - subtitle: Report subtitle (optional)
/// - author: Author name(s) (required)
/// - logo: Path to logo image (optional)
/// - date: Report date (optional, defaults to current date)
/// - version: Version number (optional)
/// - bibliography: Bibliography file path (optional)
/// - lof: Display list of figures (boolean, default: false)
/// - lot: Display list of tables (boolean, default: false)
/// - body: Main document content (required)
#let report(
  title: [Add title],
  subtitle: none,
  author: [Add author],
  logo: none,
  date: none,
  version: none,
  bibliography: none,
  lof: false,
  lot: false,
  body,
) = {
  // ==========================================================================
  // DOCUMENT SETUP
  // ==========================================================================

  set page(paper: "a4")
  set text(hyphenate: false)
  set par(justify: true)

  // ==========================================================================
  // COVER PAGE
  // ==========================================================================

  page(
    background: rect(fill: cover_page_color, width: 100%, height: 100%),
    margin: (top: 6em, bottom: 1em, left: 5em, right: 5em),

    // Header with logo and version
    header: grid(
      columns: (1fr, 1fr, 1fr),
      align: (left + horizon, center + horizon, right + horizon),

      // Logo (left)
      [#if logo != none {
        image(logo, height: 3em)
      }],

      // Center (empty)
      [],

      // Version (right)
      text(
        size: 1em,
        fill: cover_page_text,
        weight: 400,
        font: main_fonts,
      )[VERSION | *#version*],
    ),

    // Main cover content
    box(
      grid(
        columns: 1fr,
        rows: (2fr, 0.8fr, 0.8fr),

        // Title and subtitle section
        grid(
          columns: 1,
          gutter: 4em,

          // Title (right-aligned with right border)
          box(
            text(
              size: 1.5em,
              fill: cover_page_text,
              weight: 600,
              font: secondary_fonts,
              align(upper(title), right),
            ),
            width: 85%,
            stroke: (right: cover_page_line),
            inset: 1em,
          ),

          // Subtitle (left-aligned with left border)
          box(
            text(
              size: 1.3em,
              fill: cover_page_text,
              weight: 400,
              font: secondary_fonts,
              align(subtitle, left),
            ),
            width: 85%,
            inset: 1em,
            stroke: (left: cover_page_line),
          ),
        ),

        // Decorative gradient polygon
        [#polygon(
          fill: gradient.linear(
            accent_color,
            secondary_color.transparentize(100%),
            angle: 360deg,
          ),
          (130%, 10cm),
          (130%, 12cm),
          (0%, 8cm),
          (-10%, 9cm),
        )],

        // Author and date footer
        grid(
          columns: (1fr, 1fr, 1fr),
          align: (left, center, right),

          // Author
          text(
            size: 1.3em,
            fill: cover_page_text,
            weight: 200,
            font: main_fonts,
          )[#author],

          // Center (empty)
          [],

          // Date
          text(
            size: 1.3em,
            fill: cover_page_text,
            weight: 400,
            font: main_fonts,
          )[#date],
        ),

        align: center + horizon,
      ),
      stroke: (top: cover_page_line + 0.1em),
    ),
  )

  // ==========================================================================
  // PAGE LAYOUT AND TYPOGRAPHY
  // ==========================================================================

  // Page margins for content pages
  set page(margin: (bottom: 4cm, left: 2.5cm, right: 2.5cm, top: 2.5cm))

  // Paragraph settings
  set par(
    justify: true,
    leading: 0.6em, // Space between lines
  )
  set block(spacing: 1.5em) // Space between paragraphs

  // Text settings
  set text(
    font: main_fonts,
    size: 10pt,
    weight: 300,
    hyphenate: false,
    spacing: 100%,
  )

  // Code block styling
  show raw: set text(size: 0.8em, font: code_fonts)

  // ==========================================================================
  // FOOTER CONFIGURATION
  // ==========================================================================

  set page(
    footer: grid(
      columns: (1fr, 1fr, 1fr),
      align: (left, center, right),
      gutter: 0.5em,

      // Version box (left)
      if version != none {
        [Version: #version_box(version)]
      },

      // Center (empty)
      [],

      // Page numbering (right)
      context {
        counter(page).display("1 of 1", both: true)
      },
    ),
  )

  // ==========================================================================
  // LIST STYLING
  // ==========================================================================

  // Bullet list settings
  set list(
    tight: false,
    indent: 1.5em,
    body-indent: 1em,
    spacing: auto,
    marker: ([•], [--], [○], [‣]), // Multi-level markers
  )

  // Numbered list settings
  set enum(
    tight: false,
    indent: 1.5em,
    body-indent: 1em,
    spacing: auto,
  )

  // ==========================================================================
  // LINK AND REFERENCE STYLING
  // ==========================================================================

  // External link styling
  show link: it => [
    #h(0.3em)
    #set text(weight: "regular")
    #box(
      [#it],
      stroke: main_color + 0.04em,
      fill: main_color.lighten(90%),
      outset: 0.2em,
      radius: 0.2em,
    )
    #h(0.3em)
  ]

  // Cross-reference styling
  show ref: it => [
    #set text(weight: "regular")
    #box(
      [#it],
      stroke: (
        bottom: (paint: accent_color, thickness: 0.1em, dash: "solid"),
      ),
      fill: main_color.lighten(50%),
    )
  ]

  // ==========================================================================
  // HEADING HIERARCHY
  // ==========================================================================

  set heading(numbering: "1.1.")

  // Level 1: Main sections (large, uppercase, colored)
  show heading.where(level: 1): it => [
    #set text(
      fill: secondary_color,
      weight: 800,
      size: 1.3em,
      font: secondary_fonts,
    )
    #block(
      smallcaps(it),
      inset: (top: 0.5em, bottom: 0.5em, rest: 0em),
    )
  ]

  // Level 2: Subsections (medium, underlined, accent colored)
  show heading.where(level: 2): it => [
    #set text(
      fill: accent_color.darken(50%),
      weight: 500,
      size: 1.1em,
      font: secondary_fonts,
    )
    #block(
      underline(smallcaps(it)),
      inset: (top: 0.5em, bottom: 0.5em, rest: 0em),
    )
  ]

  // Level 3: Sub-subsections (small caps, dark blue)
  show heading.where(level: 3): it => [
    #set text(
      fill: dark_blue.darken(50%),
      weight: 400,
      size: 1em,
      font: secondary_fonts,
    )
    #block(
      smallcaps(it),
      inset: (top: 0.5em, bottom: 0.5em, rest: 0em),
    )
  ]

  // Levels 4-8: Standard styling (dark text, normal weight)
  show heading.where(level: 4): set text(fill: dark_text, weight: 300, size: 1em)
  show heading.where(level: 5): set text(fill: dark_text, weight: 300, size: 1em)
  show heading.where(level: 6): set text(fill: dark_text, weight: 300, size: 1em)
  show heading.where(level: 7): set text(fill: dark_text, weight: 300, size: 1em)
  show heading.where(level: 8): set text(fill: dark_text, weight: 300, size: 1em)

  // ==========================================================================
  // FIGURE AND TABLE STYLING
  // ==========================================================================

  // Figure caption styling
  show figure.caption: it => {
    set text(fill: cover_page_text, weight: 400, size: 1em)
    block(it, inset: (left: 5em, right: 5em, top: 0em, bottom: 0em))
  }

  // Table-specific settings
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: table): set block(breakable: false)
  show table.cell: set text(size: 0.8em)

  // Quarto table compatibility
  show figure.where(kind: "quarto-float-tbl"): set block(breakable: true)
  show figure.where(kind: "quarto-float-tbl"): set table.header(repeat: true)

  // Table styling with alternating row colors
  set table(
    fill: (_, y) => {
      if calc.odd(y) {
        // Odd rows: light accent
        return accent_color.lighten(90%).desaturate(90%)
      } else if y == 0 {
        // Header row: primary color
        return main_color.lighten(10%).desaturate(5%)
      }
    },
    inset: 0.7em,
    stroke: (x, y) => (
      x: none, // No vertical lines
      top: if y <= 1 { 0.5pt } else { 0pt }, // Top line for header
      bottom: 0.5pt, // Bottom line for all rows
    ),
  )

  // ==========================================================================
  // TABLE OF CONTENTS
  // ==========================================================================

  // Reset page numbering (exclude cover page)
  counter(page).update(1)

  // Custom table of contents
  context {
    let custom_outline_fill = box(width: 1fr, repeat("  . "))

    set outline(title: "Table of Contents")
    set outline.entry(fill: custom_outline_fill)

    // Tight spacing for all entries
    show outline.entry: set block(spacing: 0.4em)

    // Extra spacing before level 1 entries (except first)
    show outline.entry.where(level: 1): set block(above: 1.2em)

    // Level 1 entries: bold, colored, no fill dots
    show outline.entry.where(level: 1): it => {
      show repeat: none
      text(
        it,
        fill: secondary_color,
        font: secondary_fonts,
        weight: 600,
      )
    }

    // Slightly smaller font for all entries
    show outline.entry: it => [
      #set text(size: 0.9em)
      #it
    ]

    outline(indent: auto, depth: 5)

    pagebreak()
  }

  // ==========================================================================
  // MAIN DOCUMENT BODY
  // ==========================================================================

  body

  // ==========================================================================
  // LIST OF FIGURES AND TABLES
  // ==========================================================================

  context {
    pagebreak()

    // List of Figures
    outline(
      title: [List of Figures],
      target: figure.where(kind: "quarto-float-fig"),
    )
    outline(
      title: none,
      target: figure.where(kind: image),
    )

    pagebreak()

    // List of Tables
    outline(
      title: [List of Tables],
      target: figure.where(kind: "quarto-float-tbl"),
    )
    outline(
      title: none,
      target: figure.where(kind: table),
    )
  }
}

// ============================================================================
// USAGE EXAMPLE
// ============================================================================
//
// #import "medstata-template.typ": report
//
// #show: report.with(
//   title: "Clinical Evaluation Report",
//   subtitle: "Post-Market Clinical Follow-up Study",
//   author: "Dr. Jane Smith",
//   date: datetime.today().display(),
//   version: "1.0",
//   logo: "logo.png",
//   lof: true,
//   lot: true,
// )
//
// = Introduction
// Your content here...
//
// ============================================================================
