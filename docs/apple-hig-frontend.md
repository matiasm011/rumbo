# Apple HIG audit — primary-source findings for Rumbo's web chat UI

Research compiled 2026-09-24 from **primary Apple sources only**: the Human Interface
Guidelines (HIG), Apple Developer API documentation, and WWDC session transcripts.
Every claim carries the URL of the Apple source that owns it.

> **Currency note:** the HIG pages below are the current iOS 26-era revisions, which
> introduce **Liquid Glass** as the material for the controls/navigation layer and keep
> the classic `ultraThin…thick` "standard materials" for the content layer. The
> `navigation-bars` HIG URL now redirects to the consolidated **Toolbars** page.
> Where guidance changed recently, the change-log date is cited.

Sources fetched:
- HIG: Layout, Typography, Materials, Color, Dark Mode, Motion, Accessibility,
  VoiceOver, Sheets, Modality, Toolbars (absorbs Navigation bars), Gestures,
  Playing haptics, Feedback, Designing for iOS, iMessage apps and stickers
- API docs: `UIBlurEffect.Style`, `UINotificationFeedbackGenerator`,
  `UIImpactFeedbackGenerator`, `UISheetPresentationController`
- WWDC 2018 Session 803, "Designing Fluid Interfaces" (full transcript)

---

## 1. Layout & tap targets

| Claim | Value | Source |
|---|---|---|
| Default (recommended) control size, iOS/iPadOS | **44×44 pt** | https://developer.apple.com/design/human-interface-guidelines/accessibility |
| Absolute minimum control size, iOS/iPadOS | **28×28 pt** | https://developer.apple.com/design/human-interface-guidelines/accessibility |
| Padding around a control **with** a bezel | ~**12 pt** | https://developer.apple.com/design/human-interface-guidelines/accessibility ("Consider spacing between controls as important as size") |
| Padding around a bezel-less control's visible edges | ~**24 pt** | https://developer.apple.com/design/human-interface-guidelines/accessibility |
| Safe areas | "Respecting the safe area is essential to make sure system UI and hardware features like the Dynamic Island don't obstruct content and controls." | https://developer.apple.com/design/human-interface-guidelines/layout |
| Standard margins | The system provides "predefined layout guides that make it easy to apply standard margins around content and restrict the width of text for optimal readability." **No specific pt margin values are published in the current HIG.** | https://developer.apple.com/design/human-interface-guidelines/layout |
| Reach ergonomics | "It tends to be easier and more comfortable for people to reach a control when it's located in the middle or bottom area of the display." | https://developer.apple.com/design/human-interface-guidelines/designing-for-ios |
| Progressive disclosure | Use disclosure triangles/menus/nested views "to reduce how much content to initially display." | https://developer.apple.com/design/human-interface-guidelines/layout |
| Grouping | Group related items using "negative space, container shapes, or separator lines." | https://developer.apple.com/design/human-interface-guidelines/layout |
| Dynamic Type in layout | Layouts must adapt: horizontal items may need to stack vertically; rows/containers grow in height so text isn't cropped. | https://developer.apple.com/design/human-interface-guidelines/layout |

**Web translation notes:** 44×44 pt ≈ 44×44 CSS px at 1× (1 pt = 1 px on a 1× display;
WebKit treats 1 pt = 1.333 px, but the practical web reading of Apple's rule is
"~44 CSS px"). WCAG 2.2 Target Size (AA) is 24×24 CSS px — Apple's 44 pt default is
stricter; Apple's 28 pt floor maps closely to WCAG's 24 px floor.

---

## 2. Typography

SF Pro text styles at the **Large (default)** Dynamic Type size, iOS/iPadOS
(source table: "iOS, iPadOS Dynamic Type sizes › Large (default)"):

| Style | Weight | Size (pt) | Leading (pt) | Emphasized variant |
|---|---|---|---|---|
| Large Title | Regular | **34** | 41 | Bold |
| Title 1 | Regular | **28** | 34 | Bold |
| Title 2 | Regular | **22** | 28 | Bold |
| Title 3 | Regular | **20** | 25 | Semibold |
| Headline | **Semibold** | **17** | 22 | Semibold |
| Body | Regular | **17** | 22 | Semibold |
| Callout | Regular | **16** | 21 | Semibold |
| Subheadline | Regular | **15** | 20 | Semibold |
| Footnote | Regular | **13** | 18 | Semibold |
| Caption 1 | Regular | **12** | 16 | Semibold |
| Caption 2 | Regular | **11** | 13 | Semibold |

Source: https://developer.apple.com/design/human-interface-guidelines/typography (Specifications)

Legibility minimums (also restated on the Accessibility page):

- iOS default text size **17 pt**, minimum **11 pt** — "Follow the recommended default
  and minimum text sizes for each platform — for both custom and system fonts."
  Sources: https://developer.apple.com/design/human-interface-guidelines/typography ,
  https://developer.apple.com/design/human-interface-guidelines/accessibility
- "In general, **avoid light font weights**… prefer Regular, Medium, Semibold, or Bold…
  avoid Ultralight, Thin, and Light… especially when text is small."
  Source: https://developer.apple.com/design/human-interface-guidelines/typography

**Tracking (letter-spacing)** — SF Pro, iOS (1/1000 em units; multiply by font size to
get pt/px). The system adjusts tracking dynamically per point size; key values:

| Size | Tracking (1/1000 em) | ≈ CSS `letter-spacing` |
|---|---|---|
| 11 | +6 | +0.006 em |
| 12 | 0 | 0 |
| 13 | −6 | −0.006 em |
| 15 | −16 | −0.016 em |
| 16 | −20 | −0.020 em |
| 17 | −26 | −0.026 em (−0.43 px) |
| 20 | −23 | −0.023 em |
| 22 | −12 | −0.012 em |
| 24 | +3 | +0.003 em |
| 28 | +14 | +0.014 em |
| 34 | +12 | +0.012 em (+0.40 px) |

Source: https://developer.apple.com/design/human-interface-guidelines/typography (Tracking values › SF Pro).
Note the crossover: negative tracking below ~23 pt, positive above — i.e. body text is
tightened, display sizes loosened. The note "In a running app, the system font
dynamically adjusts tracking at every point size" means web `-apple-system` text gets
this automatically; only match it manually for non-system fonts or mockups.

**Dynamic Type expectations:**

- Text styles "allow text to scale proportionately when people change the system's text
  size." Using system text styles "ensures support for Dynamic Type and larger
  accessibility type sizes."
  Source: https://developer.apple.com/design/human-interface-guidelines/typography
- Full iOS scale: xSmall, Small, Medium, **Large (default)**, xLarge, xxLarge, xxxLarge,
  then accessibility sizes AX1–AX5 (Body reaches **53 pt** at AX5).
  Source: https://developer.apple.com/design/human-interface-guidelines/typography (Specifications)
- "Keep text truncation to a minimum as font size increases… aim to display as much
  useful text at the largest accessibility font size as you do at the largest standard
  font size."
  Source: https://developer.apple.com/design/human-interface-guidelines/typography
- At large sizes, "consider using a stacked layout where text appears above secondary
  items" (glyphs/timestamps move below text).
  Source: https://developer.apple.com/design/human-interface-guidelines/typography
- Accessibility page: "give people the option to enlarge text by **at least 200
  percent**."
  Source: https://developer.apple.com/design/human-interface-guidelines/accessibility

**Web translation notes:** use `font: -apple-system-body` etc. where supported, or map
the table above onto CSS custom properties; honor `rem`-based sizing so browser text
zoom plays the Dynamic Type role. Leading values convert directly to `line-height`
(e.g. Body 17/22 → `line-height: 22px` ≈ 1.29).

---

## 3. Materials & translucency

**Taxonomy (current, iOS 26-era):** two material types — **Liquid Glass** (functional
layer for controls/navigation) and **standard materials** (content layer).

- "Don't use Liquid Glass in the content layer… use standard materials for elements in
  the content layer, such as app backgrounds." "Use Liquid Glass effects sparingly…
  Limit these effects to the most important functional elements."
  Source: https://developer.apple.com/design/human-interface-guidelines/materials
- Liquid Glass variants: **regular** (blurs + adjusts luminosity to keep text legible;
  used by most system components) vs **clear** (highly translucent; only "for components
  that appear over visually rich backgrounds" like photos/video). With clear glass over
  bright content, "consider adding a dark dimming layer of **35% opacity**."
  Source: https://developer.apple.com/design/human-interface-guidelines/materials
- iOS/iPadOS standard materials: **ultra-thin, thin, regular (default), thick** — "which
  you can use in the content layer to help create visual distinction."
  Source: https://developer.apple.com/design/human-interface-guidelines/materials
- "Choose materials and effects based on **semantic meaning and recommended usage**.
  Avoid selecting a material or effect based on the apparent color it imparts… because
  system settings can change its appearance."
  Source: https://developer.apple.com/design/human-interface-guidelines/materials
- Thickness trade-off: "Thicker materials… provide better contrast for text and other
  elements with fine features. Thinner materials… help people retain their context."
  Source: https://developer.apple.com/design/human-interface-guidelines/materials

**`UIBlurEffect.Style` enum (API taxonomy that backs the materials):**

- Adaptable: `systemUltraThinMaterial`, `systemThinMaterial`, `systemMaterial`,
  `systemThickMaterial`, `systemChromeMaterial`
- Fixed light/dark variants of each (`…Light` / `…Dark`), plus legacy non-adaptive
  `extraLight`, `light`, `dark`, `extraDark`, `regular`, `prominent`.

Source: https://developer.apple.com/documentation/uikit/uiblureffect/style

**Vibrancy:**

- Label vibrancy levels usable on any material (except as noted): `label` (default,
  highest contrast), `secondaryLabel`, `tertiaryLabel`, `quaternaryLabel` (lowest;
  "avoid using quaternary on top of the thin and ultraThin materials, because the
  contrast is too low"). Fills: `fill`, `secondaryFill`, `tertiaryFill`. Separators have
  a single vibrancy level that "works well on all materials."
  Source: https://developer.apple.com/design/human-interface-guidelines/materials
- "Help ensure legibility by using vibrant colors on top of materials."
  Source: https://developer.apple.com/design/human-interface-guidelines/materials

**Separators / hairlines:**

- iOS defines two semantic separator colors: `separator` ("allows some underlying
  content to be visible") and `opaqueSeparator` ("doesn't allow any underlying content
  to be visible").
  Source: https://developer.apple.com/design/human-interface-guidelines/color (Specifications › iOS, iPadOS system colors)
- API: https://developer.apple.com/documentation/uikit/uicolor/separator
- The current HIG does **not** publish a hairline thickness value; the 1-physical-pixel
  hairline convention lives in Apple's design resources/templates, not in HIG text.
  (Flagged as undocumented-in-primary-HIG.)

**Web translation notes:** `backdrop-filter: blur()` + a translucent tint approximates
`systemMaterial`; there is no web equivalent of vibrancy — approximate hierarchy with
`color-mix()`/opacity steps for secondary/tertiary text. Prefer `regular`/`thick`
(more opaque) behind small text per the contrast guidance above.

---

## 4. Navigation & large titles

The HIG merged navigation-bar guidance into the **Toolbars** page in June 2025
("Updated guidance… incorporated navigation bar guidance";
https://developer.apple.com/design/human-interface-guidelines/navigation-bars now
redirects to /toolbars).

- **Large titles:** "Use a large title to help people stay oriented as they navigate and
  scroll. By default, a large title transitions to a standard title as people begin
  scrolling the content, and transitions back to large when people scroll to the top."
  Source: https://developer.apple.com/design/human-interface-guidelines/toolbars (iOS section)
  API: https://developer.apple.com/documentation/uikit/uinavigationbar/preferslargetitles
- **Titles:** "Write a concise title. Aim for a word or short phrase… keep the title
  **under 15 characters**." "Don't title windows with your app name."
  Source: https://developer.apple.com/design/human-interface-guidelines/toolbars
- **Back/Close:** "Use the standard Back and Close buttons… Prefer the standard symbols
  for each, and don't use a text label that says Back or Close."
  Source: https://developer.apple.com/design/human-interface-guidelines/toolbars
- **Item placement:** leading edge = navigation/back then title; trailing edge =
  primary action (e.g. Done), search, More menu; "aim for a maximum of three" groups.
  Source: https://developer.apple.com/design/human-interface-guidelines/toolbars
- **Bar appearance:** "Reduce the use of toolbar backgrounds and tinted controls… use a
  ScrollEdgeEffectStyle when necessary to distinguish the toolbar area from the content
  area" (i.e. bars are transparent at rest and gain a material/edge effect only when
  content scrolls under them).
  Source: https://developer.apple.com/design/human-interface-guidelines/toolbars
- **Bar heights:** the current HIG publishes **no** navigation-bar/large-title height
  values. (The widely-cited 44 pt bar / 96 pt large-title dimensions come from legacy
  HIG revisions and Apple Design Resources templates — https://developer.apple.com/design/resources/ —
  not from current HIG text. Flagged as a divergence between common belief and current
  primary documentation.)

**Web translation notes:** replicate the collapse-on-scroll pattern by interpolating the
title between 34 pt (Large Title spec) and 17 pt semibold (Headline spec) tied to
scroll position, and only apply `backdrop-filter` to the nav bar once content scrolls
beneath it (the "scroll edge effect" behavior).

---

## 5. Messaging UI conventions

**Finding: Apple does not document chat-bubble design in any primary source.** The HIG
contains no guidance on message bubble grouping, inter-bubble spacing, timestamp
placement, read receipts, or typing indicators. The only Messages-related HIG page is
"iMessage apps and stickers," which covers app extensions and sticker specs, not
transcript UI:
https://developer.apple.com/design/human-interface-guidelines/imessage-apps-and-stickers

Relevant adjacent guidance that *is* documented:

- The Messages compose sheet is cited as an example of a sheet that shows **only at full
  height** ("the compose sheets in Messages and Mail display only at full height to give
  people enough room to create content").
  Source: https://developer.apple.com/design/human-interface-guidelines/sheets
- Typing indicators map to the general Feedback principle: "it often works well to
  display status information in a passive way so that people can view it when they need
  it" — i.e. status integrated into the interface, not alerts.
  Source: https://developer.apple.com/design/human-interface-guidelines/feedback
- Accessibility: "Minimize use of time-boxed interface elements… Prefer dismissing views
  with an explicit action" — relevant to transient toast/typing UI.
  Source: https://developer.apple.com/design/human-interface-guidelines/accessibility

**Implication for the audit:** bubble radius, grouping rules, and typing-indicator style
in Rumbo can't be "HIG-checked" — they can only be checked against the general
principles (layout grouping, typography, contrast, VoiceOver ordering). Any blog
claiming "Apple recommends X for chat bubbles" is not traceable to a primary source.

---

## 6. Haptics

**When Apple says haptics are appropriate (iOS):**

- **Notification** (`UINotificationFeedbackGenerator`): "provide feedback about the
  outcome of a task or action, such as depositing a check or unlocking a vehicle" —
  i.e. **success / warning / error** after a task completes.
  Sources: https://developer.apple.com/design/human-interface-guidelines/playing-haptics ,
  https://developer.apple.com/documentation/uikit/uinotificationfeedbackgenerator
- **Impact** (`UIImpactFeedbackGenerator`, light/medium/heavy + soft/rigid in API):
  "provide a physical metaphor you can use to complement a visual experience. For
  example, people might feel a tap when a view snaps into place or a thud when two heavy
  objects collide." API doc: "trigger impact feedback when a user interface object
  collides with another object."
  Sources: https://developer.apple.com/design/human-interface-guidelines/playing-haptics ,
  https://developer.apple.com/documentation/uikit/uifeedbackgenerator ,
  https://developer.apple.com/documentation/uikit/uiimpactfeedbackgenerator
- **Selection** (`UISelectionFeedbackGenerator`): "feedback while the values of a UI
  element are changing" (e.g. scrolling a picker).
  Source: https://developer.apple.com/design/human-interface-guidelines/playing-haptics
- Standard controls (toggles, sliders, pickers) play system haptics automatically.
  Source: https://developer.apple.com/design/human-interface-guidelines/playing-haptics

**Best practices (all quotable constraints):**

- "Use system-provided haptic patterns according to their documented meanings… avoid
  using the pattern to mean something else."
- "Use haptics consistently… build a clear, causal relationship between each haptic and
  the action."
- "Prefer using haptics to **complement** other feedback" — match haptic
  intensity/sharpness to the accompanying animation.
- "**Avoid overusing haptics**… can feel just right when it happens occasionally, but
  become tiresome when it plays frequently."
- "In most apps, prefer playing **short haptics that complement discrete events**."
- "**Make haptics optional.** Let people turn off or mute haptics, and make sure people
  can still enjoy your app or game without them."

Source for all: https://developer.apple.com/design/human-interface-guidelines/playing-haptics

**Web translation notes:** the web Vibration API (`navigator.vibrate()`) is
Android/Chrome-only — iOS Safari does not implement it, so haptics are
progressive-enhancement only. Where available: map notification-success to a single
short pulse (~10 ms), error to a pattern (e.g. `vibrate([50, 50, 50])`), impact to a
single ≤10 ms pulse, and always gate behind a user setting per "Make haptics optional."
Do not attempt to replicate continuous Core Haptics patterns.

---

## 7. Motion

**WWDC 2018 Session 803, "Designing Fluid Interfaces"**
(https://developer.apple.com/videos/play/wwdc2018/803/) — the canonical Apple motion
session; all quotes below are from its transcript:

- **Springs, not durations:** "We actually like to avoid using duration when we're
  describing elastic behaviors… The spring is always moving, and it's ready to move
  somewhere [else]." Parameterize with **damping ratio** and **frequency response**
  (mass/stiffness/damping stay "behind the scenes").
- **Default to no overshoot:** "We recommend starting with **100% damping**, or no
  overshoot, when you're tuning elastic [behaviors]." "A spring doesn't need to
  overshoot."
- **Overshoot only when the gesture carries momentum:** "If the gesture that's driving
  the motion itself has momentum, then you should reward that momentum." Example given:
  in Music, tapping the Now Playing mini-bar presents with **100% damping** (no
  overshoot, because a tap has no momentum), but swipe-dismissing Now Playing uses
  **80% damping** ("a little bit of bounce and squish") because the swipe has momentum.
- **Momentum projection:** when a thrown object must pick an endpoint, "we've taken the
  velocity… mixed in the deceleration rate, and we end up with this projected position";
  the shared code uses `UIScrollView.decelerationRate` so flings land where scrolling
  intuition says they should. (Rumbo's sheet already does this — it matches Apple's
  canonical pattern.)
- **Rubber-banding = boundary communication:** "Softly indicating boundaries… the
  interface is gradually and softly letting you know that there's nothing there… it's
  always telling you that you've reached the edge." Without it "you actually wouldn't
  know the difference between a frozen phone, and a phone that's just at the top… of the
  screen."
- **Redirectable/interruptible:** interfaces should allow "constant redirection and
  interruption" — animations must be retargetable mid-flight without waiting for
  completion.
- **Latency:** "People are really, really sensitive to latency… look for delays
  everywhere. It's not just swipes. It's taps, it's presses… Everything needs to
  respond."
- **Smoothness ≠ frame rate alone:** avoid too much visual change between adjacent
  frames (strobing); techniques cited: higher frame rates, motion blur, and **motion
  stretching** (used in the iPhone X app-launch zoom).

**HIG Motion page** (https://developer.apple.com/design/human-interface-guidelines/motion):

- "Aim for **brevity and precision** in feedback animations… brief and precise… feels
  lightweight and unobtrusive."
- "In apps, generally **avoid adding motion to UI interactions that occur
  frequently**."
- "**Let people cancel motion.** As much as possible, don't make people wait for an
  animation to complete."
- "**Make motion optional**… avoid using it as the only way to communicate important
  information."
- Motion should "follow people's gestures": if a view is revealed by sliding down from
  the top, people expect to dismiss it by sliding it back up (symmetric spatial paths —
  also in the WWDC 803 transcript).

**Reduced Motion** (from the Accessibility page,
https://developer.apple.com/design/human-interface-guidelines/accessibility): when
Reduce Motion is on, "reduce automatic and repetitive animations," specifically:

- "Tightening animation springs to reduce bounce effects"
- "Tracking animations directly with people's gestures"
- "Avoiding animating depth changes in z-axis layers"
- "Replacing transitions in x-, y-, and z-axes with **fades**"
- "Avoiding animating into and out of blurs"

**Web translation notes:** Apple publishes **no duration/easing numbers** for general UI
animation in the HIG — the documented contract is behavioral (springs, damping,
interruptibility), not millisecond values. On the web: implement sheet/bubble motion
with spring integrators parameterized by damping ratio (start at ζ = 1.0), honor
`@media (prefers-reduced-motion: reduce)` by swapping transforms for opacity fades and
removing overshoot — a direct mapping of Apple's list.

---

## 8. Accessibility

**Contrast** — the Accessibility page states Accessibility Inspector uses **WCAG Level
AA** values (https://developer.apple.com/design/human-interface-guidelines/accessibility):

| Text size | Text weight | Minimum contrast |
|---|---|---|
| Up to 17 pt | All | **4.5:1** |
| 18 pt and larger | All | **3:1** |
| All sizes | Bold | **3:1** |

- "If your app doesn't provide this minimum contrast by default, ensure it at least
  provides a higher contrast color scheme when the system setting Increase Contrast is
  turned on."
- The Dark Mode page adds: "At a minimum, make sure the contrast ratio between colors is
  no lower than **4.5:1**. For custom foreground and background colors, strive for a
  contrast ratio of **7:1**, especially in small text."
  Source: https://developer.apple.com/design/human-interface-guidelines/dark-mode
- "Convey information with more than color alone" — add shapes/icons in addition to
  color (directly relevant to affinity bars and progress chips: don't encode affinity
  purely as color).
  Source: https://developer.apple.com/design/human-interface-guidelines/accessibility

**VoiceOver expectations for chat-like content**
(https://developer.apple.com/design/human-interface-guidelines/voiceover):

- "Provide alternative labels for all key interface elements" — including custom
  elements (send button needs a real label, not just an arrow glyph).
- "Exclude purely decorative images from VoiceOver."
- "**Specify how elements are grouped, ordered, or linked.** Proximity, alignment, and
  other visible contextual cues help sighted people perceive relationships… describe
  these relationships to VoiceOver" — i.e. a bubble's text, timestamp, and status must
  be announced as one logical unit in reading order (VoiceOver reads top-to-bottom,
  leading-to-trailing).
- "**Inform VoiceOver when visible content or layout changes occur**" — new incoming
  messages must be announced (API: `AccessibilityNotification`; web equivalent:
  `aria-live="polite"` on the message list).
  API: https://developer.apple.com/documentation/accessibility/accessibilitynotification
- "Use titles and headings to help people navigate your information hierarchy" — the
  large title should be a real heading.

**Control size & spacing:** see §1 (44×44 pt default / 28×28 pt minimum; 12/24 pt
padding). Source: https://developer.apple.com/design/human-interface-guidelines/accessibility

**Other directly applicable rules:**

- "Support simple gestures for common interactions… **Offer alternatives to gestures**"
  — if the sheet is swipe-dismissable, also provide a visible Close/Done button.
  Source: https://developer.apple.com/design/human-interface-guidelines/accessibility
- "Minimize use of time-boxed interface elements… Prefer dismissing views with an
  explicit action."
  Source: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Text enlargement "by at least 200 percent."
  Source: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Reduce Motion list — see §7.

---

## 9. Dark Mode

Source page: https://developer.apple.com/design/human-interface-guidelines/dark-mode

- **Supporting both appearances is treated as expected:** "In iOS, iPadOS, macOS, and
  tvOS, people often choose Dark Mode as their default interface style, and they
  generally **expect all apps and games to respect their preference**."
- "**Avoid offering an app-specific appearance setting.** An app-specific appearance
  mode option creates more work for people… they may think your app is broken because it
  doesn't respond to their systemwide appearance choice."
- "Ensure that your app looks good in **both** appearance modes" — including the **Auto**
  setting that can switch while the app is running.
- **Semantic/adaptive colors:** "Embrace colors that adapt to the current appearance…
  Avoid using hard-coded color values or colors that don't adapt." (Web equivalent:
  `prefers-color-scheme` + custom properties, or `light-dark()`.)
- **Base vs. elevated backgrounds (iOS):** "the system uses two sets of background
  colors — called **base** and **elevated** — to enhance the perception of depth when
  one dark interface is layered above another. The base colors are dimmer… the elevated
  colors are brighter, making foreground interfaces appear to advance." A modal sheet
  automatically switches from base to elevated. → In dark mode, Rumbo's bottom sheet
  should get *lighter*, not darker, than the chat background.
  API: https://developer.apple.com/documentation/uikit/uicolor/separator (semantic color example)
- **Contrast floors apply in both appearances** (4.5:1 min, 7:1 goal — see §8), and test
  with Increase Contrast + Reduce Transparency enabled.
- "**Soften the color of white backgrounds**" in content images so they don't glow
  against dark surroundings.
- Use system label colors (primary/secondary/tertiary/quaternary) which "adapt
  automatically."

---

## 10. Bottom sheets

Source page: https://developer.apple.com/design/human-interface-guidelines/sheets
API: https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller

- **Purpose:** "A sheet helps people perform a **scoped task that's closely related to
  their current context**." (Rumbo's vocational-profile sheet fits the pattern.)
- **Modal vs. nonmodal (iOS):** a sheet can be nonmodal — "people use its functionality
  to affect the parent view without dismissing the sheet" (example: Notes' formatting
  sheet). This legitimizes a persistent, peekable profile sheet over the chat.
- **Detents:** "Sheets resize according to their **detents**, which are particular
  heights at which a sheet naturally rests. The system defines two detents: **large** is
  the height of a fully expanded sheet and **medium** is about half of the fully
  expanded height. Sheets can have one or more custom detent values." "Sheets
  automatically support the large detent. Adding the medium detent allows the sheet to
  rest at both heights, whereas specifying only medium prevents the sheet from expanding
  to full height."
  API: https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/detents
- **Progressive disclosure:** "In an iPhone app, consider supporting the medium detent
  to allow progressive disclosure of the sheet's content" — most relevant items visible
  at medium, more on expand. (Maps to Rumbo: progress chips + top affinities at medium;
  full disclosure section at large.)
- **Grabber:** "**Include a grabber in a resizable sheet.** A grabber shows people that
  they can drag the sheet to resize it; they can also **tap it to cycle through the
  detents**. In addition… a grabber also works with VoiceOver so people can resize the
  sheet without seeing the screen."
  API: https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/prefersgrabbervisible
- **Swipe to dismiss:** "People expect to **swipe vertically to dismiss** a sheet
  instead of tapping a dismiss button. If people have unsaved changes… when they begin
  swiping to dismiss it, use an action sheet to let them confirm."
- **Buttons:** Cancel/Close on the **leading** edge of the sheet's top bar, Done on the
  **trailing** edge; "If you provide a Done button, always pair it with a Cancel
  button"; never show Cancel + Done + Back together.
- **Dimming:** iPadOS page/form sheets center content "on top of a dimmed background
  view"; `UISheetPresentationController` exposes `largestUndimmedDetentIdentifier` so
  dimming can be removed at/below a detent (standard pattern: undimmed at medium,
  dimmed at large).
  API: https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller (code sample)
- **One at a time:** "Display only one sheet at a time from the main interface."
- **Alternatives:** "For complex or prolonged user flows, consider alternatives to
  sheets" (full-screen modal for multistep tasks).
- Modality page: confirm before closing a modal view when closing could lose
  user-generated content.
  Source: https://developer.apple.com/design/human-interface-guidelines/modality

**Web translation notes:** detents = snap points (`medium ≈ 50%`, `large ≈ 100%` of the
sheet's expanded height); grabber = a ~36×5 pt rounded pill, itself a ≥44 pt-tall hit
zone (§1) that is both draggable and tappable-to-cycle; pair swipe-to-dismiss with a
visible close control (§8); dim the chat only at the large detent.

---

## Appendix — quick-reference values

| Token | Value | Source |
|---|---|---|
| Hit area default (iOS) | 44×44 pt | /design/human-interface-guidelines/accessibility |
| Hit area minimum (iOS) | 28×28 pt | /design/human-interface-guidelines/accessibility |
| Bezeled control padding | ~12 pt | /design/human-interface-guidelines/accessibility |
| Bezel-less control padding | ~24 pt | /design/human-interface-guidelines/accessibility |
| Body text | 17 pt Regular, leading 22 | /design/human-interface-guidelines/typography |
| Large Title | 34 pt Regular, leading 41 | /design/human-interface-guidelines/typography |
| Headline | 17 pt Semibold | /design/human-interface-guidelines/typography |
| Minimum legible text (iOS) | 11 pt | /design/human-interface-guidelines/typography |
| Body tracking @17 pt | −0.026 em | /design/human-interface-guidelines/typography |
| Contrast floor (≤17 pt text) | 4.5:1 | /design/human-interface-guidelines/accessibility |
| Contrast floor (≥18 pt or bold) | 3:1 | /design/human-interface-guidelines/accessibility |
| Contrast goal, custom colors | 7:1 | /design/human-interface-guidelines/dark-mode |
| Text enlargement support | ≥200% | /design/human-interface-guidelines/accessibility |
| Sheet detents | medium ≈ ½, large = full | /design/human-interface-guidelines/sheets |
| Clear-glass dimming layer | 35% black | /design/human-interface-guidelines/materials |
| Spring default | 100% damping (no overshoot) | /videos/play/wwdc2018/803 |
| Overshoot precedent | 80% damping, momentum gestures only | /videos/play/wwdc2018/803 |
| Title length | < 15 characters | /design/human-interface-guidelines/toolbars |
