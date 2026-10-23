"""Native GPU scout for the same sketch-gpt Cabin World production.

The director's panel preview is for reviewing frames. This viewport keeps the
world on the GPU for responsive first-person/drone operation and camera takes.
"""
from __future__ import annotations

import math
import time

import numpy as np

from . import cinema as cm
from .app import _dome, text_surface
from two_v_demo import cabin_world as cw
from two_v_demo.render_kit import SCENE_VERTEX_SHADER, SCENE_FRAGMENT_SHADER, perspective, look_at


class Scout:
    def __init__(self,episode=None,size=(1280,720)):
        import pygame as pg
        import moderngl
        self.pg,self.gl=pg,moderngl
        pg.init()
        for attr,val in ((pg.GL_CONTEXT_MAJOR_VERSION,3),(pg.GL_CONTEXT_MINOR_VERSION,3),
                         (pg.GL_CONTEXT_PROFILE_MASK,pg.GL_CONTEXT_PROFILE_CORE)):
            pg.display.gl_set_attribute(attr,val)
        pg.display.set_mode(size,pg.OPENGL|pg.DOUBLEBUF|pg.RESIZABLE)
        pg.display.set_caption("sketch-gpt | live cinematic scout")
        self.ctx=moderngl.create_context()
        self.program=self.ctx.program(vertex_shader=SCENE_VERTEX_SHADER,fragment_shader=SCENE_FRAGMENT_SHADER)
        self.overlay=_dome().Renderer(self.ctx)
        self.meshes={}; self.episode=episode or cm.load_episode()
        for key in cw.LAYERS:
            if key!="builder": self.upload(key,cw.layer(key))
        self.upload("episode-props",cm.set_props())
        self.upload("cast",cm.cast_geometry(self.episode,0))
        self.flight=cm.Flight.home("walk"); self.mode="walk"
        self.timeline=0.; self.playing=False; self.captured=False; self.running=True
        self.take=None; self.take_start=0.; self.take_last=0.; self.last_cast=0
        self.clock=pg.time.Clock(); self.hud=True; self.status="F1 controls | Tab mouse look | 1 walk / 2 drone / 3 timeline"
        self.last_overlay=0.; self.capture(True)

    def upload(self,key,batch):
        if key in self.meshes:
            buffer,vao=self.meshes.pop(key); vao.release(); buffer.release()
        data=np.asarray(batch.vertices,dtype='f4')
        buffer=self.ctx.buffer(data.tobytes())
        vao=self.ctx.vertex_array(self.program,[(buffer,"3f 3f 4f","in_position","in_normal","in_color")])
        self.meshes[key]=(buffer,vao)

    def capture(self,on):
        self.captured=on; self.pg.event.set_grab(on); self.pg.mouse.set_visible(not on); self.pg.mouse.get_rel()

    def camera(self):
        if self.mode=="timeline":
            _,clip,p,_=self.episode.locate(self.timeline)
            w,h=self.pg.display.get_window_size(); return cm.shot_camera(self.episode,clip,p,w/h)
        return self.flight.state()

    def record(self):
        if self.take is None:
            self.take=[]; self.take_start=time.perf_counter(); self.take_last=0
            self.status="REC camera path / R stops and saves a new take"
        else:
            if len(self.take)>=2:
                import json, medialib
                folder=medialib.new_folder("sketch-gpt-camera-take")
                path=folder/"camera-take.json"
                path.write_text(json.dumps({"schema":"sketch-gpt.motion/1","units":"metres, seconds, millimetres",
                    "duration":self.take[-1]["time_s"],"samples":self.take},indent=2),encoding="utf-8")
                medialib.write_index(); self.status=f"Saved {folder.name}; import motion take in the director"
                print(path,flush=True)
            else: self.status="Take too short: record at least two samples"
            self.take=None

    def handle(self):
        pg=self.pg
        for event in pg.event.get():
            if event.type==pg.QUIT: self.running=False
            elif event.type==pg.KEYDOWN:
                key=event.key
                if key==pg.K_ESCAPE:
                    if self.captured: self.capture(False)
                    else: self.running=False
                elif key==pg.K_TAB: self.capture(not self.captured)
                elif key in (pg.K_1,pg.K_2,pg.K_3):
                    self.mode={pg.K_1:"walk",pg.K_2:"drone",pg.K_3:"timeline"}[key]
                    if self.mode!="timeline":
                        self.flight.mode=self.mode; self.flight.velocity[:]=0
                        self.flight.speed=cm.CONSTANTS['drone_speed_m_s'] if self.mode=='drone' else cm.CONSTANTS['walk_speed_m_s']
                elif key==pg.K_SPACE: self.playing=not self.playing; self.mode="timeline"
                elif key==pg.K_HOME: self.flight=cm.Flight.home("drone" if self.mode=="drone" else "walk")
                elif key==pg.K_F1: self.hud=not self.hud
                elif key==pg.K_r: self.record()
                elif key==pg.K_LEFT: self.timeline=max(0,self.timeline-1/self.episode.fps)
                elif key==pg.K_RIGHT: self.timeline=min(self.episode.duration-1e-6,self.timeline+1/self.episode.fps)
                elif key in (pg.K_EQUALS,pg.K_PLUS): self.flight.speed=min(20,self.flight.speed*1.25)
                elif key==pg.K_MINUS: self.flight.speed=max(.2,self.flight.speed/1.25)
            elif event.type==pg.MOUSEMOTION and self.captured and self.mode!="timeline":
                self.flight.look(*event.rel)
            elif event.type==pg.MOUSEWHEEL:
                self.flight.lens=float(np.clip(self.flight.lens-event.y*2,12,150))
            elif event.type==pg.WINDOWFOCUSLOST:
                self.capture(False)

    def update(self,dt):
        pg=self.pg
        if self.playing:
            self.timeline=(self.timeline+dt)%self.episode.duration
        if self.mode!="timeline" and self.captured:
            held=pg.key.get_pressed()
            keys={name for name,key in (("w",pg.K_w),("a",pg.K_a),("s",pg.K_s),("d",pg.K_d),("q",pg.K_q),("e",pg.K_e)) if held[key]}
            self.flight.step(keys,dt,held[pg.K_LSHIFT] or held[pg.K_RSHIFT])
        # Actors update when the timeline changes, never during a static camera scout.
        phase=round(self.timeline*8)
        if phase!=self.last_cast:
            self.upload("cast",cm.cast_geometry(self.episode,self.timeline)); self.last_cast=phase
        if self.take is not None:
            now=time.perf_counter()-self.take_start
            if now-self.take_last>=1/12:
                eye,target,fov=self.camera(); lens=24/(2*math.tan(math.radians(fov)/2))
                self.take.append({"time_s":now,"eye":eye.tolist(),"target":target.tolist(),"lens":float(np.clip(lens,12,200))}); self.take_last=now
                if now>=300: self.record()

    def render(self):
        pg,gl=self.pg,self.gl; w,h=pg.display.get_window_size()
        self.ctx.viewport=(0,0,w,h); self.ctx.clear(.35,.38,.32,1,depth=1)
        eye,target,fov=self.camera(); mvp=perspective(fov,w/max(1,h),.05,400)@look_at(eye,target)
        self.program["u_mvp"].write(np.ascontiguousarray(mvp.T).astype('f4').tobytes())
        self.program["u_camera"].value=tuple(map(float,eye)); self.program["u_light"].value=cw.LIGHT
        self.ctx.enable(gl.DEPTH_TEST); self.ctx.disable(gl.CULL_FACE)
        for _,vao in self.meshes.values(): vao.render()
        if self.hud:
            now=time.perf_counter()
            if now-self.last_overlay>.2:
                lines=["sketch-gpt / LIVE CINEMATIC SCOUT",self.status,
                    f"{self.mode.upper()}  {self.timeline:.2f}/{self.episode.duration:g} s  lens {self.flight.lens:g} mm  speed {self.flight.speed:.2f} m/s",
                    "WASD move | mouse look | Q/E drone lift | wheel lens | +/- speed | Shift boost",
                    "1 walk | 2 drone | 3 shot timeline | Space play/pause | arrows step frame",
                    "R record motion take | Home reset | Tab mouse | Esc release / quit | F1 HUD",
                    "Floor support on; structure collision off. Scout lighting is ungraded."]
                self.overlay.upload_overlay("scout-info",text_surface(lines,min(w-30,980)))
                self.last_overlay=now
            self.overlay.render_overlay("scout-info",w,h,15,15)
        pg.display.flip()

    def run(self,frames=0):
        count=0; began=time.perf_counter()
        try:
            while self.running:
                dt=self.clock.tick(60)/1000; self.handle(); self.update(dt); self.render(); count+=1
                if frames and count>=frames: break
        finally:
            if self.take is not None: self.record()
            for buffer,vao in self.meshes.values(): vao.release(); buffer.release()
            self.overlay.release(); self.program.release(); self.ctx.release(); self.pg.quit()
        print(f"Live scout: {count} frames, {count/max(.001,time.perf_counter()-began):.1f} average fps",flush=True)


def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--frames",type=int,default=0)
    args=ap.parse_args(); Scout().run(args.frames)


if __name__=="__main__": main()
