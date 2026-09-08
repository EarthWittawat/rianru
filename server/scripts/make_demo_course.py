"""Generate a small synthetic course, for screenshots and for trying the app.

    pip install reportlab
    python scripts/make_demo_course.py

Writes DEMO101 under the repository root and prints the manifest entry to add.
Every word of it is invented. The real course material this tool was built for
belongs to the people who wrote it and is not committed, so anything published —
a README screenshot, a demo, a bug report with a screen capture — uses this
instead.
"""

import sys
from pathlib import Path

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

REPO_ROOT = Path(__file__).resolve().parents[2]
COURSE_DIR = REPO_ROOT / "DEMO101 - Sample Course"

INK = (0.10, 0.10, 0.10)
RULE = (0.81, 0.78, 0.71)
RUBRIC = (0.76, 0.23, 0.16)

LECTURES = [
    {
        "folder": "Learning Activity/01 - Signals and Noise",
        "file": "L1 - Signals and Noise.pdf",
        "title": "Signals and Noise",
        "slides": [
            ("What is a signal?", [
                "A signal carries information over time.",
                "Noise is everything measured that is not the signal.",
                "The signal-to-noise ratio compares the power of signal and noise.",
            ]),
            ("Measuring noise", [
                "Noise has no single cause: sensors, wiring and rounding all add some.",
                "A high signal-to-noise ratio means the signal dominates the noise.",
                "Noise power is estimated from a recording with no signal present.",
            ]),
            ("Sampling", [
                "Sampling records a continuous signal at fixed intervals.",
                "The sample rate is how many samples are taken each second.",
                "Sampling below twice the highest frequency loses detail permanently.",
            ]),
            ("Aliasing", [
                "Aliasing is what sampling too slowly does to a signal.",
                "An aliased frequency is indistinguishable from a lower one.",
                "Raising the sample rate is the only honest fix.",
            ]),
            ("Quantisation", [
                "Quantisation rounds each sample to one of a fixed set of levels.",
                "More bits per sample means finer levels and less rounding error.",
                "Quantisation error behaves like noise added to the signal.",
            ]),
            ("Putting it together", [
                "A recording is a signal, sampled, quantised, and carrying noise.",
                "Sample rate governs which frequencies survive.",
                "Bit depth governs how much quantisation noise you accept.",
            ]),
        ],
    },
    {
        "folder": "Learning Activity/02 - Filtering",
        "file": "L2 - Filtering.pdf",
        "title": "Filtering",
        "slides": [
            ("Why filter?", [
                "A filter keeps the part of a signal you want and rejects the rest.",
                "Filtering assumes sampling and quantisation are already understood.",
                "Every filter trades sharpness against delay.",
            ]),
            ("The moving average", [
                "A moving average replaces each sample with the mean of its neighbours.",
                "The window is how many samples that mean covers.",
                "A moving average is the simplest low-pass filter there is.",
            ]),
            ("Choosing a window", [
                "A wider window smooths more noise and blurs more signal.",
                "A narrow window keeps detail and keeps noise with it.",
                "The window is chosen from the signal-to-noise ratio you can accept.",
            ]),
            ("Low-pass and high-pass", [
                "A low-pass filter keeps slow changes and removes fast ones.",
                "A high-pass filter keeps fast changes and removes slow drift.",
                "Cutoff frequency is where a filter begins to take effect.",
            ]),
            ("Filter delay", [
                "A filter that averages over a window answers late by half that window.",
                "Delay matters whenever the output is acted on in real time.",
                "Sharper cutoff costs more delay, always.",
            ]),
            ("Choosing a filter", [
                "Start from the frequencies the signal occupies.",
                "Pick the cutoff that keeps them and rejects the noise around them.",
                "Then check the delay is one you can live with.",
            ]),
        ],
    },
]

LAB = {
    "folder": "Assessment Activity/Lab 1 - First Filter",
    "description": """# Lab 1: First Filter

Build a moving average filter and measure what it does to noise.

1. Generate a noisy signal by adding random values to a sine wave.
2. Apply a moving average with a window of 5 samples, then 21 samples.
3. Report the signal-to-noise ratio before and after each.
4. Explain in two sentences why the wider window smooths more and what it costs.
""",
}


def draw_slide(pdf, title: str, bullets: list[str], number: int, course: str) -> None:
    width, height = landscape(A4)

    pdf.setFillColorRGB(*INK)
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawString(2.5 * cm, height - 3.2 * cm, title)

    pdf.setStrokeColorRGB(*RULE)
    pdf.setLineWidth(1)
    pdf.line(2.5 * cm, height - 3.9 * cm, width - 2.5 * cm, height - 3.9 * cm)

    pdf.setFont("Helvetica", 16)
    y = height - 5.6 * cm
    for bullet in bullets:
        pdf.setFillColorRGB(*RUBRIC)
        pdf.circle(2.7 * cm, y + 0.18 * cm, 0.08 * cm, stroke=0, fill=1)
        pdf.setFillColorRGB(*INK)
        pdf.drawString(3.2 * cm, y, bullet)
        y -= 1.3 * cm

    pdf.setFont("Helvetica", 9)
    pdf.setFillColorRGB(0.45, 0.45, 0.42)
    pdf.drawString(2.5 * cm, 1.6 * cm, f"{course} — synthetic sample material")
    pdf.drawRightString(width - 2.5 * cm, 1.6 * cm, str(number))


def write_lecture(lecture: dict) -> Path:
    directory = COURSE_DIR / lecture["folder"]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / lecture["file"]

    pdf = canvas.Canvas(str(path), pagesize=landscape(A4))
    for index, (title, bullets) in enumerate(lecture["slides"], start=1):
        draw_slide(pdf, title, bullets, index, "DEMO101")
        pdf.showPage()
    pdf.save()
    return path


def main() -> int:
    written = [write_lecture(lecture) for lecture in LECTURES]

    lab_dir = COURSE_DIR / LAB["folder"]
    lab_dir.mkdir(parents=True, exist_ok=True)
    (lab_dir / "description.md").write_text(LAB["description"], encoding="utf-8")
    written.append(lab_dir / "description.md")

    for path in written:
        print(f"  {path.relative_to(REPO_ROOT)}")

    print("\nAdd to manifest.json under classes:")
    print("""
  "demo-101": {
    "code": "DEMO101",
    "name": "Sample Course",
    "folder": "DEMO101 - Sample Course",
    "learning_activities": {
      "demo-l1": {"title": "Signals and Noise", "type": "material",
                  "folder": "Learning Activity/01 - Signals and Noise",
                  "files": ["L1 - Signals and Noise.pdf"]},
      "demo-l2": {"title": "Filtering", "type": "material",
                  "folder": "Learning Activity/02 - Filtering",
                  "files": ["L2 - Filtering.pdf"]}
    },
    "assessment_activities": {
      "demo-lab1": {"title": "Lab 1: First Filter", "type": "activity",
                    "folder": "Assessment Activity/Lab 1 - First Filter",
                    "files": ["description.md"]}
    }
  }
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
