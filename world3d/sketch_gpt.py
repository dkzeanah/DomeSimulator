"""sketch-gpt: architectural drawing studio for the repository's editable world.

Run through the launcher's sketch-gpt tab, or ``py -3.12 -m world3d.sketch_gpt``.
The solver, solids, editing operations, jig stages and fabrication exports are shared
with world3d and Dome Creator. No second dome generator lives here.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import document as dm, pieces as pc, structures as st

ROOT = Path(__file__).resolve().parents[1]
SAVE = ROOT / "world3d" / "saved" / "sketch-gpt.json"
PALETTES = {
    "Cedar / sage": ((169, 111, 65), (219, 221, 201), (62, 100, 105)),
    "Charcoal / oak": ((160, 122, 80), (69, 81, 80), (75, 110, 123)),
    "Linen / honey": ((189, 140, 80), (234, 224, 198), (90, 125, 130)),
}
ASSUMPTIONS = [
    ("Units", "All model and CSV lengths are inches; drawings are fit-to-page, not cutting templates."),
    ("Furniture", "Illustrative props in inches: bed 60 x 80; table 42 x 26 x 28; counter 60 x 24 x 36."),
    ("Skin", "Existing solver offset and 0.25-inch display thickness; no envelope specification implied."),
    ("Finish", "Palette and glazed triangles are presentation choices, not specified materials."),
    ("Construction", "Geometry study. Fasteners, bracing, anchors, loads and services require design."),
    ("Access", "No door is cut into structural members. Door, egress and room clearances remain unresolved."),
]
BUILD_STEPS = [
    ("Set out the platform", "foundation_jig", "Locate the solver's pentagon corners and star intersections. Check side lengths and diagonals against the foundation schedule. Confirm site survey and bearing design before excavation.", "Gate: site, footing and anchorage design approved."),
    ("Build the foundation", "foundation", "Identify each F piece in the schedule. Trial-fit the perimeter and star on the layout; check crown coordinates, level and support locations before installing the deck.", "Gate: support spans, joints and ground bearing checked."),
    ("Lay the deck", "foundation_deck", "Use the pentagonal crown as the deck boundary. The displayed slab is a visualization of the floor extent. Select decking, support spacing, fixings and moisture separation for the actual project.", "Gate: floor assembly and attachment details resolved."),
    ("Prepare panel stock", "dome_jig", "Use the BOM and jig-cut-sequence CSV. Separate nominal edge, finished stock, sacrificial tail and head overfit. Keep member IDs with the pieces; do not substitute nominal edge length for a physical cut.", "Gate: inspect grain, defects, moisture and a trial joint."),
    ("Assemble the lower course", "lower", "Follow the panel identity map. The highlight groups panels by centroid elevation for illustration; it is not a temporary works design. Use the approved erection sequence and bracing before raising any panel.", "Gate: lifting method and temporary restraint designed."),
    ("Close the frame", "frame", "Match panel and member IDs with the seam-join schedule. Work from the supported lower panels toward the crown. Verify fit at each seam before closing the final panels.", "Gate: connections, tolerances and permanent stability checked."),
    ("Develop the enclosure", "shell", "Use each panel's nominal triangle and solver skin offset as design references. Resolve insulation, air and water layers, drainage, seams, openings and condensation before fabricating an enclosure.", "Gate: envelope details and opening reinforcement resolved."),
    ("Fit out the living space", "living", "The cutaway shows a furniture concept on the existing deck. Coordinate access, egress, ventilation, utilities, fire separation and furniture clearances with the final floor plan.", "Gate: habitable-use and local approval requirements satisfied."),
]


def simulator():
    from .app import _dome
    return _dome()


def new_document(load=True):
    doc = dm.Document()
    if load:
        doc.load(SAVE)
    return doc


def facts():
    m = st.dome_model()
    v = m.topology.vertices
    crown = np.asarray(st.foundation_model().crown)
    area = abs(np.dot(crown[:, 0], np.roll(crown[:, 1], -1)) -
               np.dot(crown[:, 1], np.roll(crown[:, 0], -1))) / 2 / 144
    return {"panels": len(m.topology.faces), "members": len(m.members),
            "nominal_long_edge_in": m.config.long_edge_in,
            "dome_width_in": float(np.ptp(v[:, 0])),
            "dome_height_in": float(np.ptp(v[:, 2])),
            "deck_area_sqft": float(area), "deck_top_in": st.foundation_top()}


def furniture():
    """Presentation props; sizes declared in ASSUMPTIONS before drawings use them."""
    z = st.foundation_top() + 1.5
    out = []
    def box(pid, name, lo, hi, color):
        out.append(pc.Piece(pid, "furniture", name, st._box(np.array(lo) + [0, 0, z],
                        np.array(hi) + [0, 0, z]), color, "prop"))
    box("BED", "Bed concept 60 x 80 in", (-85, -18, 0), (-25, 62, 16), (.84, .82, .72, 1))
    box("BED-T", "Linen throw", (-85, 6, 16), (-25, 58, 18), (.39, .49, .39, 1))
    box("PILLOW-1", "Linen pillow", (-82, -15, 18), (-58, 0, 23), (.94, .91, .80, 1))
    box("PILLOW-2", "Linen pillow", (-54, -15, 18), (-30, 0, 23), (.94, .91, .80, 1))
    box("TABLE", "Table concept 42 x 26 in", (3, -55, 26), (45, -29, 28), (.67, .43, .25, 1))
    for k,(x,y) in enumerate(((5,-53),(41,-53),(5,-33),(41,-33))):
        box(f"TABLE-LEG-{k}", "Table leg", (x,y,0), (x+2,y+2,26), (.23,.29,.27,1))
    box("COUNTER", "Counter concept 60 x 24 in", (20, 35, 0), (80, 59, 36), (.30, .39, .36, 1))
    box("WORKTOP", "Counter worktop", (19,34,36), (81,60,37), (.82,.81,.74,1))
    box("RUG", "Woven rug", (-12, -70, .1), (70, -2, .4), (.77, .64, .44, 1))
    return out


def scene(doc, stage="living"):
    keys = {"foundation_jig": ["foundation_jig"], "foundation": ["foundation"],
            "foundation_deck": ["foundation", "foundation_deck"],
            "dome_jig": ["dome_jig"], "lower": ["foundation", "foundation_deck", "dome"],
            "frame": ["foundation", "foundation_deck", "dome", "mine"],
            "shell": ["foundation", "foundation_deck", "dome", "dome_skin", "mine"],
            "living": ["foundation", "foundation_deck", "dome", "dome_skin", "mine"]}[stage]
    out = [p for k in keys for p in doc.layers.get(k, [])]
    if stage == "lower":
        centers = {m.face_index: float(np.mean(st.dome_model().topology.vertices[list(f.vertices)], axis=0)[2])
                   for m, f in zip(st.dome_model().members[::3], st.dome_model().topology.faces)}
        threshold = np.median(list(centers.values()))
        keep = {f"D{i + 1:03d}" for i, m in enumerate(st.dome_model().members) if centers[m.face_index] <= threshold}
        out = [p for p in out if p.layer != "dome" or p.pid in keep]
    if stage == "living":
        # A diagrammatic cutaway removes front skin only; frame stays complete.
        out = [p for p in out if p.layer != "dome_skin" or p.points().mean(axis=0)[1] > 0]
        out += furniture()
    return out


def jig_scene(index, panel=0):
    d = simulator()
    out = []
    for key, mesh in d.build_fabrication_jig(st.dome_model(), panel, index).items():
        if isinstance(mesh,d.LineData):
            for k,pair in enumerate(np.asarray(mesh.vertices).reshape(-1,2,7)):
                a,b=pair[:,:3]
                if np.linalg.norm(a-b)>1e-6:
                    out.append(pc.Piece(f"{key}-line-{k}","jig",key,
                        pc.strut(a,b,"square",.18),tuple(pair[0,3:7]),"jig"))
        if isinstance(mesh, d.MeshData) and len(mesh.indices):
            # Preserve per-triangle solver colors (fences and cut planes matter).
            vv = np.asarray(mesh.vertices).reshape(-1, 10)
            for k, tri in enumerate(np.asarray(mesh.indices).reshape(-1, 3)):
                xyz = vv[tri, :3]
                out.append(pc.Piece(f"{key}-{k}", "jig", key,
                    pc.from_rings(xyz, xyz + [0, 0, .001]), tuple(vv[tri[0], 6:10]), "jig"))
    return out


def camera(yaw=-65, elevation=25):
    a, b = math.radians(yaw), math.radians(elevation)
    right = np.array([-math.sin(a), math.cos(a), 0])
    toward = np.array([math.cos(b)*math.cos(a), math.cos(b)*math.sin(a), math.sin(b)])
    up = np.cross(toward, right)
    return np.array([right, up, toward])


def polygons(pieces, size, yaw=-65, elevation=25, palette="Cedar / sage", selected=None):
    basis = camera(yaw, elevation)
    allpts = np.concatenate([p.points() for p in pieces]) @ basis.T
    lo, hi = allpts.min(axis=0), allpts.max(axis=0)
    w, h = size
    scale = min(w * .84 / max(1, hi[0]-lo[0]), h * .78 / max(1, hi[1]-lo[1]))
    center = (lo+hi)/2
    wood, skin, glass = PALETTES[palette]
    result = []
    for p in pieces:
        for poly, _ in p.solid.faces:
            normal = np.cross(poly[1]-poly[0], poly[2]-poly[0])
            n = np.linalg.norm(normal)
            if n < 1e-9:
                continue
            normal /= n
            if normal @ basis[2] < -.01:
                continue
            q = (poly @ basis.T - center) * scale
            xy = [(w/2+x, h*.52-y) for x,y,_ in q]
            col = np.array(p.colour[:3])*255
            if p.layer in ("dome", "mine"):
                col = np.array(wood)
            if p.layer == "dome_skin":
                col = np.array(glass if int(p.pid[2:]) % 4 == 0 else skin)
            light = .68 + .32 * max(0, normal @ np.array([-.4, -.5, .76]))
            color = tuple(int(np.clip(c*light, 0, 255)) for c in col)
            result.append((float(q[:,2].mean()), xy, color, p.pid, p.layer))
    return sorted(result, key=lambda row: row[0])


def font(size, bold=False):
    path = Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default(size=size)


def render(pieces, size=(1600, 1000), yaw=-65, elevation=25, palette="Cedar / sage",
           selected=None, title="A place to live", blueprint=False):
    img = Image.new("RGB", size, "#f1eee5" if not blueprint else "#edf2f1")
    draw = ImageDraw.Draw(img)
    w, h = size
    for y in range(0, h, max(16, w//45)):
        draw.line((0,y,w,y), fill="#e7e7dd", width=1)
    for x in range(0, w, max(16, w//45)):
        draw.line((x,0,x,h), fill="#e7e7dd", width=1)
    # A depth buffer is essential here: face-centroid painter ordering makes long
    # foundation members appear through the deck. Picking uses rays against the
    # same solids; displayed and exported geometry uses actual per-pixel depth.
    import moderngl
    basis=camera(yaw,elevation)
    bounds=np.concatenate([p.points() for p in pieces])@basis.T
    lo,hi=bounds.min(axis=0),bounds.max(axis=0); center=(lo+hi)/2
    scale=min(w*.84/max(1,hi[0]-lo[0]),h*.78/max(1,hi[1]-lo[1]))
    triangles=[]; edges=[]
    wood,skin,glass=PALETTES[palette]
    def project(q):
        q=(q@basis.T-center)*scale
        q[...,0]*=2/w; q[...,1]=q[...,1]*2/h-.04
        q[...,2]*=-1/max(1,(hi[2]-lo[2])*scale)
        return q
    for p in pieces:
        tri=pc.triangles(p)
        normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        lengths=np.linalg.norm(normal,axis=1)
        valid=lengths>1e-9; tri=tri[valid]; normal=normal[valid]/lengths[valid,None]
        if not len(tri): continue
        col=np.array(p.colour[:3])*255
        if p.layer in ("dome","mine"): col=np.array(wood)
        if p.layer=="dome_skin": col=np.array(glass if int(p.pid[2:])%4==0 else skin)
        if blueprint: col=np.array([222,232,230])
        if p.pid==selected: col=np.array([238,176,70])
        light=.72+.28*np.abs(normal@np.array([-.4,-.5,.76]))
        colors=np.ones((len(tri),3,4)); colors[:,:,:3]=light[:,None,None]*col[None,None,:]/255
        triangles.append(np.concatenate([project(tri),colors],axis=2).reshape(-1,7))
        if blueprint or p.layer in ("dome_skin","furniture","jig"):
            for poly,_ in p.solid.faces:
                q=project(poly)
                for k in range(len(poly)):
                    for j in (k,(k+1)%len(poly)):
                        v=q[j].copy(); v[2]-=.00002
                        edges.append(np.r_[v,[.20,.34,.32] if blueprint else col*.62/255,1])
    ctx=moderngl.create_standalone_context()
    samples=min(4,ctx.max_samples)
    target=ctx.simple_framebuffer((w,h),components=4)
    fbo=ctx.simple_framebuffer((w,h),components=4,samples=samples)
    fbo.use(); fbo.clear(0,0,0,0,depth=1)
    program=ctx.program(vertex_shader='''#version 330
        in vec3 position; in vec4 color; out vec4 rgba;
        void main(){gl_Position=vec4(position,1);rgba=color;}''',fragment_shader='''#version 330
        in vec4 rgba; out vec4 frag; void main(){frag=rgba;}''')
    ctx.enable(moderngl.DEPTH_TEST)
    buffers=[]; arrays=[]
    for data,mode in ((triangles,moderngl.TRIANGLES),(edges,moderngl.LINES)):
        if not data: continue
        array=np.concatenate(data,axis=0) if mode==moderngl.TRIANGLES else np.asarray(data)
        buffer=ctx.buffer(np.asarray(array,dtype='f4').tobytes()); buffers.append(buffer)
        vao=ctx.vertex_array(program,[(buffer,'3f 4f','position','color')]); arrays.append(vao); vao.render(mode)
    ctx.copy_framebuffer(target,fbo)
    model=Image.frombytes('RGBA',(w,h),target.read(components=4)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    img.paste(model,(0,0),model)
    for vao in arrays: vao.release()
    for buffer in buffers: buffer.release()
    program.release(); fbo.release(); target.release(); ctx.release()
    draw.rectangle((0,0,w,h*.105), fill="#203e3c")
    draw.text((w*.035,h*.023), "sketch-gpt  /  " + title, font=font(max(16,w//43),True), fill="#f4edda")
    draw.rectangle((0,h*.94,w,h), fill="#203e3c")
    draw.text((w*.035,h*.955), "DomeSim  |  solver geometry  |  design study  |  fit-to-page",
              font=font(max(12,w//90)), fill="#e6e2d2")
    return img


def panel_drawing(index, size=(1400,900)):
    """Dimensioned reference triangle with real receiving and butt contact outlines."""
    d, m = simulator(), st.dome_model()
    face = m.topology.faces[index]
    frame = d._panel_frame(m, index)
    xy = np.array([d._panel_xy(m.topology.vertices[k], frame) for k in face.vertices])
    lo, hi = xy.min(axis=0), xy.max(axis=0)
    w,h = size
    scale = min(w*.68/max(1,hi[0]-lo[0]),h*.60/max(1,hi[1]-lo[1]))
    def point(q):
        p = (np.asarray(q)-(hi+lo)/2)*scale
        return (w/2+p[0],h*.49-p[1])
    im = Image.new("RGB",size,"#f6f4ec")
    dr = ImageDraw.Draw(im)
    pts = [point(q) for q in xy]
    dr.polygon(pts,fill="#e1e9e2",outline="#254844",width=3)
    for k,p in enumerate(pts):
        dr.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill="#a86737")
        dr.text((p[0]+10,p[1]),f"N{face.vertices[k]}",font=font(20,True),fill="#254844")
        q=pts[(k+1)%3]
        length=np.linalg.norm(m.topology.vertices[face.vertices[k]]-m.topology.vertices[face.vertices[(k+1)%3]])
        mid=(np.array(p)+q)/2
        direction=mid-np.array([w/2,h*.49]); direction/=max(1,np.linalg.norm(direction))
        label=f'{length:.3f} in'
        anchor=mid+direction*35
        dr.text(tuple(anchor),label,font=font(22,True),fill="#254844",anchor="mm",stroke_width=3,stroke_fill="#f6f4ec")
    members=[x for x in m.members if x.face_index==index]
    for member in members:
        for cut,col in ((member.receiving_cut_points,"#b3448d"),(member.butt_contact_points,"#248b9e")):
            pp=[point(d._panel_xy(p,frame)) for p in cut]
            dr.line(pp+[pp[0]],fill=col,width=4)
    dr.text((45,30),f"P{index+1:03d} / {face.face_type} / EXTERIOR",font=font(32,True),fill="#254844")
    dr.text((45,h-120),"Magenta: receiving / head trim    Cyan: butt contact",font=font(22),fill="#254844")
    dr.text((45,h-80),"Dimensions are nominal reference edges. Use physical stock and cut-plane schedules.",font=font(20),fill="#52625c")
    dr.text((45,h-48),"Fit-to-page drawing. Do not measure the printed page for fabrication.",font=font(20),fill="#52625c")
    return im


def identity_drawing(size=(1600,1000)):
    m=st.dome_model(); w,h=size
    vertices=m.topology.vertices[:,:2]
    lo,hi=vertices.min(axis=0),vertices.max(axis=0)
    scale=min(w*.78/(hi[0]-lo[0]),h*.72/(hi[1]-lo[1]))
    xy=(vertices-(lo+hi)/2)*scale
    xy=np.column_stack([w/2+xy[:,0],h*.5-xy[:,1]])
    im=Image.new("RGB",size,"#f6f4ec"); dr=ImageDraw.Draw(im)
    for face in m.topology.faces:
        pp=xy[list(face.vertices)]
        dr.polygon([tuple(q) for q in pp],fill="#e1e9e2" if face.face_type=="BAB" else "#efe2cb",outline="#34594f",width=2)
        center=pp.mean(axis=0)
        dr.text(tuple(center),f"P{face.index+1:03d}",font=font(20,True),fill="#254844",anchor="mm")
    dr.text((45,25),"PANEL IDENTITY MAP / PLAN / +Y UP",font=font(32,True),fill="#254844")
    dr.text((45,h-90),"Each label identifies one complete three-member panel. Exterior handedness is defined on its own sheet.",font=font(22),fill="#254844")
    dr.text((45,h-52),"Member IDs and world-piece IDs: identity-map.csv. Map describes the baseline solver topology.",font=font(22),fill="#52625c")
    return im


def pick_scene(pieces,size,x,y,yaw,elevation):
    basis=camera(yaw,elevation)
    points=np.concatenate([p.points() for p in pieces])@basis.T
    lo,hi=points.min(axis=0),points.max(axis=0); center=(lo+hi)/2
    w,h=size; scale=min(w*.84/max(1,hi[0]-lo[0]),h*.78/max(1,hi[1]-lo[1]))
    projected=np.array([(x-w/2)/scale,(h*.52-y)/scale,hi[2]-center[2]+100])
    origin=(projected+center)@basis; direction=-basis[2]
    best=None; distance=float("inf")
    for p in pieces:
        t=pc.ray_hit(pc.triangles(p),origin,direction)
        if t is not None and t<distance: best,distance=p,t
    return best


def export_obj(pieces, path):
    with path.open("x",encoding="utf-8") as f:
        f.write("# sketch-gpt / DomeSim / inches / z up\n")
        offset=1
        for p in pieces:
            f.write(f"o {p.pid}\n")
            for poly,_ in p.solid.faces:
                for x,y,z in poly:
                    f.write(f"v {x:.8f} {y:.8f} {z:.8f}\n")
                f.write("f "+" ".join(str(offset+k) for k in range(len(poly)))+"\n")
                offset+=len(poly)


def build_guide(folder, doc, images):
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import simpleSplit
    path=folder/"sketch-gpt-guide.pdf"
    c=canvas.Canvas(str(path),pagesize=(842,595))
    c.setTitle("sketch-gpt | Dome design and construction geometry guide")
    page=0
    def start(title, subtitle=""):
        nonlocal page
        page+=1
        c.setFillColor(HexColor("#f6f4ec")); c.rect(0,0,842,595,fill=1,stroke=0)
        c.setFillColor(HexColor("#203e3c")); c.rect(0,532,842,63,fill=1,stroke=0)
        c.setFillColor(HexColor("#f6f4ec")); c.setFont("Helvetica-Bold",20); c.drawString(32,559,title)
        c.setFont("Helvetica",9); c.drawString(32,542,subtitle)
        c.setFillColor(HexColor("#52625c")); c.setFont("Helvetica",8)
        c.drawString(32,18,"sketch-gpt / DomeSim / geometry study / fit-to-page / inches")
        c.drawRightString(810,18,str(page))
    def text(s,x,y,width=760,size=11):
        c.setFillColor(HexColor("#29443f")); c.setFont("Helvetica",size)
        for line in simpleSplit(s,"Helvetica",size,width):
            c.drawString(x,y,line); y-=size*1.45
        return y-10
    def picture(im,x=32,y=141,w=778,h=376):
        c.drawImage(ImageReader(im),x,y,w,h,preserveAspectRatio=True,anchor="c",mask="auto")
    start("sketch-gpt / The livable dome", "Architectural illustration, fabrication references and guided assembly drawings")
    picture(images["hero"],32,106,778,420)
    text("One model, from solved pieces to presentation. Read the design basis and open decisions before using the schedules.",32,86)
    c.showPage()
    start("Design basis / read first", "Derived geometry and declared visualization assumptions")
    y=509
    for key,value in facts().items():
        y=text(f"{key.replace('_',' ')}: {value:.3f}" if isinstance(value,float) else f"{key}: {value}",32,y,size=10)
    for key,value in ASSUMPTIONS:
        y=text(f"{key}: {value}",32,y,size=10)
    text("Source: world3d.structures, infill.base, geodesic_raw_wedge_dome_dihedral. Physical lengths and cut planes come directly from their exports. No approval or load capacity is established by this guide.",32,y,size=10)
    c.showPage()
    start("Sheet index / use the package", "The illustrated guide and machine-readable source schedules travel together")
    y=500
    for s in ["Presentation: landscape and portrait hero images, cutaway living view, plan and elevation.",
              "Assembly: eight staged sheets from set-out to fit-out; each ends with a design or inspection gate.",
              "Panel fabrication: all twelve solver jig stages, followed by a dimensioned sheet for every panel.",
              "Schedules: BOM, both end cuts, seam joins, jig cut sequence and butt-cut setups in CSV.",
              "Panel references: one original solver SVG per panel. SVGs are scalable references, not certified full-size templates.",
              "Editable model: world.json carries the operation log; OBJ contains the edited frame, deck and presentation props in inches.",
              "Identity: D001 etc. are world piece IDs; WOOD_P001_E0 etc. are solver member IDs. identity-map.csv joins the two.",
              "Edits: presentation views and model exports reflect edits. Solver panel sheets describe the baseline. Edited pieces are flagged in model-status.json; reconcile them before fabrication."]:
        y=text(s,32,y,size=12)
    c.showPage()
    for title,key in [("Living study / cutaway","living"),("Plan / deck and furniture","plan"),("Elevation / frame","elevation")]:
        start(title,"Illustrative layout; no structural members removed for an opening")
        picture(images[key],32,60,778,460); c.showPage()
    start("Panel identity map", "Baseline topology / use with the per-panel sheets and identity-map.csv")
    picture(images["identity"],32,60,778,460); c.showPage()
    for i,(title,stage,instruction,gate) in enumerate(BUILD_STEPS):
        start(f"Build {i+1:02d} / {title}",gate)
        picture(images[f"step-{i}"],32,163,778,362)
        text(instruction,32,136,size=12); c.showPage()
    d=simulator()
    for i,(_slug,title,description,enforces) in enumerate(d.JIG_STAGES):
        start("Panel jig / "+title, "Solver fixture geometry / representative panel P001")
        picture(images[f"jig-{i}"],32,193,778,328)
        y=text(description,32,165,size=11)
        text("Enforces: "+enforces,32,y,size=10); c.showPage()
    m=st.dome_model()
    for face in m.topology.faces:
        i=face.index
        start(f"Panel P{i+1:03d} / fabrication reference",m.config.wedge_orientation+" / clockwise exterior pinwheel")
        picture(panel_drawing(i),32,172,778,353)
        c.setFont("Helvetica-Bold",10); c.setFillColor(HexColor("#29443f"))
        c.drawString(32,155,"Member / class        Nominal edge       Finished stock       Receives             Butts into")
        y=133
        for member in [x for x in m.members if x.face_index==i]:
            c.setFont("Courier",9)
            c.drawString(32,y,f"{member.member_id} / {member.edge_type}  {member.nominal_length_in:9.3f} in  {member.physical_stock_length_in:9.3f} in  {member.receives_member_id}  {member.butt_into_member_id}")
            y-=19
        text("Both end-plane normals, local cut descriptors, blank allowances and cut order: cut-schedule.csv and jig-cut-sequence.csv. Saw descriptors must be interpreted with the solver's face and fence references.",32,65,size=9)
        c.showPage()
    start("Before construction / close the design", "This package establishes geometry, not a complete habitable building specification")
    y=499
    for s in ["Structure: site loads, timber species and grade, defects, joint resistance, seam fasteners, anchorage, uplift and temporary bracing.",
              "Envelope: roof covering, flashings, drained seams, insulation, air barrier, vapor control, condensation and glazing support.",
              "Occupancy: engineered doorway, compliant egress, fire safety, ventilation, water, sanitation and electrical design.",
              "Fabrication: verify units, solver orientation, member identity and a test panel. Check stock allowances and machine references. Printed drawings are not scale templates.",
              "Edited designs: the baseline cut package must be regenerated or reconciled with the operation log by a designer. Moving or cutting a member invalidates its original fit assumptions.",
              "Reference matching: no external plan PDFs were supplied when this edition was generated. Sheet style and content can be matched once the reference documents are available."]:
        y=text(s,32,y,size=13)
    c.showPage(); c.save()
    return path


def export_package(doc=None,palette="Cedar / sage",progress=print):
    import medialib
    doc=doc or new_document()
    folder=medialib.new_folder("sketch-gpt")
    incomplete=folder/"INCOMPLETE.txt"
    incomplete.write_text("Export in progress. A release is complete only when manifest.json exists.\n",encoding="utf-8")
    progress(f"New release: {folder}")
    images={}
    images["identity"]=identity_drawing()
    images["identity"].save(folder/"panel-identity-map.png")
    for key,stage,yaw,elev in [("hero","shell",-65,22),("living","living",-90,40),
                              ("plan","living",-90,90),("elevation","frame",-90,0)]:
        pieces=scene(doc,stage)
        if key=="plan": pieces=[p for p in pieces if p.layer not in ("dome_skin","dome")]
        images[key]=render(pieces,(2400,1500),yaw,elev,palette,title=key.title())
        images[key].save(folder/f"{key}-landscape.png")
    render(scene(doc,"shell"),(1200,1800),-65,22,palette,title="A place to live").save(folder/"hero-portrait.png")
    progress("Drawing assembly sequence and solver jig stages...")
    for i,(title,stage,*_) in enumerate(BUILD_STEPS):
        images[f"step-{i}"]=render(scene(doc,stage),(1600,1000),-65,30,palette,title=title,blueprint=True)
    for i,(_,title,*_) in enumerate(simulator().JIG_STAGES):
        images[f"jig-{i}"]=render(jig_scene(i),(1600,1000),-65,50,palette,title=title)
    schedules=folder/"schedules"; schedules.mkdir()
    d,m=simulator(),st.dome_model()
    for name,fn in [("bom",d.export_bom),("cut-schedule",d.export_cut_schedule),
                    ("seam-joins",d.export_seam_join_schedule),("jig-cut-sequence",d.export_jig_cut_sequence),
                    ("butt-cut-setups",d.export_butt_cut_setups)]:
        fn(m,schedules/f"{name}.csv")
    panels=folder/"panel-references"; panels.mkdir()
    for face in m.topology.faces:
        d.export_panel_jig_svg(m,face.index,panels/f"P{face.index+1:03d}.svg")
    with (folder/"identity-map.csv").open("x",newline="",encoding="utf-8") as f:
        writer=csv.writer(f); writer.writerow(["world_piece","solver_member","panel","present_in_edited_model"])
        for i,member in enumerate(m.members):
            writer.writerow([f"D{i+1:03d}",member.member_id,f"P{member.face_index+1:03d}",doc.find(f"D{i+1:03d}") is not None])
    doc.save(folder/"world.json")
    export_obj(scene(doc,"living"),folder/"living-study.obj")
    export_obj(scene(doc,"frame"),folder/"edited-frame.obj")
    (folder/"model-status.json").write_text(json.dumps({"name":"sketch-gpt","facts":facts(),
        "assumptions":ASSUMPTIONS,"baseline_fabrication":True,"edited":bool(doc.ops),
        "operation_count":len(doc.ops),"operations":doc.ops,
        "note":"Solver schedules describe the baseline; edited geometry requires fabrication reconciliation."},indent=2),encoding="utf-8")
    progress("Composing the PDF and release assets...")
    pdf=build_guide(folder,doc,images)
    release=folder/"release"; release.mkdir()
    specification=(ROOT/"docs/sketch-gpt-standalone-spec.md").read_text(encoding="utf-8")
    for language in ("rust","cpp"):
        prompt=(ROOT/f"docs/sketch-gpt-{language}-prompt.md").read_text(encoding="utf-8")
        (folder/f"sketch-gpt-{language}-build-prompt.md").write_text(prompt+"\n\n---\n\n"+specification,encoding="utf-8")
    thumbs=release/"thumbnails"; thumbs.mkdir()
    for key,im in images.items():
        im.resize((640,400),Image.Resampling.LANCZOS).save(thumbs/f"{key}.jpg",quality=90)
    (release/"description.md").write_text("# sketch-gpt / A place to live\n\n"
        "Architectural studies and construction geometry from DomeSim's actual raw-wedge solver. "
        "Explore the frame, the panel jig, and a furnished cutaway. Geometry study; building design and approvals remain project-specific.\n\n"
        "## YouTube\nFrom solved timber pieces to a dome living concept. Follow the panel jig and browse the dimensional guide.\n\n"
        "## Facebook\nA dome you can explore: frame, fit-out concept and illustrated panel fabrication references.\n\n"
        "## Instagram\nCedar, sage, daylight. A compact dome living study, built from the solver's own geometry.\n\n"
        "#DomeSim #sketchGPT #GeodesicDome #TimberDesign #SmallSpaceLiving\n",encoding="utf-8")
    incomplete.unlink()
    files=[p for p in folder.rglob("*") if p.is_file()]
    (folder/"manifest.json").write_text(json.dumps({"schema":1,"name":"sketch-gpt","files":[
        {"path":str(p.relative_to(folder)),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in files]},indent=2),encoding="utf-8")
    medialib.write_index()
    progress(f"Complete: {pdf}")
    return folder


class Studio:
    """Orbitable drawing workspace using the same editable document as world3d."""
    def __init__(self,root):
        import tkinter as tk
        from tkinter import ttk
        self.root=root; self.doc=new_document(); self.selected=None
        self.yaw=-65; self.elevation=25; self.drag=None; self.last_faces=[]
        root.title("sketch-gpt | Dome drawing studio"); root.geometry("1440x920")
        left=ttk.Frame(root,padding=14,width=300); left.pack(side="left",fill="y"); left.pack_propagate(False)
        ttk.Label(left,text="sketch-gpt",font=("Segoe UI",24,"bold")).pack(anchor="w")
        ttk.Label(left,text="DOME DRAWING STUDIO",font=("Segoe UI",10)).pack(anchor="w",pady=(0,14))
        self.palette=tk.StringVar(value="Cedar / sage")
        self.stage=tk.StringVar(value="living")
        for label,var,values in [("Material study",self.palette,list(PALETTES)),("Construction layer",self.stage,[s[1] for s in BUILD_STEPS])]:
            ttk.Label(left,text=label).pack(anchor="w")
            cb=ttk.Combobox(left,textvariable=var,values=values,state="readonly"); cb.pack(fill="x",pady=(0,8))
            cb.bind("<<ComboboxSelected>>",lambda e:self.redraw())
        row=ttk.Frame(left); row.pack(fill="x",pady=6)
        for label,angles in [("Orbit",(-65,25)),("Plan",(-90,90)),("Front",(-90,0))]:
            ttk.Button(row,text=label,command=lambda a=angles:self.view(*a)).pack(side="left")
        ttk.Label(left,text="Drag to orbit. Click a piece to inspect.",wraplength=270).pack(anchor="w",pady=8)
        self.info=tk.StringVar(value="Select a piece in the drawing.")
        ttk.Label(left,textvariable=self.info,wraplength=270).pack(fill="x",pady=8)
        for label,cmd in [("Delete selected",self.delete),("Copy +12 in X",self.copy),("Move +6 in Z",self.move),
                          ("Cut selected at midpoint",self.cut),
                          ("Undo",self.undo),("Save project",self.save),("Reload saved project",self.reload),
                          ("Open cinematic director",self.director),
                          ("Export guide + imagery + model",self.export)]:
            ttk.Button(left,text=label,command=cmd).pack(fill="x",pady=3)
        ttk.Label(left,text="Add square strut: x,y,z endpoints (in)").pack(anchor="w",pady=(12,3))
        self.a=tk.StringVar(value="0,0,30"); self.b=tk.StringVar(value="48,0,30")
        ttk.Entry(left,textvariable=self.a).pack(fill="x"); ttk.Entry(left,textvariable=self.b).pack(fill="x")
        ttk.Button(left,text="Add strut to My pieces",command=self.add).pack(fill="x",pady=3)
        ttk.Label(left,text="Design study. Door, services, connections and envelope require design.\nEdits affect views and OBJ; cut schedules describe the solver baseline.",wraplength=270).pack(anchor="w",pady=15)
        self.canvas=tk.Canvas(root,bg="#f1eee5",highlightthickness=0); self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Configure>",lambda e:self.schedule_draw())
        self.canvas.bind("<ButtonPress-1>",self.press); self.canvas.bind("<B1-Motion>",self.motion)
        self.canvas.bind("<ButtonRelease-1>",self.release)
        self.status=tk.StringVar(value="Ready. Presentation dimensions use the unchanged solver model.")
        ttk.Label(root,textvariable=self.status).pack(side="bottom",fill="x")
        self._after=None
        root.after(100,self.redraw)

    def schedule_draw(self):
        if getattr(self,"_after",None): self.root.after_cancel(self._after)
        self._after=self.root.after(75,self.redraw)

    def view(self,yaw,elevation):
        self.yaw,self.elevation=yaw,elevation; self.redraw()

    def redraw(self):
        from PIL import ImageTk
        self._after=None
        size=(max(600,self.canvas.winfo_width()),max(500,self.canvas.winfo_height()))
        pieces=scene(self.doc,self.stage.get())
        self.photo=ImageTk.PhotoImage(render(pieces,size,self.yaw,self.elevation,self.palette.get(),self.selected))
        self.canvas.delete("all"); self.canvas.create_image(0,0,image=self.photo,anchor="nw")

    def press(self,e): self.drag=(e.x,e.y,self.yaw,self.elevation)
    def motion(self,e):
        if self.drag:
            x,y,a,b=self.drag; self.yaw=a+(e.x-x)*.4; self.elevation=max(-5,min(90,b+(e.y-y)*.3)); self.schedule_draw()
    def release(self,e):
        if self.drag and abs(e.x-self.drag[0])+abs(e.y-self.drag[1])<5:
            p=pick_scene(scene(self.doc,self.stage.get()),(max(600,self.canvas.winfo_width()),max(500,self.canvas.winfo_height())),e.x,e.y,self.yaw,self.elevation)
            self.selected=p.pid if p else None
            self.info.set(f"{p.pid} / {p.name}\nPrincipal extents: "+" x ".join(f"{v:.2f}" for v in p.extents())+" in\n"+str(p.meta) if p else "No piece selected.")
            self.redraw()
        self.drag=None
    def delete(self):
        if self.selected and self.doc.do({"op":"delete","pid":self.selected}): self.selected=None; self.redraw()
    def copy(self):
        if self.selected and self.doc.do({"op":"copy","pid":self.selected,"delta":[12,0,0]}): self.redraw()
    def move(self):
        if self.selected and self.doc.do({"op":"move","pid":self.selected,"delta":[0,0,6]}): self.redraw()
    def cut(self):
        p=self.doc.find(self.selected) if self.selected else None
        if p:
            a,b=p.axis()
            if self.doc.do({"op":"cut","pid":p.pid,"point":((a+b)/2).tolist(),"normal":(b-a).tolist()}):
                self.selected=p.pid+".a"; self.redraw()
    def undo(self): self.doc.undo(); self.redraw()
    def save(self): self.doc.save(SAVE); self.status.set(f"Saved {SAVE}")
    def reload(self): self.doc=new_document(); self.selected=None; self.redraw()
    def add(self):
        from tkinter import messagebox
        try:
            a,b=[np.array([float(x) for x in s.get().split(",")]) for s in (self.a,self.b)]
            if a.shape!=(3,) or b.shape!=(3,) or not np.all(np.isfinite([a,b])) or np.linalg.norm(a-b)<.01:
                raise ValueError("Enter two different finite x,y,z endpoints.")
            self.doc.do({"op":"add","layer":"mine","kind":"square","a":a.tolist(),"b":b.tolist()})
            self.stage.set("frame"); self.redraw()
        except ValueError as exc: messagebox.showerror("Add strut",str(exc))
    def export(self):
        # Solver and Tk stay on the UI thread; progress pumps idle drawing only.
        from tkinter import messagebox
        def update(s): self.status.set(s); self.root.update_idletasks()
        try:
            out=export_package(self.doc,self.palette.get(),update)
            messagebox.showinfo("sketch-gpt release",f"Saved a new release:\n{out}")
        except Exception as exc: messagebox.showerror("Export failed",str(exc))

    def director(self):
        import subprocess
        import sys
        # Each interactive GL workspace owns its process/context, just as the
        # film exporter gives each orientation a separate process.
        subprocess.Popen([sys.executable,'-m','world3d.sketch_gpt','--director'],cwd=ROOT)


def selftest():
    import tempfile
    d=simulator(); m=st.dome_model()
    d.validate_physical_model(m)
    doc=new_document(False)
    assert facts()["members"]==len(doc.layers["dome"])
    for stage in [s[1] for s in BUILD_STEPS]:
        ps=scene(doc,stage); assert ps
        assert render(ps,(800,500)).size==(800,500)
    for i in range(len(d.JIG_STAGES)):
        ps=jig_scene(i); assert ps and all(np.all(np.isfinite(p.points())) for p in ps)
    assert any("-line-" in p.pid for p in jig_scene(1)), "reference triangle missing"
    assert panel_drawing(0).size==(1400,900)
    cube=pc.Piece("test","mine","test",st._box((-1,-1,-1),(1,1,1)),(1,1,1,1))
    assert pick_scene([cube],(800,500),400,260,-90,0).pid=="test"
    assert pick_scene([cube],(800,500),1,1,-90,0) is None
    p=doc.layers["dome"][0]; original=p.points().copy()
    assert doc.do({"op":"move","pid":p.pid,"delta":[0,0,6]})
    assert np.allclose(doc.find(p.pid).points(),original+[0,0,6])
    doc.undo(); assert np.allclose(doc.find(p.pid).points(),original)
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/"frame.obj"; export_obj(scene(doc,"frame"),path)
        assert "o D001" in path.read_text()
        try: export_obj([],path)
        except FileExistsError: pass
        else: raise AssertionError("OBJ overwrite permitted")
    print("sketch-gpt selftest: ok")


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest",action="store_true"); ap.add_argument("--export",action="store_true")
    ap.add_argument("--director",action="store_true")
    a=ap.parse_args()
    if a.director:
        from .cinema_app import main as director_main
        director_main()
    elif a.selftest: selftest()
    elif a.export: print(export_package())
    else:
        import tkinter as tk
        root=tk.Tk(); Studio(root); root.mainloop()
    return 0


if __name__=="__main__": raise SystemExit(main())
