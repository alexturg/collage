import os

import pytest

pytest.importorskip("numpy")

from src.Collage import Collage
from src.CollageImage import PILCollageImage
from src.CornerCreator import CornerCreator
from src.CollageImage import safe_open_image


@pytest.fixture
def filename():
    return os.path.join('test', 'files', 'kotya.jpg')


@pytest.fixture
def collage(tk_root):
    collage = Collage(0, 1, 1, 1, None, [tk_root], {'width': 30, 'height': 30})
    try:
        yield collage
    finally:
        collage.destroy()


@pytest.fixture
def collage_image(filename, collage):
    img = safe_open_image(filename, collage.get_corners())
    img.resize((10, 10))
    return img


def test_init(collage_image):
    assert collage_image.PIL is not None
    assert collage_image.PIL.width == 10
    assert collage_image.PIL.height == 10


def test_resize(collage_image):
    collage_image.resize((100, 150))
    assert collage_image.PIL.width == 100
    assert collage_image.PIL.height == 150


def test_big_resize(collage_image):
    collage_image.resize((1000, 800))
    assert collage_image.PIL.width == 960
    assert collage_image.PIL.height == 768
    assert 2 * collage_image.corner[0] + collage_image.PIL.width == 1000
    assert 2 * collage_image.corner[1] + collage_image.PIL.height == 800
