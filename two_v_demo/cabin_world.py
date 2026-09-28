"""The Cabin World: the one scene every re-render is set in.

A hilltop at sunset: the raw-wedge simulator's own 2V dome standing on its
pad, two crown triangles still to go up, a builder reaching for the gap, and
in the foreground everything it came from -- the log with its end grain and
its eight rip cuts, the stump with the chainsaw on it, the stack of members,
the chips. :mod:`wedge_book.cover_scene` builds every object; this module is
how films use them, so that a film about the wedge dome shows the
simulator's dome, not a sketch of one.

Two ways in, sharing one world:

**Inside a masterclass lesson** (narration, captions, phone cut, release
folder all come from the standard exporter)::

    from two_v_demo import cabin_world as cw

    def paint(app, opaque, transparent, p):
        cw.paint(app)                       # the whole world, cached on the GPU
        opaque.box(...)                     # plus this chapter's own geometry

    Lesson(..., scenes={"stage": paint}, ground="off",
           backdrop=cw.backdrop, light=cw.LIGHT, camera_fn=...)

**Standalone**, for a short without narration (the cold open)::

    studio = cw.Studio(1920, 1080)
    image = studio.frame(eye, target, fov, extra=[batch], hide={"builder"})

Landmarks -- where the log end, the saw, the gap, the builder are -- come from
:func:`landmarks`, so a camera or a callout never hard-codes a position that
the scene might later move.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .render_kit import (SCENE_FRAGMENT_SHADER, SCENE_VERTEX_SHADER,
                         TriangleBatch, look_at, perspective)

LAYERS = ("ground", "forest", "deck", "dome", "builder", "props")
"""Everything in the world, by name. Hide any of them per frame."""

HERO_EYE = (1.10, -12.2, 3.30)
"""The side the world is dressed for: the cover's camera, south of the dome.
The missing crown triangles and the builder face this way."""

LIGHT = (0.55, 0.70, -0.45)
"""The low sun, as the direction its light travels -- the cover's."""

FONT_HEAVY = "C:/Windows/Fonts/ROCKEB.TTF"   # the cover's Rockwell Extra Bold
FONT_BOLD = "C:/Windows/Fonts/ROCKB.TTF"


def _scene():
    from wedge_book import cover_scene
    return cover_scene


@dataclass(frozen=True)
class Landmarks:
    """Named places in the world, in metres, z up. Read, never retype."""

    log_end: np.ndarray        # centre of the split end of the log
    log_axis: np.ndarray       # unit, from the split end into the log
    trunk_r: float
    stump_top: np.ndarray
    saw: np.ndarray            # where the chainsaw sits on the stump
    stack: np.ndarray          # the member stack's near corner
    deck_centre: np.ndarray    # top surface of the pad
    deck_r: float
    dome_centre: np.ndarray    # centre of the dome's sphere
    dome_r: float
    apex: np.ndarray
    gap: np.ndarray            # the unfinished crown
    gap_dir: np.ndarray        # unit, horizontal, toward the gap
    builder: np.ndarray        # where the builder stands
    long_member: float
    short_member: float
    splits: int


@lru_cache(maxsize=None)
def _gap():
    cs = _scene()
    eye = np.array(HERO_EYE)
    faces = cs.crown_gap_faces(2, math.degrees(math.atan2(eye[1], eye[0])) + 40)
    model = cs.cover_model()
    centre = np.mean([model.topology.faces[i].center for i in faces], axis=0)
    gap_dir = np.array([centre[0], centre[1], 0.0])
    return faces, gap_dir / np.linalg.norm(gap_dir)


def missing_faces() -> tuple[int, ...]:
    """The crown triangles not yet up -- the solver's face indices."""
    return tuple(_gap()[0])


@lru_cache(maxsize=None)
def landmarks() -> Landmarks:
    """Named places in the world -- the log end, the saw, the gap, the builder."""
    cs = _scene()
    s = cs.sizes()
    _faces, gap_dir = _gap()
    # The log and its props, as cover_scene.props lays them out.
    log_end = np.array([-0.55, -6.35, s.trunk_r])
    axis = np.array([-0.18, 1.0, 0.0])
    stump = np.array([-1.55, -4.55, 0.0])
    centre = np.array([0.0, 0.0, cs.DECK_TOP + 0.02])
    return Landmarks(
        log_end=log_end, log_axis=axis / np.linalg.norm(axis), trunk_r=s.trunk_r,
        stump_top=stump + [0, 0, 0.421], saw=stump + [-0.06, 0.02, 0.422],
        stack=np.array([1.45, -6.55, 0.0]),
        deck_centre=np.array([0.0, 0.0, cs.DECK_TOP]), deck_r=s.deck_r,
        dome_centre=centre, dome_r=s.dome_r, apex=centre + [0, 0, s.dome_r],
        gap=np.array([gap_dir[0] * s.dome_r * 0.62, gap_dir[1] * s.dome_r * 0.62,
                      cs.DECK_TOP + s.dome_r * 0.93]),
        gap_dir=gap_dir,
        builder=np.array([gap_dir[0] * s.dome_r * 0.42, gap_dir[1] * s.dome_r * 0.42,
                          cs.DECK_TOP]),
        long_member=s.long_member, short_member=s.short_member, splits=s.splits)


@lru_cache(maxsize=None)
def layer(name: str) -> TriangleBatch:
    """One layer of the world, built once per process."""
    cs = _scene()
    s = cs.sizes()
    faces, gap_dir = _gap()
    if name == "ground":
        return cs.ground_batch()
    if name == "forest":
        return cs.forest()
    if name == "deck":
        return cs.deck_batch(s)
    if name == "dome":
        return cs.dome_batch(s, faces)[0]
    if name == "builder":
        return cs.builder(s, gap_dir)
    if name == "props":
        return cs.props(s, np.array(HERO_EYE))
    raise KeyError(f"no layer {name!r}; the world has {', '.join(LAYERS)}")


def subject_points(name: str) -> list[np.ndarray]:
    """What a phone cut should keep in frame for a layer: the dome and pad
    are the subject; ground and forest are scenery and give none."""
    m = landmarks()
    if name == "dome":
        r = m.dome_r
        return [m.dome_centre + [x * r, y * r, 0] for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1))] + [m.apex]
    if name == "deck":
        return [m.deck_centre + [x * m.deck_r, y * m.deck_r, 0]
                for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    return []


# ----------------------------------------------------------------------
# Inside a lesson: the app's hooks
# ----------------------------------------------------------------------

def paint(app, hide=(), subject: bool = True) -> None:
    """Hand the world to the masterclass renderer, uploaded once, drawn every frame.

    Call from a scene painter. The lesson should set ``ground="off"``,
    ``backdrop=backdrop`` and ``light=LIGHT``. Pass ``subject=False`` when the
    chapter is about something else in the world (a close-up on the bench), so
    a phone cut frames that rather than the whole dome.
    """
    for name in LAYERS:
        if name not in hide:
            app.static_layer(f"cabin:{name}", lambda n=name: layer(n),
                             subject_points(name) if subject else None)


def horizon_row(eye, target, mvp, width: int, height: int) -> float:
    """The screen row the horizon falls on, through the frame's own matrix."""
    eye, target = np.asarray(eye, float), np.asarray(target, float)
    level = np.array([target[0] - eye[0], target[1] - eye[1], 0.0])
    if np.linalg.norm(level) < 1e-9:
        return -1.0e6   # looking straight down: no sky in frame
    far = eye + level / np.linalg.norm(level) * 1000.0
    clip = np.asarray(mvp, float) @ np.array([*far, 1.0])
    if clip[3] <= 0:
        return -1.0e6
    return (1 - (clip[1] / clip[3] * 0.5 + 0.5)) * height


_SKIES: dict = {}


def sky(width: int, height: int, horizon: float) -> np.ndarray:
    """The painted sunset for a horizon row, cached: the sky depends on
    nothing else, so a slow camera reuses it for many frames."""
    row = int(round(max(-height, min(2 * height, horizon))))
    key = (width, height, row)
    if key not in _SKIES:
        if len(_SKIES) > 64:
            _SKIES.clear()
        _SKIES[key] = _scene().backdrop(width, height, row)
    return _SKIES[key]


def backdrop(app, eye, target, mvp, width: int, height: int) -> np.ndarray:
    """``Lesson.backdrop``: the sunset behind the world."""
    return sky(width, height, horizon_row(eye, target, mvp, width, height))


# ----------------------------------------------------------------------
# Standalone: the studio
# ----------------------------------------------------------------------

class Studio:
    """An offscreen camera on the world: one context, the world uploaded once.

    ``frame`` returns a finished picture -- world, anything extra for this
    frame, the painted sky behind, and the cover's golden-hour grade.
    """

    def __init__(self, width: int, height: int, samples: int = 8):
        import moderngl

        self.width, self.height = width, height
        self.ctx = ctx = moderngl.create_standalone_context()
        self.program = ctx.program(vertex_shader=SCENE_VERTEX_SHADER,
                                   fragment_shader=SCENE_FRAGMENT_SHADER)
        self.vaos = {}
        for name in LAYERS:
            data = np.asarray(layer(name).vertices, dtype="f4")
            vbo = ctx.buffer(data.tobytes())
            self.vaos[name] = (vbo, self._vao(vbo))
        self.ms = ctx.framebuffer(
            color_attachments=[ctx.renderbuffer((width, height), samples=samples)],
            depth_attachment=ctx.depth_renderbuffer((width, height), samples=samples))
        self.out = ctx.framebuffer(color_attachments=[ctx.texture((width, height), 4)])
        self.program["u_light"].value = LIGHT

    def _vao(self, vbo):
        return self.ctx.vertex_array(self.program, [(vbo, "3f 3f 4f", "in_position",
                                                     "in_normal", "in_color")])

    def frame(self, eye, target, fov, extra=(), hide=(), grade: bool = True) -> np.ndarray:
        import moderngl

        w, h = self.width, self.height
        eye, target = np.asarray(eye, float), np.asarray(target, float)
        mvp = perspective(fov, w / h, 0.05, 400.0) @ look_at(eye, target)
        self.program["u_mvp"].write(np.ascontiguousarray(mvp.T).astype("f4").tobytes())
        self.program["u_camera"].value = tuple(float(v) for v in eye)
        extras = [np.asarray(b.vertices, dtype="f4") for b in extra if b.vertices]
        extra_vbo = self.ctx.buffer(np.concatenate(extras).tobytes()) if extras else None
        extra_vao = self._vao(extra_vbo) if extra_vbo is not None else None
        grabs = []
        # Rendered over black and over white, which gives an exact matte for the sky.
        for clear in (0.0, 1.0):
            self.ms.use()
            self.ctx.enable(moderngl.DEPTH_TEST)
            self.ctx.clear(clear, clear, clear, 1.0)
            for name, (_vbo, vao) in self.vaos.items():
                if name not in hide:
                    vao.render()
            if extra_vao is not None:
                extra_vao.render()
            self.ctx.copy_framebuffer(self.out, self.ms)
            raw = np.frombuffer(self.out.read(components=3), dtype=np.uint8).reshape(h, w, 3)
            grabs.append(np.flipud(raw).astype(np.float32) / 255.0)
        if extra_vao is not None:
            extra_vao.release()
            extra_vbo.release()
        black, white = grabs
        alpha = np.clip(1.0 - (white - black).mean(axis=2), 0.0, 1.0)[..., None]
        colour = np.where(alpha > 1e-3, black / np.maximum(alpha, 1e-3), 0.0)
        img = np.clip(colour, 0, 1) * alpha + sky(w, h, horizon_row(eye, target, mvp, w, h)) * (1 - alpha)
        return _scene().grade(img) if grade else img

    def release(self) -> None:
        self.ctx.release()


# ----------------------------------------------------------------------
# Lettering, in the cover's type
# ----------------------------------------------------------------------

def _fit(font_path: str, text: str, size: int, width: float) -> ImageFont.FreeTypeFont:
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    while size > 10:
        font = ImageFont.truetype(font_path, size)
        if probe.textlength(text, font=font) <= width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, size)


def letter(img: np.ndarray, lines, strength: float = 1.0, top: float = 0.10) -> np.ndarray:
    """Centred lines of type over a frame, with a soft shadow.

    ``lines`` is ``[(text, "heavy" | "bold", share_of_short_side), ...]``; each
    line is shrunk to fit 86% of the frame's width.
    """
    if strength <= 0:
        return img
    h, w, _ = img.shape
    base = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    layer_ = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer_)
    short = min(w, h)
    y = int(h * top)
    alpha = int(255 * min(1.0, strength))
    for text, weight, share in lines:
        font = _fit(FONT_HEAVY if weight == "heavy" else FONT_BOLD, text,
                    int(short * share), w * 0.86)
        box = draw.textbbox((0, 0), text, font=font)
        x = (w - (box[2] - box[0])) / 2
        draw.text((x + 3, y + 3), text, font=font, fill=(20, 12, 6, int(alpha * 0.55)))
        draw.text((x, y), text, font=font, fill=(255, 244, 226, alpha))
        y += box[3] + int(short * 0.022)
    out = Image.alpha_composite(base, layer_).convert("RGB")
    return np.asarray(out, dtype=np.float32) / 255.0


def lower_third(img: np.ndarray, title: str, detail: str = "", strength: float = 1.0) -> np.ndarray:
    """A caption band low in the frame: one bold line, an optional smaller one."""
    if strength <= 0:
        return img
    h, w, _ = img.shape
    base = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    band = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(band)
    short = min(w, h)
    a = min(1.0, strength)
    big = _fit(FONT_BOLD, title, int(short * 0.050), w * 0.84)
    small = _fit(FONT_BOLD, detail, int(short * 0.030), w * 0.84) if detail else None
    th = draw.textbbox((0, 0), title, font=big)[3]
    dh = draw.textbbox((0, 0), detail, font=small)[3] if small else 0
    pad = int(short * 0.025)
    top = int(h * 0.80) - th - dh - pad
    draw.rectangle((0, top - pad, w, top + th + dh + pad * 2), fill=(18, 12, 8, int(150 * a)))
    draw.text((int(w * 0.08), top), title, font=big, fill=(255, 244, 226, int(255 * a)))
    if small:
        draw.text((int(w * 0.08), top + th + pad // 2), detail, font=small,
                  fill=(240, 205, 150, int(255 * a)))
    out = Image.alpha_composite(base, band).convert("RGB")
    return np.asarray(out, dtype=np.float32) / 255.0


def validate_cabin_world() -> None:
    m = landmarks()
    assert set(LAYERS) == {"ground", "forest", "deck", "dome", "builder", "props"}
    assert m.dome_r > 1.0 and m.deck_r > m.dome_r, "the pad is wider than the dome"
    assert m.apex[2] > m.deck_centre[2] + m.dome_r * 0.99
    assert abs(np.linalg.norm(m.gap_dir) - 1) < 1e-9 and abs(np.linalg.norm(m.log_axis) - 1) < 1e-9
    # The gap and the builder turn toward the hero side.
    assert np.dot(m.gap_dir[:2], np.array(HERO_EYE[:2]) / np.linalg.norm(HERO_EYE[:2])) > 0.3
    # Horizon: a level camera puts it at mid-frame.
    eye, target = np.array([0.0, -10.0, 2.0]), np.array([0.0, 0.0, 2.0])
    mvp = perspective(50.0, 16 / 9, 0.05, 400.0) @ look_at(eye, target)
    assert abs(horizon_row(eye, target, mvp, 1920, 1080) - 540) < 1.0
