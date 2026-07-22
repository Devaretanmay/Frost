# Creating a Demo Video with Dynamic Zooms & Motion Blur

To achieve smooth auto-zooms, camera panning, background blur, and spotlight callouts, use one of the following 3 workflows:

---

## Option 1: Screen Studio (Automated 4K Auto-Zooms)

[Screen Studio](https://www.screen.studio) is the industry standard for developer tool launch videos on macOS. It automatically detects terminal activity, text highlights, and mouse movements, applying smooth 4K camera inertia and dynamic zooms automatically.

### Step-by-Step Screen Studio Setup:

1. **Terminal Setup**:
   - Open your terminal (iTerm2, Ghostty, or Warp).
   - Set theme to **Catppuccin Macchiato** or **Tokyo Night**.
   - Font size: `18pt` JetBrains Mono.
   - Window size: `1200 x 720`.

2. **Record Screen Studio**:
   - Launch Screen Studio and select the Terminal window.
   - Run the automated CLI demo script or perform the walkthrough.

3. **Preset Adjustments for FROST Launch**:
   - **Background**: Dark Navy / Deep Blur (`#0D1117`).
   - **Window Corner Radius**: `16px` with soft drop shadow (`Blur: 30px, Y: 10px`).
   - **Zoom In Points**:
     - ⏱️ `0:18` — Auto-zoom on `frost doctor` green diagnostic checkmarks (`Zoom: 130%`).
     - ⏱️ `0:48` — Smooth zoom into `[UNCERTAINTY POINT DETECTED]` banner (`Zoom: 145%`).
     - ⏱️ `1:25` — Zoom into `Branch B: Oscillation Loop [KILLED]` red badge (`Zoom: 140%`).
     - ⏱️ `1:45` — Full zoom into `54/54 Passed GREEN (100%)` (`Zoom: 150%`).

4. **Export**: Select **4K / 60 FPS MP4**.

---

## Option 2: Code-Driven Video Generation with Remotion (React)

If you prefer programmatic, frame-perfect code-driven video generation (100% reproducible via code), use **Remotion** (`remotion.dev`).

### Remotion Camera Zoom Component Example (`DemoVideo.tsx`):

```tsx
import { interpolate, useCurrentFrame, Spring, Composition } from "remotion";
import { TerminalWindow } from "./TerminalWindow";

export const FrostDemoVideo = () => {
  const frame = useCurrentFrame();

  // Dynamic Camera Zoom Keyframes
  const scale = interpolate(
    frame,
    [0, 30, 45, 75, 90, 110], // Frames
    [1.0, 1.0, 1.35, 1.35, 1.0, 1.5], // Zoom Factor
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const translateY = interpolate(
    frame,
    [45, 75, 90, 110],
    [-20, -20, 0, -40],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        width: 1920,
        height: 1080,
        backgroundColor: "#0b0f19",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          transform: `scale(${scale}) translateY(${translateY}px)`,
          transition: "transform 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        <TerminalWindow />
      </div>
    </div>
  );
};
```

---

## Option 3: Manual Video Editor Keyframes (CapCut / Premiere Pro / DaVinci Resolve)

If using traditional video editing software (CapCut, Premiere Pro, Final Cut, DaVinci):

### Keyframe Coordinate Matrix:

| Timestamp | Event | Zoom Scale | Position Offset (X, Y) | Easing Curve |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 - 0:15** | Problem Statement | `100%` | `(0, 0)` | Linear |
| **0:18** | `frost doctor` output | `130%` | `(0, -50px)` | Ease Out Cubic |
| **0:45** | `UNCERTAINTY DETECTED` | `145%` | `(0, -100px)` | Ease Out Exponential |
| **1:15** | Micro-Branch Spawning | `135%` | `(-50px, -20px)` | Smooth Pan |
| **1:30** | Loop Engine Kills Branch B | `150%` | `(0, +60px)` | Snappy Punch-In |
| **1:45** | `54/54 Passed GREEN` | `160%` | `(0, -120px)` | Ease Out Back |
| **1:55** | Final Call to Action | `100%` | `(0, 0)` | Smooth Zoom Out |

---

## Audio Design & Visual Polish Guidelines

1. **Sound Effects (SFX)**:
   - **Subtle Mechanical Keyboard Clicks**: Low opacity sound during command typing.
   - **Deep Tech Whoosh**: Plays on camera zoom punch-ins (`0:45` and `1:30`).
   - **High Tech Chime**: Plays when `Branch A: WINNER MERGED` turns GREEN.

2. **Motion Blur & Glow**:
   - Enable `180° Shutter Angle` motion blur during camera pans.
   - Add a subtle green drop-shadow glow (`#00f0ff` / `#10b981`) around the terminal window when FROST finishes execution.
