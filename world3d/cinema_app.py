"""Director controls for sketch-gpt's shared Cabin World and episode timeline."""
from __future__ import annotations

import copy
import math
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from . import cinema as cm


class Director:
    def __init__(self, root, episode=None):
        import tkinter as tk
        from tkinter import ttk
        self.tk,self.ttk=tk,ttk; self.root=root
        self.episode=episode or cm.load_episode(); self.history=[]
        self.time=0.; self.selected=0; self.playing=False; self.keys=set()
        self.flight=cm.Flight.home(); self.preview=None; self.closed=False
        self.take=None; self.take_start=0.; self.in_point=0.; self.out_point=self.episode.duration
        self.last=time.perf_counter(); self.drag=None; self.loop=tk.BooleanVar(value=False)
        self.guides=tk.BooleanVar(value=True); self.caption=tk.BooleanVar(value=True)
        self.mode=tk.StringVar(value="Timeline"); self.rate=tk.StringVar(value="1")
        self.format=tk.StringVar(value="640x360"); self.zoom=tk.DoubleVar(value=1)
        self.speed=tk.DoubleVar(value=4); self.damping=tk.DoubleVar(value=5)
        self.status=tk.StringVar(value="Right-drag to look; focus the viewport for WASD. Q/E lift the drone. Shift boosts. Esc stops.")
        root.title("sketch-gpt | Nearly Level director"); root.geometry("1550x1000")
        root.protocol("WM_DELETE_WINDOW",self.close)
        top=ttk.Frame(root,padding=6); top.pack(fill="x")
        ttk.Label(top,text="sketch-gpt / DIRECTOR",font=("Segoe UI",15,"bold")).pack(side="left",padx=(0,18))
        self.mode_box=ttk.Combobox(top,textvariable=self.mode,values=("Timeline","First person","Drone"),state="readonly",width=13)
        self.mode_box.pack(side="left"); self.mode_box.bind("<<ComboboxSelected>>",self.change_mode)
        ttk.Combobox(top,textvariable=self.format,values=("640x360","960x540","540x960"),state="readonly",width=10).pack(side="left",padx=6)
        ttk.Checkbutton(top,text="Framing guides",variable=self.guides,command=self.redraw).pack(side="left")
        ttk.Checkbutton(top,text="Dialogue",variable=self.caption,command=self.redraw).pack(side="left")
        ttk.Button(top,text="Save edit",command=self.save).pack(side="right",padx=3)
        ttk.Button(top,text="Open edit",command=self.load).pack(side="right",padx=3)
        body=ttk.Panedwindow(root,orient="horizontal"); body.pack(fill="both",expand=True)
        def scrolling_panel(width):
            host=ttk.Frame(body)
            canvas=tk.Canvas(host,width=width,highlightthickness=0)
            bar=ttk.Scrollbar(host,orient='vertical',command=canvas.yview)
            bar.pack(side='right',fill='y'); canvas.pack(side='left',fill='both',expand=True)
            canvas.configure(yscrollcommand=bar.set)
            content=ttk.Frame(canvas,padding=5)
            window=canvas.create_window((0,0),window=content,anchor='nw')
            content.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
            canvas.bind('<MouseWheel>',lambda e:canvas.yview_scroll(int(-e.delta/120),'units'))
            return host,content,canvas
        left_host,left,self.tools_scroll=scrolling_panel(275)
        right_host,right,self.inspector_scroll=scrolling_panel(325)
        middle=ttk.Frame(body,padding=5)
        body.add(left_host,weight=1); body.add(middle,weight=5); body.add(right_host,weight=2)
        ttk.Label(left,text="SHOTS / EDIT",font=("Segoe UI",10,"bold")).pack(anchor="w")
        self.list=ttk.Treeview(left,columns=("duration","move"),show="tree headings",height=15)
        self.list.heading("#0",text="Shot"); self.list.heading("duration",text="Sec"); self.list.heading("move",text="Move")
        self.list.column("#0",width=125); self.list.column("duration",width=45); self.list.column("move",width=70)
        self.list.pack(fill="both",expand=True); self.list.bind("<<TreeviewSelect>>",self.choose)
        row=ttk.Frame(left); row.pack(fill="x")
        for label,command in (("+",self.add),("Copy",self.duplicate),("Delete",self.delete)):
            ttk.Button(row,text=label,command=command,width=6).pack(side="left",pady=3)
        row=ttk.Frame(left); row.pack(fill="x")
        for label,command in (("Up",lambda:self.reorder(-1)),("Down",lambda:self.reorder(1)),("Undo",self.undo)):
            ttk.Button(row,text=label,command=command,width=6).pack(side="left",pady=3)
        ttk.Label(left,text="SCOUT / RECORD",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(12,3))
        ttk.Label(left,text="Speed (m/s)").pack(anchor="w")
        ttk.Scale(left,from_=.2,to=12,variable=self.speed).pack(fill="x")
        ttk.Label(left,text="Drone response (1/s)").pack(anchor="w")
        ttk.Scale(left,from_=.5,to=12,variable=self.damping).pack(fill="x")
        for label,command in (("Reset scout camera",self.home),("Capture camera key",self.capture),
                              ("Start / stop motion take",self.record),("Analyze selected shot",self.analyze),
                              ("Open live GPU scout",self.scout),("Import motion take",self.import_take),
                              ("Export storyboard + edit",self.export_edit),("Render episode animatic",self.render_film)):
            ttk.Button(left,text=label,command=command).pack(fill="x",pady=3)
        ttk.Label(left,text="Walk follows floor/deck height. Structure collision is off. Motion takes record camera paths, not screen pixels.",wraplength=245).pack(anchor="w",pady=8)
        self.canvas=tk.Canvas(middle,bg="#142421",highlightthickness=1,highlightbackground="#526d60",takefocus=True)
        self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Button-1>",lambda e:self.canvas.focus_set())
        self.canvas.bind("<ButtonPress-3>",self.look_start); self.canvas.bind("<B3-Motion>",self.look_move)
        self.canvas.bind("<MouseWheel>",self.lens_wheel)
        self.canvas.bind("<KeyPress>",self.key_down); self.canvas.bind("<KeyRelease>",self.key_up)
        self.canvas.bind("<FocusOut>",lambda e:self.keys.clear())
        self.camera_info=tk.StringVar()
        ttk.Label(middle,textvariable=self.camera_info,wraplength=800).pack(fill="x")
        controls=ttk.Frame(middle); controls.pack(fill="x",pady=4)
        for label,command in (("|<",lambda:self.seek(0)),("< frame",lambda:self.step(-1)),("Play / pause",self.play),
                              ("frame >",lambda:self.step(1)),("In",self.mark_in),("Out",self.mark_out)):
            ttk.Button(controls,text=label,command=command).pack(side="left",padx=1)
        ttk.Checkbutton(controls,text="Loop",variable=self.loop).pack(side="left")
        ttk.Combobox(controls,textvariable=self.rate,values=("0.25","0.5","1","2"),state="readonly",width=5).pack(side="left")
        self.clock=tk.StringVar(value="00:00:00:00")
        ttk.Label(controls,textvariable=self.clock,font=("Consolas",12)).pack(side="right")
        self.graph=tk.Canvas(middle,height=115,bg="#182f2c",highlightthickness=0); self.graph.pack(fill="x")
        ttk.Label(right,text="SHOT INSPECTOR",font=("Segoe UI",10,"bold")).pack(anchor="w")
        self.fields={}; self.option_widgets={}
        options={"move":cm.MOVES,"focus":("family","dome","bench","log",*[a.id for a in self.episode.cast]),
                 "speaker":("",*[a.id for a in self.episode.cast]),"action":cm.ACTIONS,"reaction":cm.ACTIONS,
                 "easing":("smooth","linear","ease out")}
        names=[("title","Title"),("duration","Duration (s)"),("move","Motion"),("focus","Focus"),
               ("lens","Start lens (mm)"),("end_lens","End lens (mm)"),("distance","Start distance (m)"),
               ("end_distance","End distance (m)"),("yaw","Bearing (deg)"),("sweep","Travel / sweep"),
               ("height","Camera lift (m)"),("easing","Easing"),("speaker","Speaker"),("action","Action"),("reaction","Listeners")]
        grid=ttk.Frame(right); grid.pack(fill="x")
        for i,(key,label) in enumerate(names):
            ttk.Label(grid,text=label).grid(row=i,column=0,sticky="w",padx=(0,8))
            var=tk.StringVar(); self.fields[key]=var
            widget=ttk.Combobox(grid,textvariable=var,values=options[key],state="readonly",width=17) if key in options else ttk.Entry(grid,textvariable=var,width=20)
            widget.grid(row=i,column=1,sticky="ew",pady=1)
            if key in options: self.option_widgets[key]=widget
        grid.columnconfigure(1,weight=1)
        ttk.Label(right,text="Dialogue").pack(anchor="w",pady=(6,0))
        self.dialogue=tk.Text(right,height=3,wrap="word",font=("Segoe UI",10)); self.dialogue.pack(fill="x")
        ttk.Label(right,text="Meme caption").pack(anchor="w")
        self.caption_text=tk.StringVar(); ttk.Entry(right,textvariable=self.caption_text).pack(fill="x")
        ttk.Button(right,text="Apply shot / ripple timeline",command=self.apply).pack(fill="x",pady=5)
        block=ttk.LabelFrame(right,text="Actor blocking / local metres",padding=5); block.pack(fill="x",pady=4)
        self.actor=tk.StringVar(value=self.episode.cast[0].id)
        cb=ttk.Combobox(block,textvariable=self.actor,values=[a.id for a in self.episode.cast],state="readonly"); cb.pack(fill="x")
        self.actor_box=cb
        cb.bind("<<ComboboxSelected>>",lambda e:self.load_block())
        self.block_from=tk.StringVar(); self.block_to=tk.StringVar()
        for label,var in (("From x,y,z",self.block_from),("To x,y,z",self.block_to)):
            ttk.Label(block,text=label).pack(anchor="w"); ttk.Entry(block,textvariable=var).pack(fill="x")
        ttk.Button(block,text="Apply blocking",command=self.apply_block).pack(fill="x",pady=3)
        ttk.Label(right,text="Guides: thirds, 90% safe area, phone crop. The phone export uses its own camera fit.",wraplength=280).pack(anchor="w",pady=5)
        timeline_box=ttk.Frame(root,padding=5); timeline_box.pack(fill="x")
        row=ttk.Frame(timeline_box); row.pack(fill="x")
        ttk.Label(row,text="TIMELINE / click to scrub; drag a shot's right edge to trim",font=("Segoe UI",10,"bold")).pack(side="left")
        ttk.Label(row,text="Zoom").pack(side="left",padx=(18,3))
        ttk.Scale(row,from_=1,to=10,variable=self.zoom,command=lambda v:self.draw_timeline()).pack(side="left",fill="x",expand=True)
        self.timeline=tk.Canvas(timeline_box,height=155,bg="#152a27",highlightthickness=0); self.timeline.pack(fill="x")
        scroll=ttk.Scrollbar(timeline_box,orient="horizontal",command=self.timeline.xview); scroll.pack(fill="x")
        self.timeline.configure(xscrollcommand=scroll.set)
        self.timeline.bind("<ButtonPress-1>",self.timeline_press); self.timeline.bind("<B1-Motion>",self.timeline_motion)
        self.timeline.bind("<ButtonRelease-1>",self.timeline_release)
        self.timeline.bind("<Configure>",lambda e:self.draw_timeline())
        ttk.Label(root,textvariable=self.status,anchor="w").pack(fill="x",padx=8,pady=3)
        self.refresh(); self.select(0); self._tick_id=root.after(100,self.tick)

    def remember(self):
        self.history.append((copy.deepcopy(self.episode),self.selected,self.time)); self.history=self.history[-30:]

    def show_error(self,exc):
        from tkinter import messagebox
        messagebox.showerror("sketch-gpt director",str(exc),parent=self.root)

    def refresh(self):
        self.list.delete(*self.list.get_children())
        for i,c in enumerate(self.episode.clips): self.list.insert("","end",iid=str(i),text=f"{i+1:02d} {c.title}",values=(f"{c.duration:g}",c.move))
        self.in_point=min(self.in_point,max(0,self.episode.duration-.1))
        self.out_point=min(max(self.in_point+.1,self.out_point),self.episode.duration)
        self.time=min(self.time,self.episode.duration-1e-5); self.draw_timeline()

    def select(self,index):
        self.selected=max(0,min(index,len(self.episode.clips)-1))
        c=self.episode.clips[self.selected]
        for key,var in self.fields.items(): var.set(str(getattr(c,key)))
        self.dialogue.delete("1.0","end"); self.dialogue.insert("1.0",c.dialogue)
        self.caption_text.set(c.caption); self.load_block()
        self.list.selection_set(str(self.selected)); self.list.see(str(self.selected)); self.analyze()

    def choose(self,event=None):
        selection=self.list.selection()
        if selection and int(selection[0])!=self.selected:
            self.select(int(selection[0])); self.seek(float(self.episode.starts()[self.selected]))

    def apply(self):
        try:
            numeric={"duration","lens","end_lens","distance","end_distance","yaw","sweep","height"}
            values={k:float(v.get()) if k in numeric else v.get() for k,v in self.fields.items()}
            candidate=copy.deepcopy(self.episode)
            candidate.clips[self.selected]=replace(candidate.clips[self.selected],**values,
                dialogue=self.dialogue.get("1.0","end").strip(),caption=self.caption_text.get())
            candidate.validate(); self.remember(); self.episode=candidate
            self.refresh(); self.select(self.selected); self.redraw()
        except Exception as exc: self.show_error(exc)

    def load_block(self):
        a=next(a for a in self.episode.cast if a.id==self.actor.get())
        path=self.episode.clips[self.selected].blocking.get(a.id,{"from":a.position,"to":a.position})
        self.block_from.set(",".join(map(str,path["from"]))); self.block_to.set(",".join(map(str,path["to"])))

    def apply_block(self):
        try:
            path={"from":[float(x) for x in self.block_from.get().split(",")],"to":[float(x) for x in self.block_to.get().split(",")]}
            candidate=copy.deepcopy(self.episode); candidate.clips[self.selected].blocking[self.actor.get()]=path
            candidate.validate(); self.remember(); self.episode=candidate; self.redraw(); self.analyze()
        except Exception as exc: self.show_error(exc)

    def add(self):
        self.remember(); i=self.selected+1
        self.episode.clips.insert(i,cm.Clip(self.new_id(),"New shot",5))
        self.out_point=self.episode.duration; self.refresh(); self.select(i)

    def new_id(self):
        used={c.id for c in self.episode.clips}; n=1
        while f"shot-{n:02d}" in used: n+=1
        return f"shot-{n:02d}"

    def duplicate(self):
        self.remember(); i=self.selected+1; c=copy.deepcopy(self.episode.clips[self.selected]); c.id=self.new_id(); c.title+=" copy"
        self.episode.clips.insert(i,c); self.out_point=self.episode.duration; self.refresh(); self.select(i)

    def delete(self):
        if len(self.episode.clips)>1:
            self.remember(); del self.episode.clips[self.selected]; self.refresh(); self.select(min(self.selected,len(self.episode.clips)-1)); self.redraw()

    def reorder(self,direction):
        j=self.selected+direction
        if 0<=j<len(self.episode.clips):
            self.remember(); clips=self.episode.clips; clips[j],clips[self.selected]=clips[self.selected],clips[j]
            self.refresh(); self.select(j); self.redraw()

    def undo(self):
        if self.history:
            self.episode,self.selected,self.time=self.history.pop()
            self.refresh(); self.select(min(self.selected,len(self.episode.clips)-1)); self.redraw()

    def save(self):
        try: self.episode.save(); self.status.set(f"Saved episode to {cm.SAVE}")
        except Exception as exc: self.show_error(exc)

    def load(self):
        from tkinter import filedialog
        path=filedialog.askopenfilename(parent=self.root,filetypes=[("Episode JSON","*.json")],initialdir=str(cm.SAVE.parent))
        if path:
            try:
                ep=cm.load_episode(path); self.remember(); self.episode=ep; self.time=0; self.out_point=ep.duration
                # This editor supports arbitrary cast IDs through its selectors.
                values=tuple(a.id for a in ep.cast)
                self.actor_box.configure(values=values)
                self.option_widgets['speaker'].configure(values=("",*values))
                self.option_widgets['focus'].configure(values=("family","dome","bench","log",*values))
                self.actor.set(values[0]); self.refresh(); self.select(0); self.redraw()
            except Exception as exc: self.show_error(exc)

    def seek(self,t):
        self.time=float(np.clip(t,0,max(0,self.episode.duration-1e-6))); self.redraw(); self.draw_timeline()

    def step(self,n): self.playing=False; self.seek(self.time+n/self.episode.fps)
    def play(self): self.playing=not self.playing; self.mode.set("Timeline"); self.keys.clear(); self.last=time.perf_counter()
    def mark_in(self): self.in_point=self.time; self.out_point=max(self.out_point,self.in_point+.1); self.draw_timeline()
    def mark_out(self): self.out_point=max(self.in_point+.1,self.time); self.draw_timeline()

    def change_mode(self,event=None):
        self.playing=False; self.keys.clear(); self.home()

    def home(self):
        self.flight=cm.Flight.home("walk" if self.mode.get()=="First person" else "drone"); self.redraw()

    def key_down(self,event):
        key=event.keysym.lower()
        if key=="escape": self.playing=False; self.keys.clear(); self.root.focus_set()
        elif key=="space": self.play()
        else: self.keys.add(key)
        return "break"
    def key_up(self,event): self.keys.discard(event.keysym.lower()); return "break"
    def look_start(self,event): self.canvas.focus_set(); self.drag=(event.x,event.y)
    def look_move(self,event):
        if self.drag and self.mode.get()!="Timeline":
            self.flight.look(event.x-self.drag[0],event.y-self.drag[1]); self.drag=(event.x,event.y)
    def lens_wheel(self,event): self.flight.lens=float(np.clip(self.flight.lens-event.delta/120*2,12,150)); self.redraw()

    def capture(self):
        try:
            eye,target,fov=self.current_camera()
            lens=cm.CONSTANTS["sensor_height_mm"]/(2*math.tan(math.radians(fov)/2))
            key={"eye":eye.tolist(),"target":target.tolist(),"lens":float(np.clip(lens,12,200))}
            self.remember(); clip=self.episode.clips[self.selected]; clip.keyframes.append(key)
            if len(clip.keyframes)>=2: clip.move="spline"
            self.select(self.selected); self.status.set(f"Captured {len(clip.keyframes)} camera keys. Two keys enable the spline move.")
        except Exception as exc: self.show_error(exc)

    def record(self):
        if self.take is None:
            if self.mode.get()=="Timeline": self.mode.set("Drone"); self.home()
            self.take=[]; self.take_start=time.perf_counter(); self.status.set("Recording motion path. Fly the camera; press again to save a take.")
        else:
            elapsed=time.perf_counter()-self.take_start
            if len(self.take)<2: self.status.set("Move the camera and record at least two samples."); self.take=None; return
            self.remember()
            try:
                clip=cm.motion_clip({"schema":"sketch-gpt.motion/1","samples":self.take},self.new_id())
            except ValueError as exc:
                self.take=None; self.show_error(exc); return
            self.episode.clips.append(clip)
            self.take=None; self.out_point=self.episode.duration; self.refresh(); self.select(len(self.episode.clips)-1)
            self.status.set("Motion take added to the timeline. Render footage through the film exporter.")

    def current_camera(self):
        if self.mode.get()=="Timeline":
            _,c,p,_=self.episode.locate(self.time); w,h=map(int,self.format.get().split("x"))
            return cm.shot_camera(self.episode,c,p,w/h)
        return self.flight.state()

    def redraw(self):
        if self.closed: return
        from PIL import ImageTk
        try:
            w,h=map(int,self.format.get().split("x"))
            if self.preview is None or (self.preview.width,self.preview.height)!=(w,h):
                if self.preview: self.preview.close()
                self.preview=cm.Preview(w,h)
            camera=self.current_camera()
            image=self.preview.frame(self.episode,self.time,camera,self.guides.get(),self.caption.get())
            image.thumbnail((max(200,self.canvas.winfo_width()),max(200,self.canvas.winfo_height())))
            self.photo=ImageTk.PhotoImage(image); self.canvas.delete("all")
            self.canvas.create_image(self.canvas.winfo_width()/2,self.canvas.winfo_height()/2,image=self.photo,anchor="center")
            eye,target,fov=camera
            self.camera_info.set(f"{self.mode.get()} | eye {', '.join(f'{v:.2f}' for v in eye)} m | FOV {fov:.1f} deg | {self.episode.episode}")
            frame=round(self.time*self.episode.fps); sec,fr=divmod(frame,self.episode.fps); mins,sec=divmod(sec,60)
            self.clock.set(f"{mins//60:02d}:{mins%60:02d}:{sec:02d}:{fr:02d}")
        except Exception as exc: self.status.set(f"Preview error: {exc}"); self.playing=False

    def tick(self):
        if self.closed: return
        now=time.perf_counter(); dt=now-self.last; self.last=now
        if self.playing:
            self.time+=dt*float(self.rate.get())
            end=self.out_point if self.loop.get() else self.episode.duration
            if self.time>=end:
                if self.loop.get(): self.time=self.in_point+(self.time-end)%max(.1,end-self.in_point)
                else: self.playing=False; self.time=self.episode.duration-1e-5
            self.redraw(); self.draw_timeline()
        elif self.mode.get()!="Timeline":
            self.flight.speed=self.speed.get(); self.flight.damping=self.damping.get()
            self.flight.step(self.keys,dt,"shift_l" in self.keys or "shift_r" in self.keys)
            if self.take is not None:
                eye,target,_=self.flight.state(); self.take.append({"time_s":time.perf_counter()-self.take_start,"eye":eye.tolist(),"target":target.tolist(),"lens":self.flight.lens})
                if len(self.take)>3600: self.record()
            self.redraw()
        self._tick_id=self.root.after(50,self.tick)

    def draw_timeline(self):
        if not hasattr(self,"timeline"): return
        c=self.timeline; c.delete("all"); total=self.episode.duration
        self.pixels=max(600,c.winfo_width()-100)*self.zoom.get()/total
        width=100+total*self.pixels; c.configure(scrollregion=(0,0,width,155))
        for j,label in enumerate(("CAMERA","DIALOGUE","ACTIONS","MARKERS")):
            c.create_text(5,35+j*29,text=label,anchor="w",fill="#b2c7bd",font=("Segoe UI",8,"bold"))
        for sec in np.arange(0,total+1,max(1,round(total/14))):
            x=95+sec*self.pixels; c.create_line(x,0,x,150,fill="#314b43"); c.create_text(x+3,8,text=f"{sec:g}s",anchor="w",fill="#b8c6ba")
        for i,(start,clip) in enumerate(zip(self.episode.starts(),self.episode.clips)):
            x0,x1=95+start*self.pixels,95+(start+clip.duration)*self.pixels
            for row,color,text in [(0,"#528b82",clip.title),(1,"#766c99",clip.speaker),(2,"#8b7553",clip.action),(3,"#485c48",clip.marker)]:
                y=23+row*29
                c.create_rectangle(x0+1,y,x1-1,y+24,fill=color,outline="#e4c77c" if i==self.selected else "#142824",width=2 if i==self.selected else 1)
                if x1-x0>30: c.create_text(x0+5,y+12,text=text[:max(2,int((x1-x0)/7)-1)],anchor="w",fill="white",font=("Segoe UI",9))
        for t,label,color in ((self.time,"", "#f3d990"),(self.in_point,"I","#79d4bd"),(self.out_point,"O","#79d4bd")):
            x=95+t*self.pixels; c.create_line(x,0,x,150,fill=color,width=2); c.create_text(x+3,148,text=label,anchor="sw",fill=color)

    def timeline_press(self,event):
        x=self.timeline.canvasx(event.x); t=max(0,(x-95)/self.pixels)
        i,clip,_,start=self.episode.locate(t)
        self.playing=False
        ends=95+self.episode.starts()[1:]*self.pixels
        nearest=int(np.argmin(np.abs(ends-x)))
        if abs(x-ends[nearest])<8:
            self.select(nearest); self.remember()
            self.trim=(nearest,self.episode.clips[nearest].duration,x)
        else:
            self.select(i); self.trim=None; self.seek(t)
    def timeline_motion(self,event):
        if getattr(self,"trim",None):
            i,duration,x=self.trim; delta=(self.timeline.canvasx(event.x)-x)/self.pixels
            self.episode.clips[i].duration=float(np.clip(duration+delta,.6,300)); self.draw_timeline()
        else: self.seek((self.timeline.canvasx(event.x)-95)/self.pixels)
    def timeline_release(self,event):
        if getattr(self,"trim",None): self.trim=None; self.refresh(); self.select(self.selected)

    def analyze(self):
        if not hasattr(self,"graph"): return
        report=cm.analysis(self.episode,self.selected)
        g=self.graph; g.delete("all"); w=max(500,g.winfo_width()); h=115
        g.create_text(8,12,anchor="w",fill="#efe1b5",text=f"PATH {report['path_length_m']:.2f} m | PEAK {report['peak_speed_m_s']:.2f} m/s | PAN {report['peak_angular_deg_s']:.1f} deg/s | DIALOGUE {report['dialogue_wpm']:.0f} wpm")
        for k,col in (("speed_m_s","#83d5be"),("angular_deg_s","#dfac74")):
            values=report[k]; maximum=max(max(values),.01)
            points=[]
            for j,v in enumerate(values): points.extend([10+j*(w-20)/max(1,len(values)-1),h-18-v/maximum*60])
            g.create_line(*points,fill=col,width=2)
        g.create_text(8,h-5,anchor="sw",fill="#b6cabe",text="Speed (green) / angular speed (amber); independently normalized | "+("; ".join(report["warnings"]) or "Framing samples passed"))

    def export_edit(self):
        try:
            # The storyboard exporter owns a temporary standalone GL context.
            # Recreate the review context afterward instead of using one that
            # has ceased to be current on this thread.
            if self.preview: self.preview.close(); self.preview=None
            self.status.set("Exporting storyboard and edit..."); self.root.update_idletasks()
            path=cm.export_edit(self.episode); self.status.set(f"Production edit saved: {path}")
        except Exception as exc: self.show_error(exc)
        finally: self.redraw()

    def render_film(self):
        try:
            self.episode.save()
            log=cm.ROOT/"tmp/sketch-gpt-director/render.log"; log.parent.mkdir(parents=True,exist_ok=True)
            with log.open("a",encoding="utf-8") as f:
                subprocess.Popen([sys.executable,"-u","-m","film","make",cm.LESSON_KEY,"--no-teaser"],cwd=cm.ROOT,stdout=f,stderr=subprocess.STDOUT)
            self.status.set(f"Animatic render launched (landscape + phone + release). Progress: {log}")
        except Exception as exc: self.show_error(exc)

    def scout(self):
        self.episode.save()
        subprocess.Popen([sys.executable,"-m","world3d.cinema_live"],cwd=cm.ROOT)
        self.status.set("Live scout opened. R records a motion take; import the saved take here to add it to the timeline.")

    def import_take(self):
        from tkinter import filedialog
        import json
        path=filedialog.askopenfilename(parent=self.root,initialdir=str(cm.ROOT/'deliverables'),filetypes=[("Camera take JSON","*.json")])
        if not path: return
        try:
            clip=cm.motion_clip(json.loads(Path(path).read_text(encoding='utf-8')),self.new_id())
            candidate=copy.deepcopy(self.episode); candidate.clips.append(clip); candidate.validate()
            self.remember(); self.episode=candidate; self.out_point=candidate.duration
            self.refresh(); self.select(len(candidate.clips)-1); self.mode.set('Timeline'); self.seek(float(candidate.starts()[-2]))
        except Exception as exc: self.show_error(exc)

    def close(self):
        self.closed=True; self.keys.clear()
        if getattr(self,'_tick_id',None): self.root.after_cancel(self._tick_id)
        if self.preview: self.preview.close()
        self.root.destroy()


def main():
    import tkinter as tk
    root=tk.Tk(); Director(root); root.mainloop()


if __name__=="__main__": main()
