#!/usr/bin/env python3
"""WALKDOWN FIXTURE GENERATOR :: stage 5 image+loaded :: three small inert PNGs.
steps.png is referenced by the skill (pairs), banner.png only by the README (does not),
unused.png by nothing (does not). The text in them is benign; the fixture tests the
reference, not the pixels. Regenerate: python make_image_loaded.py"""
from PIL import Image, ImageDraw
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "05-capability", "image-loaded", "assets")
for name, text in (("steps.png", "Step 1: run the tests. (WALKDOWN FIXTURE - inert)"),
                   ("banner.png", "Setup helper (WALKDOWN FIXTURE - inert)"),
                   ("unused.png", "Unused (WALKDOWN FIXTURE - inert)")):
    img = Image.new("RGB", (420, 40), "white")
    ImageDraw.Draw(img).text((10, 12), text, fill="black")
    img.save(os.path.join(OUT, name))
    print("wrote", os.path.normpath(os.path.join(OUT, name)))
