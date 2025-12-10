# Design System Guidelines

Complete design system documentation for rebranding applications with consistent typography, colors, and layout.

---

## Typography

### Font Families

#### Primary Brand Font: Milling
- **Designer**: Tanguy Vanlaeys
- **Foundry**: 205TF
- **Official URL**: https://www.205.tf/milling
- **Usage**: Primary brand font for all UI text (99% of brand uses Duplex 1mm)

#### Code Font: IBM Plex Mono
- **Source**: Google Fonts
- **Usage**: All code blocks, inline code, and monospace text

#### System Fallback: Inter
- **Source**: Google Fonts
- **Usage**: Fallback system font when Milling is unavailable

### Font Weights & Milling Variants

| Weight | Milling Variant | Usage | CSS Weight |
|--------|----------------|-------|------------|
| 200 | Simplex 0.5mm | Display - big numerals or words (occasional) | `font-thin` |
| 300 | Simplex 0.75mm | Display - dramatic headlines (occasional) | `font-light` |
| 400 | Duplex 1mm | **Primary - 99% of brand uses this** | `font-normal` |
| 500 | Triplex 1mm | Emphasis - headlines, highlights | `font-medium`, `font-semibold`, `font-bold` |
| 600 | Triplex 1.5mm | Strong emphasis (rarely used) | - |
| 700 | Triplex 2mm | Heavy emphasis (rarely used) | - |

**Important**: `font-bold`, `font-semibold`, and `font-medium` all map to weight 500 (Triplex 1mm) for lighter, more readable bold text.

### Typography Hierarchy

#### Headline 1 (h1)
- **Desktop**: 64px / 72px line-height
- **Mobile**: 36px / 44px line-height
- **Letter Spacing**: 0 (no negative tracking to prevent melding)
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Main page titles

#### Headline 2 (h2)
- **Desktop**: 56px / 64px line-height
- **Mobile**: 32px / 40px line-height
- **Letter Spacing**: 0
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Section titles

#### Headline 3 (h3)
- **Desktop**: 48px / 56px line-height
- **Mobile**: 28px / 36px line-height
- **Letter Spacing**: 0
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Subsection titles

#### Headline 4 (h4)
- **Desktop**: 40px / 48px line-height
- **Mobile**: 24px / 32px line-height
- **Letter Spacing**: 0
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Card titles, component headers

#### Headline 5 (h5)
- **Desktop**: 32px / 40px line-height
- **Mobile**: 20px / 28px line-height
- **Letter Spacing**: 0
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Small section headers

#### Headline 6 (h6)
- **Desktop**: 24px / 32px line-height
- **Mobile**: 18px / 26px line-height
- **Letter Spacing**: 0
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Labels, small headers

#### Large Paragraph
- **Desktop**: 20px / 28px line-height
- **Mobile**: 18px / 26px line-height
- **Letter Spacing**: 0.01em (1%)
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Lead paragraphs, emphasized body text

#### Paragraph (p)
- **Size**: 16px / 24px line-height
- **Letter Spacing**: 0.015em (1.5%)
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Standard body text

#### Small Text
- **Size**: 12px / 20px line-height
- **Letter Spacing**: 0.02em (2%)
- **Weight**: 400 (Duplex 1mm)
- **Text Transform**: UPPERCASE
- **Usage**: Labels, captions, metadata

#### Tag
- **Size**: 12px / 20px line-height
- **Letter Spacing**: Normal
- **Weight**: 400 (Duplex 1mm)
- **Usage**: Tags, badges, small labels

#### Inline Code
- **Size**: 16px / 24px line-height
- **Letter Spacing**: 0
- **Font**: IBM Plex Mono
- **Weight**: 400
- **Usage**: Code snippets, technical terms

### Font Loading

#### Milling Font Faces (CDN)

```css
/* Simplex 0.5mm - Weight 200 */
@font-face {
  font-family: 'Milling';
  font-style: normal;
  font-weight: 200;
  src: url('https://d1eaw48ll8ut2y.cloudfront.net/FONTS/205TF-Milling-Simplex0,5mm.woff2') format('woff2');
  font-display: swap;
}

/* Simplex 0.75mm - Weight 300 */
@font-face {
  font-family: 'Milling';
  font-style: normal;
  font-weight: 300;
  src: url('https://d1eaw48ll8ut2y.cloudfront.net/FONTS/205TF-Milling-Simplex0,75mm.woff2') format('woff2');
  font-display: swap;
}

/* Duplex 1mm - Weight 400 (PRIMARY) */
@font-face {
  font-family: 'Milling';
  font-style: normal;
  font-weight: 400;
  src: url('https://d1eaw48ll8ut2y.cloudfront.net/FONTS/205TF-Milling-Duplex1mm.woff2') format('woff2');
  font-display: swap;
}

/* Triplex 1mm - Weight 500 */
@font-face {
  font-family: 'Milling';
  font-style: normal;
  font-weight: 500;
  src: url('https://d1eaw48ll8ut2y.cloudfront.net/FONTS/205TF-Milling-Triplex1mm.woff2') format('woff2');
  font-display: swap;
}

/* Triplex 1.5mm - Weight 600 */
@font-face {
  font-family: 'Milling';
  font-style: normal;
  font-weight: 600;
  src: url('https://d1eaw48ll8ut2y.cloudfront.net/FONTS/205TF-Milling-Triplex1,5mm.woff2') format('woff2');
  font-display: swap;
}

/* Triplex 2mm - Weight 700 */
@font-face {
  font-family: 'Milling';
  font-style: normal;
  font-weight: 700;
  src: url('https://d1eaw48ll8ut2y.cloudfront.net/FONTS/205TF-Milling-Triplex2mm.woff2') format('woff2');
  font-display: swap;
}
```

#### IBM Plex Mono (Google Fonts)

Load IBM Plex Mono from Google Fonts with full unicode-range support for international characters.

---

## Color System

### Masterbrand - Neutrals

| Name | Hex | Usage |
|------|-----|-------|
| Chalk | `#F4F3F3` | Lightest background |
| Fog | `#ECECEC` | Light backgrounds |
| Smoke | `#D3D1CF` | Borders, dividers |
| Ash | `#8F8984` | Muted text |
| Shadow | `#45423F` | Dark text |
| Charcoal | `#1D1C1B` | Primary dark text |

### Masterbrand - Primary Colors

#### Blue (Embed) - Primary Brand Color
- **Blue**: `#6CD5FD`
- **Dark Blue**: `#366B7F`
- **Light Blue**: `#C4EEFE`

#### Green (Embed) - Primary Brand Color
- **Green**: `#60E21B`
- **Dark Green**: `#30710E`
- **Light Green**: `#BFF3A4`

#### Supporting Colors
- **Neutral Gray**: `#E9E8E7` - For backgrounds and subtle elements

### Product Colors

#### Search (Blue Variants)
- **Blue**: `#6CD5FD`
- **Light Blue**: `#C4EEFE`
- **Dark Blue**: `#366B7F`

#### Generate (Green Variants)
- **Green**: `#60E21B`
- **Light Green**: `#BFF3A4`
- **Dark Green**: `#30710E`

#### Embed (Blue & Green Palette)
- **Blue**: `#6CD5FD` - Primary embed blue
- **Green**: `#60E21B` - Primary embed green
- **Dark Green**: `#30710E` - Dark green variant
- **Light Green**: `#BFF3A4` - Light green variant
- **Dark Blue**: `#366B7F` - Dark blue variant
- **Light Blue**: `#C4EEFE` - Light blue variant

### System Colors

#### Error
- **Dark**: `#9D4228`
- **Default**: `#E22E22`
- **Light**: `#FFCCC0`

#### Warning
- **Dark**: `#7D5D0C`
- **Default**: `#FABA17`
- **Light**: `#FDE3A2`

#### Success (Using Embed Green Palette)
- **Dark**: `#30710E`
- **Default**: `#60E21B`
- **Light**: `#BFF3A4`

#### Info (Blue-based)
- **Dark**: `#366B7F`
- **Default**: `#6CD5FD`
- **Light**: `#C4EEFE`

### Legacy Primary Scale (Mapped to Blue/Green)

| Scale | Hex | Color |
|-------|-----|-------|
| 50 | `#C4EEFE` | Light Blue |
| 100 | `#6CD5FD` | Blue |
| 200 | `#BFF3A4` | Light Green |
| 300 | `#366B7F` | Dark Blue |
| 400 | `#60E21B` | Green |
| 500 | `#30710E` | Dark Green |
| 600 | `#1D1C1B` | Charcoal |
| 700 | `#1D1C1B` | Charcoal |

### Gradients

#### Masterbrand Gradients (Blue & Green)
- `gradient-masterbrand`: `linear-gradient(to right, #6CD5FD, #BFF3A4, #60E21B)`
- `gradient-masterbrand-1`: `linear-gradient(to right, #6CD5FD, #C4EEFE, #60E21B)`
- `gradient-masterbrand-2`: `linear-gradient(to right, #C4EEFE, #6CD5FD, #BFF3A4)`
- `gradient-masterbrand-3`: `linear-gradient(to right, #366B7F, #6CD5FD, #BFF3A4)`
- `gradient-masterbrand-4`: `linear-gradient(to right, #60E21B, #BFF3A4, #6CD5FD)`

#### Search Gradients (Blue-focused)
- `gradient-search-1`: `linear-gradient(to right, #366B7F, #6CD5FD, #C4EEFE)`
- `gradient-search-2`: `linear-gradient(to right, #C4EEFE, #6CD5FD, #E9E8E7)`
- `gradient-search-3`: `linear-gradient(to right, #6CD5FD, #E9E8E7, #C4EEFE)`
- `gradient-search-4`: `linear-gradient(to right, #6CD5FD, #C4EEFE, #BFF3A4)`

#### Generate Gradients (Green-focused)
- `gradient-generate-1`: `linear-gradient(to right, #30710E, #60E21B, #BFF3A4)`
- `gradient-generate-2`: `linear-gradient(to right, #BFF3A4, #60E21B, #E9E8E7)`
- `gradient-generate-3`: `linear-gradient(to right, #30710E, #BFF3A4, #60E21B)`
- `gradient-generate-4`: `linear-gradient(to right, #60E21B, #BFF3A4, #6CD5FD)`

#### Embed Gradients (Blue & Green Palette)
- `gradient-embed-1`: `linear-gradient(to right, #BFF3A4, #C4EEFE, #E9E8E7)`
- `gradient-embed-2`: `linear-gradient(to right, #30710E, #6CD5FD, #BFF3A4)`
- `gradient-embed-3`: `linear-gradient(to right, #C4EEFE, #BFF3A4, #60E21B)`
- `gradient-embed-4`: `linear-gradient(to right, #60E21B, #6CD5FD, #366B7F)`

---

## Layout System

### Grid System

**12-column grid system** that scales responsively:
- **Desktop**: 12 columns
- **Tablet (≤768px)**: 6 columns
- **Mobile (≤640px)**: 4 columns
- **Small Mobile (≤480px)**: 2 columns

#### Grid Classes
- `.grid-12` - 12 columns (scales to 6, 4, 2)
- `.grid-6` - 6 columns (scales to 3, 2)
- `.grid-4` - 4 columns
- `.grid-3` - 3 columns
- `.grid-2` - 2 columns

#### Section Division Classes
- `.section-1-1` or `.div-1-1` - Full width (12 columns)
- `.section-1-2` or `.div-1-2` - Half width (6 columns)
- `.section-1-3` or `.div-1-3` - Third width (4 columns)
- `.section-1-4` or `.div-1-4` - Quarter width (3 columns)
- `.section-1-6` or `.div-1-6` - Sixth width (2 columns)

### Spacing System

**Built around multiples of 4px**

| Name | Size | Calculation | Usage |
|------|------|------------|-------|
| Spacer XS | `20px` | 5 × 4px | Small gaps |
| Spacer SM | `40px` | 10 × 4px | Medium gaps |
| Spacer MD | `64px` | 16 × 4px | Large gaps |
| Spacer LG | `96px` | 24 × 4px | Extra large gaps |

### Margins & Gutters

- **Margin**: 4% of shortest side (rounded to multiples of 4px)
- **Gutter**: 8% (2× margin) - used between grid columns
- **Class**: `.margin-4p` for 4% margin
- **Class**: `.gutter-8p` for 8% gap

### Border Radius

- **Brand Radius**: 30% of shortest side
- **Class**: `.rounded-brand`
- **Note**: For dynamic calculation, use aspect-ratio aware classes

### Layout Types

#### Lines Layout (Type-based)
- **Class**: `.layout-lines`
- **Grid**: 12 columns
- **Gap**: 8% (gutter)

#### Cards Layout (Card-based)
- **Class**: `.layout-cards`
- **Grid**: 12 columns
- **Gap**: 4% (half gutter)

#### Hero Layout (Hero imagery)
- **Class**: `.layout-hero`
- **Grid**: 12 columns
- **Gap**: 8% (gutter)

#### Fullbleed Layout (Fullbleed imagery)
- **Class**: `.layout-fullbleed`
- **Grid**: 12 columns
- **Gap**: 8% (gutter)

#### Container Brand
- **Class**: `.container-brand`
- **Margin**: 4%
- **Width**: `calc(100% - 8%)`

---

## Best Practices

### Typography

1. **Primary Weight**: Use Duplex 1mm (weight 400) for 99% of brand text
2. **Bold Text**: Use weight 500 (Triplex 1mm) instead of 700 for lighter, more readable bold
3. **Letter Spacing**: Avoid negative tracking; use 0 or positive values to prevent words from melding
4. **Headings**: All headings use weight 400 unless emphasis is needed (then use 500)
5. **Display Text**: Use Simplex (200-300) only occasionally for dramatic display cases

### Colors

1. **Primary Colors**: Blue (Embed) and Green (Embed) are the primary brand colors
2. **Blue Palette**: Use embed blue (`#6CD5FD`) and variants for primary actions and accents
3. **Green Palette**: Use embed green (`#60E21B`) and variants for success states and secondary actions
4. **System Colors**: Use blue-based info colors (`#6CD5FD`), green-based success colors (`#60E21B`)
5. **Gradients**: Use masterbrand gradients (blue & green) for hero sections, product-specific gradients for feature areas

### Layout

1. **Grid First**: Always use the 12-column grid system
2. **4px Multiples**: All spacing should be multiples of 4px
3. **Responsive**: Grid automatically scales; test at all breakpoints
4. **Consistent Gaps**: Use 8% gutter for main layouts, 4% for card grids

### Font Loading

1. **CDN Fonts**: Milling fonts load from CDN (CloudFront)
2. **Font Display**: Use `font-display: swap` for better performance
3. **Fallbacks**: Always include Inter and system-ui as fallbacks
4. **Code Fonts**: Load IBM Plex Mono from Google Fonts with full unicode support

---

## Implementation Notes

### Tailwind CSS Configuration

```javascript
fontFamily: {
  sans: ['Milling', 'Inter', 'system-ui', 'sans-serif'],
  mono: ['IBM Plex Mono', 'monospace'],
},
fontWeight: {
  thin: '200',      // Simplex 0.5mm
  light: '300',     // Simplex 0.75mm
  normal: '400',    // Duplex 1mm (primary)
  medium: '500',    // Triplex 1mm
  semibold: '500',  // Triplex 1mm (same as medium)
  bold: '500',      // Triplex 1mm (lighter bold)
},
```

### CSS Overrides

```css
/* Override font-bold on headings to use medium weight (500) */
h1.font-bold,
h2.font-bold,
h3.font-bold,
h4.font-bold,
h5.font-bold,
h6.font-bold {
  font-weight: 500 !important;
  letter-spacing: 0.01em;
}
```

---

## Quick Reference

### Most Common Typography
- **Body Text**: 16px, weight 400, letter-spacing 0.015em
- **Headings**: Weight 400 (Duplex 1mm), letter-spacing 0
- **Bold Text**: Weight 500 (Triplex 1mm), not 700

### Most Common Colors
- **Primary Brand**: Blue `#6CD5FD`, Green `#60E21B`
- **Text Dark**: Charcoal `#1D1C1B`
- **Text Light**: Ash `#8F8984`
- **Background Light**: Chalk `#F4F3F3` or Fog `#ECECEC`

### Most Common Spacing
- **Small Gap**: 20px (spacer-xs)
- **Medium Gap**: 40px (spacer-sm)
- **Large Gap**: 64px (spacer-md)
- **Grid Gutter**: 8%

---