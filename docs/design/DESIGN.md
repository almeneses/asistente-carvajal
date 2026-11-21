# Design System: Asistente Carvajal Accessible Web App

**Origen:** Google Stitch — proyecto [Asistente Carvajal Accessible Web App](https://stitch.google.com/projects/18086611055013390157)
**Project ID:** `18086611055013390157`
**Capturado:** 2026-11-20
**Pantallas analizadas:** 18 (13 visibles en el lienzo, incluidas variantes ocultas)
**Assets:** logo extraído en `assistant/static/carvajal-logo.svg`
**Nota:** este documento es la fuente de verdad visual para la fase 4; el contenido base proviene del `designTheme.designMd` del proyecto de Stitch.

---

---
name: Asistente Carvajal Senior
colors:
  surface: '#FFFFFF'
  surface-dim: '#bfddff'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#edf4ff'
  surface-container: '#e3efff'
  surface-container-high: '#d9eaff'
  surface-container-highest: '#cfe5ff'
  on-surface: '#072B46'
  on-surface-variant: '#42474e'
  inverse-surface: '#11324e'
  inverse-on-surface: '#e8f1ff'
  outline: '#72777f'
  outline-variant: '#c2c7cf'
  surface-tint: '#366287'
  primary: '#00243c'
  on-primary: '#ffffff'
  primary-container: '#003a5d'
  on-primary-container: '#7aa4cd'
  inverse-primary: '#a0cbf5'
  secondary: '#006783'
  on-secondary: '#ffffff'
  secondary-container: '#3eccfd'
  on-secondary-container: '#00546c'
  tertiary: '#341c00'
  on-tertiary: '#ffffff'
  tertiary-container: '#4f3008'
  on-tertiary-container: '#c49867'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cee5ff'
  primary-fixed-dim: '#a0cbf5'
  on-primary-fixed: '#001d32'
  on-primary-fixed-variant: '#1a4a6e'
  secondary-fixed: '#bce9ff'
  secondary-fixed-dim: '#64d3ff'
  on-secondary-fixed: '#001f2a'
  on-secondary-fixed-variant: '#004d63'
  tertiary-fixed: '#ffddbb'
  tertiary-fixed-dim: '#eebe8a'
  on-tertiary-fixed: '#2b1700'
  on-tertiary-fixed-variant: '#614017'
  background: '#F3F6F8'
  on-background: '#001d34'
  surface-variant: '#cfe5ff'
  border: '#DCE5EA'
  success: '#1E7A57'
  warning: '#A86A1F'
typography:
  headline-xl:
    fontFamily: DM Sans
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 72px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: DM Sans
    fontSize: 38px
    fontWeight: '700'
    lineHeight: 50px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: DM Sans
    fontSize: 44px
    fontWeight: '700'
    lineHeight: 60px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: DM Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: DM Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 46px
    letterSpacing: 0em
  headline-sm:
    fontFamily: DM Sans
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: 0em
  body-xl:
    fontFamily: DM Sans
    fontSize: 24px
    fontWeight: '400'
    lineHeight: 38px
    letterSpacing: 0.01em
  body-lg:
    fontFamily: DM Sans
    fontSize: 22px
    fontWeight: '400'
    lineHeight: 36px
    letterSpacing: 0.01em
  body-md:
    fontFamily: DM Sans
    fontSize: 20px
    fontWeight: '400'
    lineHeight: 32px
    letterSpacing: 0.01em
  label-lg:
    fontFamily: DM Sans
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: 0.02em
  label-md:
    fontFamily: DM Sans
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 30px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: DM Sans
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  gutter-mobile: 1rem
  margin-mobile: 1.25rem
  space-xs: 0.5rem
  space-sm: 0.875rem
  space-md: 1.5rem
  space-lg: 2.25rem
  space-xl: 3.5rem
---

## Brand & Style

This design system establishes an empathetic, dignified, and editorial digital environment tailored explicitly for older adults (ages 60+). It bridges the heritage, prestige, and corporate security of a century-old institution with an accessible, human, and assistive interface.

### Brand Personality & Emotional Response
- **Dignified & Reassuring:** Never infantilizing or clinical. The visual tone respects the user's intelligence and life experience through refined editorial layouts, calm compositions, and confident typography.
- **Effortless Clarity:** Cognitive and motor friction are deliberately reduced. High legibility, large predictable interaction zones, and explicit status verifications eliminate hesitation and technological anxiety.
- **Warm Institutional Trust:** Anchored in deep navy and serene paper-like neutrals, balanced by warm kraft touches that evoke physical stationery and corporate stability.
- **Voice-Forward & Attentive:** Interaction centers on proactive vocal assistance, highlighted by vibrant cyan cues that signal listening, comprehension, and conversational safety.

### Design Movement
The system unites **Warm Editorial Elegance** with **Inclusive Human-Centered Functionalism**. It avoids cold software tropes in favor of spacious paper-like card surfaces, 1.6 baseline line-heights, distinct high-contrast boundaries (surpassing 7:1 WCAG AAA criteria), and tactile affordances scaled for motor comfort.

## Colors

The palette is engineered to surpass WCAG 2.2 AAA accessibility requirements, ensuring minimum contrast ratios of 7:1 for normal and body typography against light surfaces.

### Functional Roles
- **Primary (`#003A5D` - Azul Carvajal):** Core structural foundation, header surfaces, primary buttons, high-priority icons, and authoritative boundaries.
- **Secondary (`#00B5E5` - Cian Carvajal):** Vocal feedback, active microphone rings, assistive status accents, and progressive focus states. Never used for unbacked white text; paired exclusively with deep navy or pure white backgrounds with strict contrast containment.
- **Tertiary (`#C89B6A` - Kraft de Carva):** Warm heritage tone applied to supportive informational accents, bookmarks, tactile badges, and human touchpoints.
- **Neutral / Text (`#072B46` - Tinta / On-surface):** Deep inky navy replacing standard blacks. Used for all primary headlines, body text, and structural dividers to provide crisp 12:1+ contrast against white backgrounds.
- **Background (`#F3F6F8`):** Ultra-soft, low-glare cool tint providing resting room for aging eyes while maintaining separation from pure white cards.
- **Surface (`#FFFFFF`):** High-clarity canvas for all interactive modules, conversational speech bubbles, and reading cards.
- **Border (`#DCE5EA`):** Structural delineation ensuring clear spatial segmentation without visual harshness.
- **Semantic Success (`#1E7A57`) & Warning (`#A86A1F`):** Deep, legible tones calibrated for immediate recognition and full AAA readability.

## Typography

The type system is set in **DM Sans** throughout all functional tiers. Its open counters, distinct geometric apertures, wide horizontal proportions, and prominent x-height support visual acuity under reduced optical sharpness and presbyopia.

### Sizing and Spacing Rules
- **No Tiny Type:** The absolute minimum font size anywhere in the application is 18px (`label-sm`). Footnotes, disclosures, and timestamps must never degrade below this threshold.
- **Generous Leading:** Paragraph and narrative text must always maintain an open line-height of 1.6 (`fontSize * 1.6`) to prevent visual crowding when tracking between lines.
- **Character Spacing:** Generous letter-spacing tokens (`0.01em` to `0.02em`) on body and labels preserve individual character distinction.
- **Heading Restraint:** Display sizes scale up to 56px on desktop and gracefully step down to 38px on handheld devices to preserve single-line impact without breaking readability.

## Layout & Spacing

The layout philosophy follows a **Centrally Contained Fluid Grid** designed to avoid eye strain caused by scanning across expansive desktop screens.

### Spatial Architecture
- **Desktop Grid:** 12-column grid constrained to a maximum content width of 1200px. Gutters are fixed at 24px (`1.5rem`), and canvas margins at 32px (`2rem`).
- **Tablet Grid:** 8-column layout with 20px gutters and 24px margins.
- **Mobile Grid:** Single-column or 4-column layout with 16px (`1rem`) gutters and 20px (`1.25rem`) outer margins.
- **Touch Target Integrity:** Every interactive hit area occupies a physical boundary of at least 64px by 64px, flanked by minimum `space-sm` (14px) empty layout buffer zones to prevent accidental activations.
- **Rhythm & Flow:** Form groups, chat dialogues, and card listings follow strict vertical stacking, prioritizing linear focus navigation over dense multi-column arrays.

## Elevation & Depth

To accommodate older adults with reduced depth perception, depth is communicated through **Tonal Layering combined with Soft Ambient Shadows and Crisp Borders**. Never rely on shadows alone to define where an element begins or ends.

### Elevation Hierarchy
- **Level 0 (App Canvas):** The neutral `#F3F6F8` matte background. Completely un-elevated, reducing screen glare.
- **Level 1 (Surface Cards & Floating Sheets):** Pure white background (`#FFFFFF`) with a continuous 1px outline in `#DCE5EA` and an ambient shadow: `box-shadow: 0 4px 16px -2px rgba(7, 43, 70, 0.06), 0 2px 6px -1px rgba(7, 43, 70, 0.04)`.
- **Level 2 (Active States, Dialogues & Modals):** Pure white background, reinforced with a 1px border in `#DCE5EA` and an ambient, wide-dispersion drop shadow: `box-shadow: 0 12px 32px -4px rgba(7, 43, 70, 0.12), 0 4px 12px -2px rgba(7, 43, 70, 0.08)`.
- **Voice Action Focus Ring:** Active microphone triggers introduce an elevated pulsating cyan halo (`0 0 0 6px rgba(0, 181, 229, 0.35)`), clearly confirming auditory reception.

## Shapes

The shape system provides friendly, soft contours that signal comfort and warmth while retaining structural integrity.

### Corner Radii Guidelines
- **Cards & Primary Modules:** Fixed 24px border radius (`rounded-xl` equivalent). This prominent radius softens interface boundaries and guides the eye inward toward content.
- **Buttons:** 18px corner radius or full pill (`9999px`) shapes for primary actions. The rounded contour invites direct finger contact.
- **Input Fields & Form Selectors:** 16px corner radius, balancing clear tabular layout with approachable edges.
- **Voice Action Button:** Perfect circular geometry (1:1 aspect ratio) to establish an unmistakably distinct primary utility.
- **Dividers & Focus Outlines:** 2px stroke weight with rounded ends, avoiding harsh hairline artifacts.

## Components

Every component prioritizes visual contrast, motor forgiveness, and multi-modal feedback (voice + text + visual icon).

### 1. Buttons
- **Primary Button:** Minimum height 64px (72px for high-priority user actions). Full `#003A5D` fill with `#FFFFFF` text in `label-lg` (22px bold). Radius 18px or full pill. Generous internal padding: 18px vertical, 36px horizontal.
- **Voice Microphone Button:** Floating circular trigger, 80px × 80px minimum (up to 96px on assistive prompts). Fill in `#00B5E5` with `#FFFFFF` interior icon. Paired with a permanent or animated 6px ambient focus ring to confirm audio input status.
- **Secondary Button:** 64px height, `#FFFFFF` background, 2px solid border in `#003A5D`, and text in `#003A5D`.
- **Interactive Feedback:** Pressed states darken background fill by 12% rather than moving or shrinking the element, preserving stable physical touch targets.

### 2. Cards
- **Construction:** Background `#FFFFFF`, 24px border radius, 1px solid border `#DCE5EA`, and Level 1 elevation shadow.
- **Spacing:** Minimum internal padding of 24px (`space-lg`) on mobile, expanding to 36px on tablet and desktop.
- **Editorial Separator:** Content groupings within cards are separated by 1px rules in `#DCE5EA` flanked by 16px margin buffers.

### 3. Input Fields
- **Dimensions:** Minimum 64px height. Internal padding: 18px vertical, 24px horizontal.
- **Styling:** `#FFFFFF` background, 16px border-radius, and a prominent 2px border in `#DCE5EA`.
- **Typographic Scale:** Field text and placeholder set in 20px `body-md`. Placeholder color `#072B46` at 60% opacity (never lower, safeguarding 4.5:1 contrast).
- **Focus Indicator:** 3px active border in `#003A5D` with an outer 4px glow in `#00B5E5` at 25% opacity.

### 4. Iconography
- **Visual Weight:** Uniform 2px line thickness; minimum bounding size 28px × 28px (32px preferred for navigation).
- **Paired Context:** Icons must never appear as standalone actions; they are always accompanied by an explicit text label set in `label-md` or `label-sm`.

### 5. Checkboxes, Radio Buttons & Switches
- **Control Sizing:** Selection markers occupy a 32px × 32px box within an overall interactive touch area of 64px × 64px.
- **Border & Fill:** 2.5px border in `#003A5D`. When checked, filled in `#003A5D` with an internal 3px pure white checkmark.
- **Labels:** Text adjacent to checkboxes uses `body-lg` (22px) and is fully clickable as part of the unified touch target.

### 6. Chips & Filters
- **Dimensions:** 48px height with full pill radius (`rounded-full`).
- **Unselected:** `#FFFFFF` surface, 1.5px border `#DCE5EA`, text `#072B46`.
- **Selected:** `#003A5D` surface, text `#FFFFFF`, accompanied by an explicit check icon.

---

## 6. Aplicación en el chat de este repositorio

La app actual es FastAPI + HTMX; el sistema se aplica con variables CSS y componentes Jinja.

### Tokens CSS

```css
:root {
  --carvajal-primary: #003A5D;
  --carvajal-primary-strong: #00243C;
  --carvajal-secondary: #00B5E5;
  --carvajal-tertiary: #C89B6A;
  --carvajal-ink: #072B46;
  --carvajal-bg: #F3F6F8;
  --carvajal-surface: #FFFFFF;
  --carvajal-border: #DCE5EA;
  --carvajal-success: #1E7A57;
  --carvajal-warning: #A86A1F;
  --carvajal-radius-card: 24px;
  --carvajal-radius-button: 18px;
  --carvajal-radius-input: 16px;
  --carvajal-font: "DM Sans", system-ui, sans-serif;
}
```

### Componentes del chat

- **Cabecera:** logo Carvajal (SVG) + título “Asistente Carvajal”; fondo blanco, borde inferior `--carvajal-border`.
- **Burbuja de Carva:** superficie blanca, radio 24px, borde 1px `--carvajal-border`, sombra nivel 1, texto 20–22px; etiqueta “Carva” y hora.
- **Burbuja del usuario:** fondo `--carvajal-primary`, texto blanco, radio 24px; alineada a la derecha.
- **Campo de pregunta:** altura mínima 64px, radio 16px, texto 20px, foco con borde 3px `--carvajal-primary` + halo cian 4px al 25%.
- **Botón enviar:** altura 64px, fondo `--carvajal-primary`, texto blanco `label-lg`; estados presionados oscurecen sin cambiar el tamaño.
- **Botón de voz (futuro):** circular 80px, `--carvajal-secondary`, halo cian al escuchar; fuera del alcance de la fase 4.
- **Tarjetas de recomendación (catálogo):** superficie blanca, radio 24px, borde, sombra nivel 1; precio y vigencia legibles a 20px; CTA primario y “ficha técnica” secundario.
- **Chips de estado:** píldora 48px, seleccionado `--carvajal-primary` con check.
- **Citas/fuentes:** enlaces en `--carvajal-primary` con subrayado visible; nunca solo color.

### Accesibilidad

- Tamaño mínimo de texto: 18px (`label-sm`); cuerpo 20–22px, títulos 26–56px.
- Áreas táctiles mínimas de 64×64px y separación de 14px.
- Contraste objetivo **AAA** (7:1) en texto normal; como mínimo **AA**.
- Foco visible de 3px + halo cian; nada depende solo del color.
- `aria-live="polite"` para anunciar respuestas; `prefers-reduced-motion` para animaciones.
- No hay texto por debajo de 18px ni placeholders con bajo contraste.

### Alcance de la fase 4

Se adopta la identidad, tipografía, paleta, tarjetas, burbujas, campo y estados.
**Fuera de alcance ahora:** modo de voz completo, avatar/mascota Carva animada y flujo de
cotización con selección de empaque (se retoman en fases posteriores).

## 7. Inventario de pantallas

| Screen ID | Etiqueta | Visible |
|---|---|---|
| `01a97f3a27bc4bb6a9d99ed56e1f7b4b` | Modo de Voz - Asistente Carvajal | sí |
| `0a95d68b395b4ff8bb995af6fe24a3ef` | Flujo Integral - Asistente Carvajal | no |
| `17b56113c0b24a63bd6c775a0a6e9a04` | Bienvenida - Asistente Carvajal | sí |
| `194f22dca7974ff88ff037fc3502c2f8` | Confirmación y Preview en Chat - Asistente Carvajal | no |
| `20ebe7919f60405fbd127f803aeb87e5` | Conversación - Asistente Carvajal | sí |
| `29266631062a458fab012e0e153e5bae` | Carva Saludando - Bienvenida | sí |
| `2ca1e29bed7848e9a678ef38d4c860ca` | Carva Escuchando - Voz | sí |
| `49f59df2d37c4d6e98ff5ebd5b65968c` | Carvajal Logo Banner | sí |
| `4c5c4ff37bcd492d810f09c83e86f24f` | Animated SVG | sí |
| `647adebfbc664280928048f2e20d6842` | Confirmación - Carva Centrado y Proporcionado | no |
| `7b76d3e311d34700a644a25b780333b7` | Confirmación y Transición a Chat - Asistente Carvajal (Ajuste Carva) | no |
| `8045cfc2cfaa4ff0a661dd62bc7baa7e` | Confirmación y Transición a Chat - Asistente Carvajal | sí |
| `3537640230418053215` | carvajal-logo.svg | sí |
| `92ce596fb4594cd4a3919fcd14985634` | Confirmación - Asistente Carvajal | no |
| `a28be66d2ed542eca90e40e3088617dc` | Carva Celebrando - Éxito | sí |
| `a771fb6a2d4f477a95e3ccf3bdf370d7` | Avatar Carva Neutral - Chat | sí |
| `cb7848c9a20f4446b141e03e3c80152a` | Asistente de Empaques - Asistente Carvajal | sí |
| `3537640230418053753` | carvajal.com-design.md | sí |

## Nota de implementación (2026-11-20)

- El token `warning` de texto se implementa como `#8A5415` sobre superficies claras
  para alcanzar AA (el `#A86A1F` del tema queda para acentos no textuales).
- El tema oscuro se deriva de la misma paleta con variables CSS.
