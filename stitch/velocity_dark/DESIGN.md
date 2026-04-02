# Design System Document: The Kinetic Editorial

## 1. Overview & Creative North Star
### The Creative North Star: "The Digital Arena"
This design system moves away from the static, boxy nature of traditional social feeds and embraces the fluid energy of professional sports. We are not building a "utility app"; we are building a premium digital skybox. The aesthetic is defined by **High-End Editorial**—think the high-contrast drama of *ESPN’s* motion graphics blended with the minimalist sophistication of a luxury timepiece brand.

To break the "template" look, we utilize **Intentional Asymmetry**. Key headlines should feel like magazine spreads, overlapping container boundaries, while content cards utilize deep tonal layering rather than rigid borders. The experience should feel expansive, fast, and exclusive.

---

## 2. Colors
Our palette is rooted in the depth of a night stadium. We use high-voltage accents to draw the eye to "the play" (the content).

### Palette Strategy
*   **The Foundation:** Use `surface` (`#0c0e12`) as the base. It is not pure black, but a deep slate that allows for "true black" (`surface-container-lowest`) to be used for deep recessed areas.
*   **The Accents:** `primary` (Electric Blue) and `secondary` (Neon Purple) should be used sparingly for high-action items. 
*   **Signature Textures:** Use linear gradients for primary CTAs (from `primary` to `primary_container`) to simulate light hitting a high-tech fabric.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders for sectioning. Boundaries must be defined solely through background color shifts or tonal transitions. To separate a feed from a sidebar, use a shift from `surface` to `surface_container_low`. 

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. 
*   **Level 0 (Base):** `surface`
*   **Level 1 (Main Content Area):** `surface_container`
*   **Level 2 (Active Cards):** `surface_container_high`
*   **Level 3 (Floating Menus/Popovers):** `surface_container_highest`

### The "Glass & Gradient" Rule
For sidebars and navigation, use **Glassmorphism**. Apply `surface_variant` at 60% opacity with a 20px backdrop blur. This allows the "buzz" of the background content to bleed through, maintaining a sense of place.

---

## 3. Typography
We use a dual-sans serif approach to balance editorial authority with functional readability.

*   **Display & Headlines (Manrope):** Bold, wide, and authoritative. Use `display-lg` for athlete names or major "Breaking" headlines. These should feel like a stadium Jumbotron.
*   **Interface & Body (Inter):** Clean and neutral. Inter provides the technical "data" feel required for stats and social commentary.

**Hierarchy as Identity:**
*   Use `headline-lg` for section headers with `on_surface_variant` (muted) for secondary metadata. 
*   High-contrast scaling: A `display-sm` headline should immediately sit next to `body-md` text to create a modern, "top-heavy" editorial look.

---

## 4. Elevation & Depth
In this system, depth is "felt," not "seen." We avoid the heavy drop shadows of the early 2010s.

### The Layering Principle
Achieve lift by "stacking." A `surface_container_lowest` card sitting on a `surface_container_low` section creates a natural, soft-etched pocket for content without a single shadow.

### Ambient Shadows
When an element must float (e.g., a "New Post" FAB), use an **Ambient Shadow**:
*   **Color:** 8% opacity of `primary_dim`.
*   **Blur:** 32px to 48px.
*   **Spread:** -4px.
This creates a glow rather than a shadow, mimicking the neon lights of an arena.

### The "Ghost Border" Fallback
If accessibility requires a container edge, use a **Ghost Border**: `outline_variant` at 15% opacity. This provides a "whisper" of an edge that disappears into the background.

---

## 5. Components

### Buttons
*   **Primary:** Gradient fill (`primary` to `primary_container`), `xl` (1.5rem) rounded corners. Text is `on_primary_fixed` (Black) for maximum punch.
*   **Tertiary (Action):** No background. Use `primary` text with a subtle `surface_bright` hover state.

### Cards & Lists
*   **The Card Rule:** Forbid divider lines. Use `1.4rem` (Spacing 4) vertical white space to separate items.
*   **State:** On hover, a card should shift from `surface_container` to `surface_container_high`.

### Input Fields
*   **Styling:** `surface_container_lowest` background, no border. Focus state is a 1px "Ghost Border" of `secondary` (Neon Purple).
*   **Corner Radius:** `md` (0.75rem).

### "Buzz" Chips
*   Used for trending topics or player stats.
*   **Style:** `surface_variant` background, `label-md` typography, `full` rounding. If "Hot," use a `secondary_container` background with `on_secondary` text.

### Glass Navigation (Sidebar)
*   60% `surface` background + 20px Blur.
*   No right-side border. Use a subtle gradient fade-to-transparent to transition into the main feed.

---

## 6. Do's and Don'ts

### Do:
*   **Do** use asymmetrical margins. For example, a 5.5rem (Spacing 16) left margin and a 2.75rem (Spacing 8) right margin on headers to create an editorial flow.
*   **Do** use `primary` and `secondary` together in gradients for "Elite" status athletes or verified "Buzz."
*   **Do** leverage the `xl` (1.5rem) corner radius for large image containers to maintain the "Premium" feel.

### Don't:
*   **Don't** use 1px gray lines to separate tweets/posts. It breaks the immersive "Digital Arena" vibe. Use a 1px gap showing the `surface_dim` background instead.
*   **Don't** use pure white (#FFFFFF) for body text. Use `on_surface` (#f6f6fc) to reduce eye strain in the dark theme.
*   **Don't** use standard "drop shadows" on cards. Use tonal layering or the Ambient Glow.
*   **Don't** cram content. If a section feels tight, double the spacing value. Air is luxury.