---
name: Public Safety Intelligence
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fd'
  on-secondary-container: '#57657b'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#0b1c30'
  on-tertiary-container: '#75859d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  mono-data:
    fontFamily: jetbrainsMono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 32px
  xl: 48px
  grid_columns: '12'
  gutter: 20px
  margin_desktop: 40px
  margin_mobile: 16px
---

## Brand & Style
The design system is engineered for high-stakes law enforcement and public safety environments. The brand personality is **authoritative, precise, and utilitarian**. It avoids unnecessary ornamentation to ensure cognitive load is minimized during critical operations.

The aesthetic follows a **Corporate/Modern** style with a focus on **Data-Centricity**. It utilizes a "Command Center" metaphor—everything is structured, modular, and optimized for rapid scanning. The visual tone evokes trust and institutional reliability, ensuring that AI-driven insights are perceived as professional tools rather than experimental technology. 

**Logo Guidance:** The geometric mark should combine a stylized radar or location pin with a mesh grid pattern, symbolizing identification through technology. Use solid, heavy-weight lines to convey stability.

## Colors
The palette is dominated by Deep Navy and Slate to ground the interface in professionalism. The default mode is **Light**, optimized for high-brightness office environments, though the foundation supports an eventual high-contrast Dark mode for field operations.

- **Primary & Secondary:** Used for structural elements, sidebars, and primary navigation.
- **Neutrals:** A meticulous scale of Slate-grays is used for borders, secondary text, and background layering to create hierarchy without depth.
- **Functional Accents:** Alert Red and Warning Orange are reserved strictly for high-confidence matches or system errors. They must never be used for decorative purposes.
- **Success Green:** Used exclusively for "Verified" statuses and system-ready indicators.

## Typography
The system uses **Inter** for all UI elements to ensure maximum legibility across different monitor resolutions. **JetBrains Mono** (or a similar monospace font) is introduced specifically for identification numbers, coordinates, and confidence scores to ensure character clarity (e.g., distinguishing '0' from 'O').

- **Headlines:** Use tight letter-spacing for a modern, compact look.
- **Labels:** Small caps or all-caps are used for metadata headers to distinguish them from user data.
- **Scalability:** For mobile/tablet views, reduce `display-lg` to 28px and `headline-md` to 20px to accommodate narrower viewports while maintaining hierarchy.

## Layout & Spacing
The layout follows a **Fixed-Fluid hybrid grid**. Sidebars and control panels have fixed widths (e.g., 280px), while the central data dashboard is fluid to maximize the display of CCTV feeds and data tables.

- **Grid:** A standard 12-column system is used for dashboard layouts.
- **Density:** High-density spacing is preferred. Use the `8px` (sm) unit for internal card padding and `16px` (md) for spacing between major components.
- **Breakpoints:**
  - **Desktop (1280px+):** Full multi-panel view.
  - **Tablet (768px - 1279px):** Collapsed sidebar, 2-column card grid.
  - **Mobile (<767px):** Single column stack, simplified data tables.

## Elevation & Depth
This design system avoids heavy drop shadows in favor of **Tonal Layers** and **Low-Contrast Outlines**. Depth is communicated through color-stepping rather than physical metaphors.

- **Level 0 (Background):** Slate-50 (#F8FAFC).
- **Level 1 (Cards/Containers):** Pure White (#FFFFFF) with a 1px border in Slate-200.
- **Level 2 (Modals/Popovers):** Pure White with a subtle 4px blur shadow, 10% opacity, to lift the element without distracting from the data.
- **Active State:** Elements that are selected or "in focus" should use a 2px Primary Navy border rather than a shadow.

## Shapes
The shape language is **Soft (0.25rem)**. This provides a professional balance between the harshness of sharp corners and the "consumer-grade" feel of highly rounded shapes.

- **Small Components (Buttons, Inputs, Badges):** 4px (0.25rem).
- **Large Components (Cards, Modals):** 8px (0.5rem).
- **Circular Elements:** Reserved only for user avatars and "Scanning" status indicators.

## Components
Consistent styling across identification tools is paramount:

- **Data Tables:** Use zebra-striping (Slate-50) for rows. Headers must be `label-bold` with a Slate-200 bottom border. No vertical borders.
- **Status Badges:** 
  - *Verified:* Green background (10% opacity), Green text.
  - *Pending:* Slate background (10% opacity), Slate text.
  - *Alert:* Red background (10% opacity), Red text.
- **Confidence Meters:** A horizontal bar-chart style component inside cards. Use a gradient scale from Slate to Primary Navy, only turning Orange/Red if a threshold is crossed.
- **Input Fields:** Strict rectangular fields with 1px Slate-300 borders. Focus state uses a 1px Primary Navy ring.
- **Buttons:** 
  - *Primary:* Solid Deep Navy with white text. 
  - *Secondary:* White background, Slate-300 border, Deep Navy text.
  - *Destructive:* Solid Alert Red for "Delete Record" or "End Live Feed".
- **Identification Cards:** Use a vertical layout for missing person profiles: top-aligned photo, followed by a bold Name, and a "Identity Confidence" score at the footer.