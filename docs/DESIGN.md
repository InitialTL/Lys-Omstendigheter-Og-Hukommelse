# Design system, accessibility and device requirements

## Direction

This is a public research instrument, **not** a product landing page. The visual
hierarchy is editorial: paper background, calm typographic scale, dark teal
accent, thin borders and small-radius surfaces. No stock photos, decorative
orbs, glassmorphism, third-party fonts, emoji illustrations or animation-heavy
marketing panels are loaded. The fixed experimental backgrounds are never
filtered or visually modified by the design system.

Source references used for the engineering decisions:

* W3C Web Content Accessibility Guidelines 2.2: https://www.w3.org/TR/WCAG22/
* W3C internationalization tips: https://www.w3.org/International/quicktips/
* Material Design responsive UI: https://m1.material.io/layout/responsive-ui.html

## Device matrix

The CSS is mobile-first in actual behavior and has fallbacks for 320 px phones,
360–430 px phones, landscape phones, 768 px tablets, 1024 px laptops and 1280 px
desktops. The same HTML uses flexible grids rather than duplicate mobile
components. Inputs retain a 16 px font to avoid unwanted iOS viewport zoom.
Buttons, input fields and language selects use at least 44–48 px minimum
heights. Safe-area insets and reduced-motion preferences are respected.

Word-pair cards fit in **two columns even on phones**, reducing scrolling
under the 60-second memorization deadline. On extremely small screens or large
user text settings scrolling may still be required; this is an unavoidable
methodological/device limitation and should be recorded in your pilot.

The 60-second adaptation stage intentionally consists of **only the stimulus
color and timer**. Fullscreen is optional and may be rejected by mobile browsers.
No layout technique can guarantee a physical screen emits a specified spectrum,
kelvin value or lux level.

## UI acceptance criteria

1. Entire registration→calibration→adaptation→learning→distraction→recall flow
   works by touch, keyboard and mouse at each viewport.
2. The recall phase starts with the new 120-second deadline; a previous 00:00
   must never immediately auto-submit an answer.
3. No horizontal document overflow at 320, 390, 768 or 1280 px.
4. A language switch is visible on all non-adaptation pages; changing the
   interface must **not** silently change the fixed graded test language.
5. `document.documentElement.lang` updates, including a future RTL `dir`.
6. Clear focus indicators, labeled controls, comprehensible error messages,
   readable contrast except for the *intentional* low-contrast calibration marks.

E2E smoke tests are in `scripts/ui_smoke.py` and run in GitHub Actions using
Chromium and a temporary database, in addition to unit and API tests.
