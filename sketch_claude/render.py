"""The renderer: the model drawn the way a SketchUp plan set draws, or lit for a showcase.

One offscreen OpenGL pass (moderngl, the same standalone context the films use), with:

* flat-shaded faces and inked edges -- the edges are each solid's real corners, drawn as
  screen-space quads so they keep their weight at any size;
* a sun with a shadow map, a sky and a hemisphere fill, fog to the horizon;
* glass drawn after everything else, back to front;
* up to four warm point lights for a lived-in interior and a night exterior;
* supersampling and a little bloom, then out as a PIL image.

``Camera.project`` maps model points to pixels of the finished image, so the plan sheets
can hang a label off the exact corner it names.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np
from PIL import Image, ImageFilter

from .model import MATERIALS, Model, Piece

_CTX = None


def ctx():
    global _CTX
    if _CTX is None:
        import moderngl
        _CTX = moderngl.create_standalone_context(require=330)
    return _CTX


def hex_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# ----------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------

def _look(eye, target, up):
    f = np.asarray(target, float) - np.asarray(eye, float)
    f /= np.linalg.norm(f)
    s = np.cross(f, up)
    if np.linalg.norm(s) < 1e-9:
        s = np.cross(f, [0, 1.0, 0])
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[:3, 3] = -m[:3, :3] @ np.asarray(eye, float)
    return m


@dataclass
class Camera:
    eye: tuple
    target: tuple
    fov: float = 35.0                 # degrees, vertical; 0 means orthographic
    ortho_h: float = 6.0              # visible height for an orthographic camera, metres
    up: tuple = (0, 0, 1.0)
    near: float = 0.05
    far: float = 200.0
    width: int = 1600
    height: int = 1000

    def view(self) -> np.ndarray:
        return _look(self.eye, self.target, np.asarray(self.up, float))

    def proj(self) -> np.ndarray:
        a = self.width / self.height
        n, f = self.near, self.far
        if self.fov <= 0:
            h = self.ortho_h / 2
            w = h * a
            m = np.eye(4)
            m[0, 0], m[1, 1], m[2, 2], m[2, 3] = 1 / w, 1 / h, -2 / (f - n), -(f + n) / (f - n)
            return m
        t = 1 / math.tan(math.radians(self.fov) / 2)
        m = np.zeros((4, 4))
        m[0, 0], m[1, 1] = t / a, t
        m[2, 2], m[2, 3] = (f + n) / (n - f), 2 * f * n / (n - f)
        m[3, 2] = -1
        return m

    def mvp(self) -> np.ndarray:
        return self.proj() @ self.view()

    def project(self, pts) -> np.ndarray:
        """Model points -> (x, y) pixels of the finished image, y down."""
        P = np.atleast_2d(np.asarray(pts, float))
        h = np.hstack([P, np.ones((len(P), 1))]) @ self.mvp().T
        ndc = h[:, :3] / h[:, 3:4]
        x = (ndc[:, 0] + 1) / 2 * self.width
        y = (1 - ndc[:, 1]) / 2 * self.height
        return np.stack([x, y], axis=1)


def framed(points, direction, fov=30.0, width=1600, height=1000, margin=1.12, target=None, ortho=False, up=(0, 0, 1.0)) -> Camera:
    """A camera looking along ``direction`` that fits every point in the frame."""
    P = np.asarray(points, float)
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    c = P.mean(axis=0) if target is None else np.asarray(target, float)
    view = _look(c - d, c, np.asarray(up, float))
    q = (np.hstack([P, np.ones((len(P), 1))]) @ view.T)[:, :3]
    a = width / height
    if ortho:
        hx = max(abs(q[:, 0]).max() * 2 / a, abs(q[:, 1]).max() * 2)
        # re-centre on the points' box in the view plane
        cx = (q[:, 0].max() + q[:, 0].min()) / 2
        cy = (q[:, 1].max() + q[:, 1].min()) / 2
        inv = np.linalg.inv(view)
        c2 = (inv @ np.array([cx, cy, -1.0, 1.0]))[:3] + d
        span = (q[:, 2].max() - q[:, 2].min())
        eye = c2 - d * (span + 20)
        h2 = max((q[:, 0].max() - q[:, 0].min()) / a, q[:, 1].max() - q[:, 1].min())
        return Camera(tuple(eye), tuple(c2), 0.0, h2 * margin, up, 0.05, span + 60, width, height)
    t = math.tan(math.radians(fov) / 2)
    dist = 0.0
    for x, y, z in q:
        depth = -z
        need = max(abs(y) / t, abs(x) / (t * a)) * margin
        dist = max(dist, need - depth + 1.0)    # q is measured from an eye one unit back
    eye = c - d * dist
    return Camera(tuple(eye), tuple(c), fov, 0, up, max(0.05, dist / 200), dist * 6 + 50, width, height)


# ----------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------

@dataclass
class Style:
    name: str = "sketch"
    sky: str = "paper"                # paper | day | dusk | night | white
    edges: bool = True
    edge_px: float = 1.6
    edge_color: tuple = (0.10, 0.09, 0.08)
    shadows: bool = True
    sun_dir: tuple = (-0.45, -0.75, 0.75)   # towards the sun
    sun: float = 0.62
    ambient: float = 0.55
    palette: str = "material"         # material | mono | xray
    fog: float = 0.0
    tone: str = "flat"                # flat (sketch) | aces (photographic)
    exposure: float = 1.0
    bloom: float = 0.0
    lights: list = field(default_factory=list)  # [(pos, rgb, power)]
    ground: str | None = None         # override the ground's colour
    xray: float = 0.0                 # opacity multiplier for every face when > 0
    saturation: float = 1.0
    sun_color: tuple = (1.0, 0.98, 0.94)
    sky_color: tuple = (0.82, 0.88, 0.95)
    skin_edges: float = 1.0           # how dark the skin's seams and shingle courses are inked


SKETCH = Style()
MONO = Style("mono", palette="mono", shadows=True, sun=0.55, ambient=0.6)
XRAY = Style("xray", palette="material", xray=0.45, shadows=False)
HIDDEN = Style("hidden", palette="mono", shadows=False, sun=0.0, ambient=1.0, sky="white", skin_edges=0.3)
DAY = Style("day", sky="day", edges=True, edge_px=1.0, edge_color=(0.16, 0.13, 0.11), sun=2.6, ambient=0.75,
            tone="aces", exposure=0.95, fog=0.012, bloom=0.08, sun_dir=(-0.55, -0.6, 0.55), skin_edges=0.45)
GOLDEN = Style("golden", sky="dusk", edges=True, edge_px=0.9, edge_color=(0.18, 0.12, 0.09), sun=3.1, ambient=0.55,
               tone="aces", exposure=1.0, fog=0.018, bloom=0.18, sun_dir=(-0.8, -0.45, 0.22),
               sun_color=(1.0, 0.72, 0.45), sky_color=(0.62, 0.62, 0.78), skin_edges=0.4)
NIGHT = Style("night", sky="night", edges=True, edge_px=0.8, edge_color=(0.05, 0.05, 0.07), sun=0.9, ambient=0.55,
              skin_edges=0.3, tone="aces", exposure=1.5, fog=0.02, bloom=0.55, sun_dir=(0.3, 0.6, 0.6),
              sun_color=(0.55, 0.65, 1.0), sky_color=(0.12, 0.16, 0.30))
INTERIOR = Style("interior", sky="day", edges=True, edge_px=0.9, edge_color=(0.16, 0.12, 0.1), sun=2.2, ambient=0.5,
                 tone="aces", exposure=1.1, fog=0.0, bloom=0.25, sun_dir=(-0.5, -0.6, 0.6), skin_edges=0.5)
STYLES = {s.name: s for s in (SKETCH, MONO, XRAY, HIDDEN, DAY, GOLDEN, NIGHT, INTERIOR)}


# ----------------------------------------------------------------------
# Shaders
# ----------------------------------------------------------------------

_VS = """
#version 330
uniform mat4 mvp;
uniform mat4 light_mvp;
in vec3 in_pos; in vec3 in_nrm; in vec4 in_col; in float in_emit;
out vec3 v_pos; out vec3 v_nrm; out vec4 v_col; out float v_emit; out vec4 v_light;
void main(){
  v_pos = in_pos; v_nrm = in_nrm; v_col = in_col; v_emit = in_emit;
  v_light = light_mvp * vec4(in_pos, 1.0);
  gl_Position = mvp * vec4(in_pos, 1.0);
}
"""

_FS = """
#version 330
uniform vec3 sun_dir; uniform vec3 sun_col; uniform float sun_k; uniform float amb_k;
uniform vec3 sky_col; uniform vec3 eye; uniform float fog_k; uniform vec3 fog_col;
uniform sampler2DShadow shadow; uniform int use_shadow; uniform float shadow_texel;
uniform vec4 clip_plane; uniform int use_clip;
uniform int n_lights; uniform vec3 l_pos[4]; uniform vec3 l_col[4];
uniform int tone; uniform float exposure; uniform float alpha_k; uniform float sat;
in vec3 v_pos; in vec3 v_nrm; in vec4 v_col; in float v_emit; in vec4 v_light;
out vec4 frag;
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.0,1.0); }
void main(){
  if (use_clip == 1 && dot(vec4(v_pos,1.0), clip_plane) > 0.0) discard;
  vec3 n = normalize(v_nrm);
  vec3 V = normalize(eye - v_pos);
  if (dot(n, V) < 0.0) n = -n;
  float sh = 1.0;
  if (use_shadow == 1) {
    vec3 p = v_light.xyz / v_light.w * 0.5 + 0.5;
    if (p.x > 0.0 && p.x < 1.0 && p.y > 0.0 && p.y < 1.0) {
      float s = 0.0;
      for (int i=-1;i<=1;i++) for (int j=-1;j<=1;j++)
        s += texture(shadow, vec3(p.xy + vec2(i,j)*shadow_texel, p.z - 0.0012));
      sh = s / 9.0;
    }
  }
  vec3 base = v_col.rgb;
  float lam = max(dot(n, normalize(sun_dir)), 0.0);
  float hemi = 0.5 + 0.5 * n.z;
  vec3 col;
  if (tone == 0) {
    col = base * (amb_k * (0.78 + 0.22*hemi) + sun_k * lam * sh * sun_col);
  } else {
    vec3 ground = vec3(0.32,0.29,0.24);
    vec3 fill = mix(ground, sky_col, hemi) * amb_k;
    col = base * (fill + sun_k * lam * sh * sun_col);
    for (int i=0;i<4;i++){ if (i >= n_lights) break;
      vec3 L = l_pos[i] - v_pos; float d2 = dot(L,L);
      col += base * l_col[i] * max(dot(n, normalize(L)), 0.0) / (1.0 + d2);
    }
    // a little sky in the glass and on the floor's sheen
    float fres = pow(1.0 - max(dot(n, V), 0.0), 4.0);
    col += fres * sky_col * 0.15 * (1.0 - v_emit);
  }
  col += base * v_emit * 2.2;
  if (fog_k > 0.0) {
    float d = length(eye - v_pos);
    col = mix(col, fog_col, 1.0 - exp(-fog_k * d));
  }
  if (tone == 1) col = aces(col * exposure);
  float g = dot(col, vec3(0.299,0.587,0.114));
  col = mix(vec3(g), col, sat);
  frag = vec4(col, v_col.a * alpha_k);
}
"""

_SHADOW_VS = """
#version 330
uniform mat4 light_mvp;
in vec3 in_pos;
void main(){ gl_Position = light_mvp * vec4(in_pos, 1.0); }
"""
_SHADOW_FS = """
#version 330
void main(){}
"""

_LINE_VS = """
#version 330
uniform mat4 mvp;
in vec3 in_pos; in vec4 in_col;
out vec4 g_col; out vec3 g_pos;
void main(){ g_col = in_col; g_pos = in_pos; gl_Position = mvp * vec4(in_pos, 1.0); }
"""
_LINE_GS = """
#version 330
layout(lines) in;
layout(triangle_strip, max_vertices=4) out;
uniform vec2 viewport; uniform float width_px;
in vec4 g_col[]; in vec3 g_pos[];
out vec4 f_col; out vec3 f_pos;
void main(){
  vec4 a = gl_in[0].gl_Position, b = gl_in[1].gl_Position;
  if (a.w < 0.001 || b.w < 0.001) return;
  vec2 sa = a.xy / a.w * viewport, sb = b.xy / b.w * viewport;
  vec2 d = sb - sa; float L = length(d);
  if (L < 1e-5) d = vec2(1,0); else d /= L;
  vec2 n = vec2(-d.y, d.x) * width_px;
  vec2 e = d * width_px * 0.5;
  vec2 o0 = (n - e) / viewport, o1 = (-n - e) / viewport, o2 = (n + e) / viewport, o3 = (-n + e) / viewport;
  float bias = 0.00025;
  f_col = g_col[0]; f_pos = g_pos[0];
  gl_Position = vec4(a.xy + o0 * a.w, a.z - bias * a.w, a.w); EmitVertex();
  gl_Position = vec4(a.xy + o1 * a.w, a.z - bias * a.w, a.w); EmitVertex();
  f_col = g_col[1]; f_pos = g_pos[1];
  gl_Position = vec4(b.xy + o2 * b.w, b.z - bias * b.w, b.w); EmitVertex();
  gl_Position = vec4(b.xy + o3 * b.w, b.z - bias * b.w, b.w); EmitVertex();
  EndPrimitive();
}
"""
_LINE_FS = """
#version 330
uniform vec4 clip_plane; uniform int use_clip;
in vec4 f_col; in vec3 f_pos;
out vec4 frag;
void main(){
  if (use_clip == 1 && dot(vec4(f_pos,1.0), clip_plane) > 0.0) discard;
  frag = f_col;
}
"""

_SKY_VS = """
#version 330
in vec2 in_xy; out vec2 uv;
void main(){ uv = in_xy * 0.5 + 0.5; gl_Position = vec4(in_xy, 0.9999, 1.0); }
"""
_SKY_FS = """
#version 330
uniform vec3 top; uniform vec3 mid; uniform vec3 low; uniform float horizon;
in vec2 uv; out vec4 frag;
void main(){
  float t = uv.y;
  vec3 c = t > horizon ? mix(mid, top, smoothstep(horizon, 1.0, t)) : mix(low, mid, smoothstep(0.0, horizon, t));
  frag = vec4(c, 1.0);
}
"""

_SKIES = {
    "paper": ((0.97, 0.97, 0.96), (0.99, 0.99, 0.98), (0.95, 0.95, 0.93)),
    "white": ((1, 1, 1), (1, 1, 1), (1, 1, 1)),
    "day": ((0.42, 0.62, 0.86), (0.78, 0.86, 0.93), (0.86, 0.88, 0.86)),
    "dusk": ((0.24, 0.30, 0.52), (0.98, 0.70, 0.48), (0.95, 0.80, 0.62)),
    "night": ((0.02, 0.03, 0.08), (0.08, 0.10, 0.22), (0.16, 0.14, 0.20)),
}


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------

@dataclass
class View:
    """What to show: the pieces, and how."""

    tags: tuple | None = None           # only these tags (None: everything)
    hide_tags: tuple = ()
    only: set | None = None             # only these piece ids
    hide: set = field(default_factory=set)
    highlight: dict = field(default_factory=dict)    # piece id -> hex colour
    ghost: set = field(default_factory=set)          # piece ids drawn faint
    explode: float = 0.0
    max_step: int | None = None
    clip: tuple | None = None           # (a, b, c, d): discard a x + b y + c z + d > 0
    door_open: float = 0.0              # degrees the leaf swings out


def _piece_colour(p: Piece, style: Style, view: View) -> tuple[tuple, float, float]:
    mat = MATERIALS.get(p.material, {"color": "#cccccc"})
    col = hex_rgb(view.highlight.get(p.id, mat["color"]))
    a = float(mat.get("opacity", 1.0))
    emit = float(mat.get("emissive", 0.0))
    if style.palette == "mono" and p.id not in view.highlight:
        g = 0.93 if p.tag != "site" else 0.98
        col = (g, g, g * 0.985)
        if p.material in ("glass", "poly"):
            col, a = (0.85, 0.9, 0.95), 0.35
        emit = 0.0
    if p.tag == "site" and style.ground:
        col = hex_rgb(style.ground)
    if style.sky == "night" and p.material == "glass":
        col, a, emit = (1.0, 0.78, 0.45), 0.55, 0.55
    if p.id in view.ghost:
        a *= 0.18
    if style.xray > 0 and p.tag not in ("site",):
        a *= style.xray
    if style.tone == "aces":
        col = tuple(c ** 2.2 for c in col)      # to linear for the lit pass
    return col, a, emit


def _leaf_transform(p: Piece, model: Model, deg: float):
    """Turn a door-leaf piece about the hinge (the leaf's -x edge), swinging outwards."""
    door = model.tables.get("door")
    if not door or not deg:
        return None
    hx = -door["W"] / 2
    hy = door["y_post"]
    a = math.radians(-deg)
    c, s = math.cos(a), math.sin(a)
    rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return rot, np.array([hx, hy, 0])


def _pieces(model: Model, view: View) -> list[tuple[Piece, np.ndarray]]:
    out = []
    for p in model.pieces:
        if view.tags is not None and p.tag not in view.tags:
            continue
        if p.tag in view.hide_tags or p.id in view.hide:
            continue
        if view.only is not None and p.id not in view.only:
            continue
        if view.max_step is not None and p.step > view.max_step:
            continue
        if not len(p.mesh.verts):
            continue
        v = p.mesh.verts
        if view.explode:
            v = v + np.asarray(p.explode, float) * view.explode
        if p.group == "door-leaf" and view.door_open:
            rot, piv = _leaf_transform(p, model, view.door_open)
            v = (v - piv) @ rot.T + piv
        out.append((p, v))
    return out


def render(model: Model, camera: Camera, style: Style = SKETCH, view: View | None = None, ss: int = 2,
           extra: list | None = None) -> Image.Image:
    """Draw the model. ``extra`` adds pieces that are not part of the model (a jig, a saw)."""
    import moderngl
    view = view or View()
    gl = ctx()
    W, H = camera.width * ss, camera.height * ss
    cam = replace(camera, width=W, height=H)
    items = _pieces(model, view)
    for p in extra or []:
        if view.only is None or p.id in view.only:
            items.append((p, p.mesh.verts))
    opaque, glass, lines = [], [], []
    for p, v in items:
        col, a, emit = _piece_colour(p, style, view)
        tri = v[p.mesh.tris]                         # (m, 3, 3)
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(nrm, axis=1, keepdims=True)
        nrm = np.where(ln > 1e-12, nrm / np.maximum(ln, 1e-12), 0)
        m = len(tri)
        block = np.zeros((m * 3, 11), dtype="f4")
        block[:, 0:3] = tri.reshape(-1, 3)
        block[:, 3:6] = np.repeat(nrm, 3, axis=0)
        block[:, 6:9] = col
        block[:, 9] = a
        block[:, 10] = emit
        if a < 0.99:
            d = float(np.linalg.norm(v.mean(axis=0) - np.asarray(cam.eye)))
            glass.append((d, block))
        else:
            opaque.append(block)
        if style.edges and len(p.mesh.edges) and p.tag != "site":
            ec = style.edge_color
            ea = 0.35 if a < 0.99 else 1.0
            if p.tag == "skin":
                ea *= style.skin_edges
            if p.id in view.ghost:
                ea *= 0.25
            seg = v[p.mesh.edges].reshape(-1, 3)
            lb = np.zeros((len(seg), 7), dtype="f4")
            lb[:, 0:3] = seg
            lb[:, 3:6] = ec
            lb[:, 6] = ea
            lines.append(lb)

    prog = gl.program(vertex_shader=_VS, fragment_shader=_FS)
    lprog = gl.program(vertex_shader=_LINE_VS, geometry_shader=_LINE_GS, fragment_shader=_LINE_FS)
    sprog = gl.program(vertex_shader=_SHADOW_VS, fragment_shader=_SHADOW_FS)
    kprog = gl.program(vertex_shader=_SKY_VS, fragment_shader=_SKY_FS)
    fbo = gl.framebuffer(color_attachments=[gl.texture((W, H), 4)], depth_attachment=gl.depth_renderbuffer((W, H)))

    # shadow map
    sun = np.asarray(style.sun_dir, float)
    sun /= np.linalg.norm(sun)
    all_pts = np.vstack([v for _, v in items]) if items else np.zeros((1, 3))
    lo, hi = all_pts.min(axis=0), all_pts.max(axis=0)
    # the shadow box covers what casts and receives near the dome, not the whole ground disc
    focus = np.vstack([v for p, v in items if p.tag != "site"]) if any(p.tag != "site" for p, _ in items) else all_pts
    flo, fhi = focus.min(axis=0), focus.max(axis=0)
    c = (flo + fhi) / 2
    rad = float(np.linalg.norm(fhi - flo)) / 2 * 1.35 + 0.5
    lview = _look(c + sun * rad * 3, c, np.array([0, 0, 1.0]) if abs(sun[2]) < 0.98 else np.array([0, 1.0, 0]))
    lproj = np.eye(4)
    lproj[0, 0] = lproj[1, 1] = 1 / rad
    lproj[2, 2], lproj[2, 3] = -2 / (rad * 6), -(rad * 6 + 0.01) / (rad * 6) * 1.0
    lproj[2, 3] = -1.0 - 0.0
    # map depth range [rad*3 - rad*2, rad*3 + rad*2] to [-1, 1]
    nn, ff = rad * 1.0, rad * 5.0
    lproj[2, 2], lproj[2, 3] = -2 / (ff - nn), -(ff + nn) / (ff - nn)
    light_mvp = (lproj @ lview).astype("f4")
    SM = 4096
    depth = gl.depth_texture((SM, SM))
    depth.compare_func = "<="
    depth.repeat_x = depth.repeat_y = False
    depth.filter = (moderngl.LINEAR, moderngl.LINEAR)
    sfbo = gl.framebuffer(depth_attachment=depth)
    buffers = []
    if opaque and style.shadows:
        allop = np.vstack(opaque)
        sb = gl.buffer(np.ascontiguousarray(allop[:, 0:3]).tobytes())
        buffers.append(sb)
        svao = gl.vertex_array(sprog, [(sb, "3f", "in_pos")])
        sfbo.use()
        sfbo.clear(depth=1.0)
        gl.enable(moderngl.DEPTH_TEST)
        gl.disable(moderngl.CULL_FACE)
        sprog["light_mvp"].write(light_mvp.T.tobytes())
        svao.render(moderngl.TRIANGLES)
        svao.release()

    fbo.use()
    gl.viewport = (0, 0, W, H)
    fbo.clear(0, 0, 0, 1, depth=1.0)
    # sky
    top, mid, low = _SKIES.get(style.sky, _SKIES["paper"])
    if style.tone == "aces":
        top, mid, low = (tuple(x ** 2.2 for x in t) for t in (top, mid, low))
        top, mid, low = (tuple(min(1, x ** (1 / 2.2)) for x in t) for t in (top, mid, low))
    quad = gl.buffer(np.array([-1, -1, 3, -1, -1, 3], dtype="f4").tobytes())
    kvao = gl.vertex_array(kprog, [(quad, "2f", "in_xy")])
    kprog["top"].value, kprog["mid"].value, kprog["low"].value = top, mid, low
    kprog["horizon"].value = 0.42
    gl.disable(moderngl.DEPTH_TEST)
    kvao.render(moderngl.TRIANGLES)
    gl.enable(moderngl.DEPTH_TEST)

    mvp = cam.mvp().astype("f4")
    prog["mvp"].write(mvp.T.tobytes())
    prog["light_mvp"].write(light_mvp.T.tobytes())
    prog["sun_dir"].value = tuple(sun)
    prog["sun_col"].value = style.sun_color
    prog["sun_k"].value = style.sun
    prog["amb_k"].value = style.ambient
    prog["sky_col"].value = style.sky_color
    prog["eye"].value = tuple(float(x) for x in cam.eye)
    prog["fog_k"].value = style.fog
    fogc = mid if style.tone != "aces" else tuple(x ** 2.2 for x in mid)
    prog["fog_col"].value = tuple(float(x) for x in fogc)
    prog["use_shadow"].value = 1 if style.shadows else 0
    prog["shadow_texel"].value = 1.0 / SM
    prog["tone"].value = 1 if style.tone == "aces" else 0
    prog["exposure"].value = style.exposure
    prog["sat"].value = style.saturation
    use_clip = 1 if view.clip else 0
    for pr in (prog, lprog):
        pr["use_clip"].value = use_clip
        pr["clip_plane"].value = tuple(float(x) for x in (view.clip or (0, 0, 0, 0)))
    lights = list(style.lights)[:4]
    prog["n_lights"].value = len(lights)
    if lights:
        pos = [tuple(l[0]) for l in lights] + [(0, 0, 0)] * (4 - len(lights))
        colr = [tuple(np.asarray(l[1]) * l[2]) for l in lights] + [(0, 0, 0)] * (4 - len(lights))
        prog["l_pos"].write(np.array(pos, dtype="f4").tobytes())
        prog["l_col"].write(np.array(colr, dtype="f4").tobytes())
    depth.use(location=0)
    prog["shadow"].value = 0
    prog["alpha_k"].value = 1.0

    def draw(block, blend=False):
        b = gl.buffer(np.ascontiguousarray(block).tobytes())
        vao = gl.vertex_array(prog, [(b, "3f 3f 4f 1f", "in_pos", "in_nrm", "in_col", "in_emit")])
        vao.render(moderngl.TRIANGLES)
        vao.release()
        b.release()

    gl.polygon_offset = (1.0, 1.0)
    if opaque:
        draw(np.vstack(opaque))
    if lines:
        lb = np.vstack(lines)
        lbuf = gl.buffer(np.ascontiguousarray(lb).tobytes())
        lvao = gl.vertex_array(lprog, [(lbuf, "3f 4f", "in_pos", "in_col")])
        lprog["mvp"].write(mvp.T.tobytes())
        lprog["viewport"].value = (W / 2, H / 2)
        lprog["width_px"].value = style.edge_px * ss / 2
        gl.enable(moderngl.BLEND)
        gl.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        lvao.render(moderngl.LINES)
    if glass:
        gl.enable(moderngl.BLEND)
        gl.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        gl.depth_mask = False
        for _, block in sorted(glass, key=lambda g: -g[0]):
            draw(block)
        gl.depth_mask = True
    gl.disable(moderngl.BLEND)
    gl.polygon_offset = (0.0, 0.0)
    raw = fbo.color_attachments[0].read()
    img = Image.frombytes("RGBA", (W, H), raw).transpose(Image.FLIP_TOP_BOTTOM).convert("RGB")
    for o in (fbo, sfbo, depth, quad, kvao, prog, lprog, sprog, kprog, *buffers):
        o.release()
    if lines:
        lvao.release()
        lbuf.release()
    if ss > 1:
        img = img.resize((camera.width, camera.height), Image.LANCZOS)
    if style.bloom > 0:
        img = _bloom(img, style.bloom)
    return img


def _bloom(img: Image.Image, k: float) -> Image.Image:
    a = np.asarray(img, dtype=np.float32) / 255.0
    lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    bright = np.clip((lum - 0.72) / 0.28, 0, 1)[..., None] * a
    b = Image.fromarray((bright * 255).astype(np.uint8))
    r = max(4, img.width // 120)
    glow = np.asarray(b.filter(ImageFilter.GaussianBlur(r)), dtype=np.float32) / 255.0
    glow2 = np.asarray(b.filter(ImageFilter.GaussianBlur(r * 4)), dtype=np.float32) / 255.0
    out = np.clip(a + k * (glow + glow2), 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8))
