"""
generators/__init__.py

Exports every concrete generator class so that GeneratorRegistry
can import them from a single location.
"""

from tools.generators.blur import BlurGenerator
from tools.generators.brightness import BrightnessGenerator
from tools.generators.copy_move import CopyMoveGenerator
from tools.generators.jpeg import JpegGenerator
from tools.generators.logo import LogoGenerator
from tools.generators.noise import NoiseGenerator
from tools.generators.signature import SignatureGenerator
from tools.generators.text import TextGenerator

__all__ = [
    "BlurGenerator",
    "BrightnessGenerator",
    "CopyMoveGenerator",
    "JpegGenerator",
    "LogoGenerator",
    "NoiseGenerator",
    "SignatureGenerator",
    "TextGenerator",
]
