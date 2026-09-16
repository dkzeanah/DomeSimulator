"""Additive book reader, semantic scene stills, catalog browser, and publishing UI."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .storage import stamp


class BookMediaDesk:
    def __init__(self, desk):
        self.desk = desk
        self.catalog = None
        self.matches = []
        self.catalog_rows = []
        self.events = queue.Queue()
        self.running = False
        self.reader_images = []
        self.reader_tables = []
        self.proof_images = []
        self.publication = None
        self.last_video = None
        self.proof_index = 0
        self.last_query = None
        self.job_after = None
        self.reader = self.frame('Read', index=1)
        self.scenes = self.frame('Scenes')
        self.lexicon = self.frame('Catalog')
        self.publish = self.frame('Publish')
        self.build_reader()
        self.build_scenes()
        self.build_catalog_browser()
        self.build_publish()
        self.desk.tabs.bind('<<NotebookTabChanged>>', self.tab_changed, add=True)
        self.desk.bind('<Destroy>', self.destroyed, add=True)
        self.job_after = desk.after(150, self.poll)
        snapshots=sorted((desk.store.home/'catalogs').glob('*.json'))
        if snapshots:
            try:
                catalog=json.loads(snapshots[-1].read_text(encoding='utf-8'))
                if catalog.get('schema')=='two-trees-codex-scene-catalog/v1':
                    self.catalog=catalog
                    self.filter_catalog()
            except (ValueError,OSError):
                pass
        # Restore the last publication only as a labeled snapshot, never as live prose.
        indices = sorted((desk.store.home/'publication-index').glob('*.json'))
        if indices:
            try:
                self.publication = json.loads(indices[-1].read_text(encoding='utf-8'))
                self.publication_status.set('Previous publication snapshot available; rebuild after edits.')
                self.show_proof(0)
                videos=sorted(Path(self.publication['output_dir']).glob('silent-readthrough-*/readthrough.json'))
                if videos:
                    candidate=json.loads(videos[-1].read_text(encoding='utf-8'))
                    if Path(candidate['video']).is_file():
                        self.last_video=candidate
            except (ValueError, OSError, KeyError):
                self.publication = None

    def frame(self, title, index=None):
        frame = ttk.Frame(self.desk.tabs, padding=8)
        if index is None:
            self.desk.tabs.add(frame, text=title)
        else:
            self.desk.tabs.insert(index, frame, text=title)
        return frame

    def notice(self, parent, text):
        label = ttk.Label(parent, text=text, wraplength=730, style='BookMeta.TLabel')
        label.pack(fill='x', pady=(4, 7))
        label.bind('<Configure>', lambda e: label.configure(wraplength=max(150,e.width-8)))
        return label

    def build_reader(self):
        bar = ttk.Frame(self.reader)
        bar.pack(fill='x')
        self.read_scope = tk.StringVar(value='Current chapter')
        scope = ttk.Combobox(bar, textvariable=self.read_scope, state='readonly',
                             values=('Current chapter', 'Whole manuscript'), width=22)
        scope.pack(side='left')
        scope.bind('<<ComboboxSelected>>', lambda e: self.refresh_reader())
        ttk.Button(bar, text='Previous', command=lambda: self.change_chapter(-1)).pack(side='left',padx=4)
        ttk.Button(bar, text='Next', command=lambda: self.change_chapter(1)).pack(side='left')
        ttk.Button(bar, text='Refresh', command=self.refresh_reader).pack(side='left',padx=4)
        self.notice(self.reader, 'Live manuscript reading view. PDF page proofs are in Publish; both include attached stills and captions.')
        self.read_text = self.desk.text_area(self.reader, 'Georgia', 12)
        for name, options in {
            'title':dict(font=('Georgia',21,'bold'),foreground='#234e3a',spacing1=20,spacing3=12),
            'heading':dict(font=('Georgia',15,'bold'),spacing1=12,spacing3=8),
            'meta':dict(font=('Segoe UI',9),foreground='#657464',spacing3=10),
            'caption':dict(font=('Segoe UI',10),foreground='#55715f',spacing1=8,spacing3=15),
            'code':dict(font=('Consolas',10),background='#eeeee3'),
            'rule':dict(foreground='#b4b6a5',spacing1=28,spacing3=28),
        }.items():
            self.read_text.tag_configure(name, **options)
        self.read_text.configure(state='disabled')

    def change_chapter(self, delta):
        pages = self.desk.store.book['pages']
        index = next((i for i,p in enumerate(pages) if p['id']==self.desk.current),0)
        self.desk.select_page(pages[max(0,min(len(pages)-1,index+delta))]['id'])
        self.refresh_reader()

    def refresh_reader(self):
        self.desk.capture()
        pages = self.desk.store.book['pages'] if self.read_scope.get()=='Whole manuscript' else [self.desk.page()]
        text = self.read_text
        text.configure(state='normal')
        for table in self.reader_tables:
            table.destroy()
        self.reader_tables=[]
        text.delete('1.0','end')
        self.reader_images = []
        for page in pages:
            if page is None:
                continue
            text.insert('end',page['title']+'\n','title')
            text.insert('end',f"{page['kind']} · {page['strand']} · {page['status']}\n",'meta')
            def render_body(source_text):
                code = False
                table_lines=[]
                def flush_table():
                    if not table_lines:
                        return
                    rows=[[cell.strip() for cell in line.strip().strip('|').split('|')] for line in table_lines]
                    rows=[row for row in rows if not all(re.fullmatch(r'[: -]+',cell or ' ') for cell in row)]
                    if rows:
                        frame=tk.Frame(text,bg='#c6cebd',padx=1,pady=1)
                        columns=max(len(row) for row in rows)
                        cell_width=max(70,min(850,text.winfo_width()-70)//columns-16)
                        for row_index,row in enumerate(rows):
                            for column,cell in enumerate(row+['']*(columns-len(row))):
                                cell=re.sub(r'\*\*([^*]+)\*\*',r'\1',cell)
                                tk.Label(frame,text=cell,wraplength=cell_width,justify='left',anchor='w',
                                         font=('Segoe UI',10,'bold' if row_index==0 else 'normal'),
                                         fg='#263e32',bg='#e7ecdf' if row_index==0 else '#f4f4e8',
                                         padx=7,pady=6).grid(row=row_index,column=column,sticky='nsew',padx=1,pady=1)
                        self.reader_tables.append(frame)
                        text.window_create('end',window=frame)
                        text.insert('end','\n')
                    table_lines.clear()
                for line in source_text.splitlines():
                    if not code and line.startswith('|'):
                        table_lines.append(line)
                        continue
                    flush_table()
                    if line.startswith('```'):
                        code = not code
                        continue
                    tag = 'code' if code or line.startswith('|') else ('heading' if line.startswith('#') else None)
                    clean = line.lstrip('# ') if line.startswith('#') else line
                    if not code:
                        clean = re.sub(r'\*\*([^*]+)\*\*',r'\1',clean)
                        clean = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',r'\1 (\2)',clean)
                    text.insert('end',clean+'\n',tag)
                flush_table()
            def render_figure(key):
                asset = self.desk.store.book['assets'].get(key)
                if asset is None:
                    return
                try:
                    from PIL import Image, ImageTk
                    with Image.open(self.desk.store.asset_path(asset)) as source:
                        im = source.copy()
                    im.thumbnail((max(300,min(740,text.winfo_width()-65)),650))
                    photo = ImageTk.PhotoImage(im,master=self.desk)
                    self.reader_images.append(photo)
                    text.insert('end','\n')
                    text.image_create('end',image=photo)
                    text.insert('end','\n'+asset['caption']+'\n'+asset['provenance']+'\n','caption')
                except Exception as exc:
                    text.insert('end',f"\nImage unavailable: {exc}\n",'caption')
            from .reading import reading_parts
            for kind,value in reading_parts(page,self.desk.store.book['assets']):
                if kind=='text':
                    render_body(value)
                else:
                    render_figure(value)
            if self.read_scope.get()=='Whole manuscript':
                text.insert('end','────────────────────────────────────\n','rule')
        text.configure(state='disabled')

    def build_scenes(self):
        ttk.Label(self.scenes,text='Find the scene that explains this passage',font=('Georgia',16)).pack(anchor='w')
        self.notice(self.scenes, 'Match chapter language to existing video scenes, or enter a phrase. Choose an animation moment and render the real scene as a still.')
        row = ttk.Frame(self.scenes)
        row.pack(fill='x')
        self.query = tk.StringVar()
        ttk.Entry(row,textvariable=self.query).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Match phrase',command=lambda:self.match_page(custom=True)).pack(side='left',padx=4)
        ttk.Button(row,text='Match chapter',command=self.match_page).pack(side='left')
        list_frame = ttk.Frame(self.scenes)
        list_frame.pack(fill='both',expand=True,pady=8)
        self.scene_list = ttk.Treeview(list_frame,columns=('scene','film','match'),show='headings',height=5,selectmode='browse')
        for key,title,width in [('scene','Scene / visual purpose',400),('film','Source film',110),('match','Score',65)]:
            self.scene_list.heading(key,text=title)
            self.scene_list.column(key,width=width,minwidth=50)
        self.scene_list.pack(side='left',fill='both',expand=True)
        scroll = ttk.Scrollbar(list_frame,command=self.scene_list.yview)
        scroll.pack(side='right',fill='y')
        self.scene_list.configure(yscrollcommand=scroll.set)
        self.scene_list.bind('<<TreeviewSelect>>',lambda e:self.show_match())
        self.match_details = tk.StringVar(value='Match a chapter to see source passages, definitions and visual purposes.')
        details = ttk.Label(self.scenes,textvariable=self.match_details,wraplength=710,justify='left')
        details.pack(fill='x',pady=(0,7))
        details.bind('<Configure>',lambda e:details.configure(wraplength=max(150,e.width-8)))
        timing = ttk.Frame(self.scenes)
        timing.pack(fill='x')
        ttk.Label(timing,text='Moment (%)').pack(side='left')
        self.moment = tk.DoubleVar(value=75)
        ttk.Scale(timing,from_=0,to=100,variable=self.moment).pack(side='left',fill='x',expand=True,padx=6)
        ttk.Entry(timing,textvariable=self.moment,width=7).pack(side='left')
        self.overlay = tk.StringVar(value='original')
        ttk.Combobox(timing,textvariable=self.overlay,values=('original','clean','math'),state='readonly',width=10).pack(side='left',padx=5)
        buttons = ttk.Frame(self.scenes)
        buttons.pack(fill='x',pady=6)
        for title,command in [('Render & attach',self.render_selected),('3-moment sequence',lambda:self.render_selected(sequence=True)),
                              ('Plan whole book',self.plan_book),('Render book matches',self.render_all_matches)]:
            ttk.Button(buttons,text=title,command=command).pack(side='left',padx=(0,4))
        self.notice(self.scenes, 'Original overlays retain the source video’s numbers and callouts. Their model assumptions remain visible in the caption and recipe; they are not recorded build measurements.')

    def selected_match(self):
        selection = self.scene_list.selection()
        return self.matches[int(selection[0])] if selection else None

    def match_page(self, custom=False):
        self.desk.capture()
        page = self.desk.page()
        if not page:
            return
        query = self.query.get().strip() if custom else page['title']+'\n'+page['body']
        if not query:
            return
        page_id = page['id']
        def work(progress):
            from .scene_catalog import build_catalog,suggest_scenes
            catalog = self.catalog or build_catalog()
            return {'catalog':catalog,'matches':suggest_scenes(query,catalog,limit=12),'page_id':page_id,'query':query}
        self.run('match',work)

    def show_match(self):
        match = self.selected_match()
        if not match:
            return
        scene = match['scene']
        reasons = match.get('reasons',[])
        why = '\n'.join(str(v) for v in reasons[:3]) if isinstance(reasons,list) else str(reasons)
        terms = ', '.join(str(t) for t in match.get('matched_terms',[])[:12])
        self.match_details.set(f"{scene['id']} · {scene.get('stage','')}\n{scene.get('summary','')[:380]}\nMatched: {terms}\n{why[:430]}")
        self.moment.set(round(float(scene.get('progress',.75))*100,1))

    def render_selected(self, sequence=False):
        match = self.selected_match()
        if not match:
            self.desk.message.set('Choose a suggested scene first.')
            return
        self.desk.capture()
        scene, page_id = deepcopy(match['scene']),self.desk.current
        page=self.desk.page()
        text_hash=hashlib.sha256((page['title']+'\n'+page['body']).encode('utf-8')).hexdigest()
        try:
            progress_value = float(self.moment.get())/100
            if not 0 <= progress_value <= 1:
                raise ValueError()
        except (ValueError,tk.TclError):
            self.desk.message.set('Moment must be a number from 0 to 100 percent.')
            return
        overlay = self.overlay.get()
        def work(progress):
            from .scene_stills import render_scene_still
            times = [.25,.6,.85] if sequence else [progress_value]
            frames = []
            for i,p in enumerate(times,1):
                progress(f"Rendering {scene['title']} · moment {i}/{len(times)}")
                frames.append(render_scene_still(scene,self.desk.store.home/'scene-stills',progress=p,overlay=overlay))
            return {'page_id':page_id,'frames':frames,'source_text_sha256':text_hash}
        self.run('stills',work)

    def plan_book(self):
        self.desk.capture()
        book = deepcopy(self.desk.store.book)
        def work(progress):
            from .scene_catalog import build_catalog
            from .book_visuals import plan_book_scenes,save_scene_plan
            catalog = self.catalog or build_catalog()
            plan = plan_book_scenes(book,catalog)
            path = save_scene_plan(plan,self.desk.store.home/'scene-plans')
            return {'path':str(path),'plan':plan,'catalog':catalog}
        self.run('plan',work)

    def render_all_matches(self):
        self.desk.capture()
        book = deepcopy(self.desk.store.book)
        def work(progress):
            from .book_visuals import plan_book_scenes,render_book_plan,save_scene_plan
            plan = plan_book_scenes(book,self.catalog)
            save_scene_plan(plan,self.desk.store.home/'scene-plans')
            return render_book_plan(plan,self.desk.store.home/'scene-stills',progress)
        self.run('book-stills',work)

    def build_catalog_browser(self):
        row = ttk.Frame(self.lexicon)
        row.pack(fill='x')
        self.catalog_filter = tk.StringVar()
        ttk.Entry(row,textvariable=self.catalog_filter).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Load / refresh',command=self.load_catalog).pack(side='left',padx=5)
        ttk.Button(row,text='Export catalog',command=self.export_catalog).pack(side='left')
        self.catalog_filter.trace_add('write',lambda *_:self.filter_catalog())
        self.catalog_status = tk.StringVar(value='Existing nouns, categories, concepts, definitions, and their source scenes.')
        ttk.Label(self.lexicon,textvariable=self.catalog_status,wraplength=730,style='BookMeta.TLabel').pack(fill='x',pady=6)
        catalog_frame=ttk.Frame(self.lexicon)
        catalog_frame.pack(fill='both',expand=True)
        self.catalog_list = ttk.Treeview(catalog_frame,columns=('name','category','type'),show='headings',height=8)
        for key,title,width in [('name','Term / concept',350),('category','Category',170),('type','Kind',100)]:
            self.catalog_list.heading(key,text=title)
            self.catalog_list.column(key,width=width,minwidth=60)
        self.catalog_list.pack(side='left',fill='both',expand=True)
        catalog_vertical=ttk.Scrollbar(catalog_frame,command=self.catalog_list.yview)
        catalog_vertical.pack(side='right',fill='y')
        self.catalog_list.configure(yscrollcommand=catalog_vertical.set)
        catalog_scroll=ttk.Scrollbar(self.lexicon,orient='horizontal',command=self.catalog_list.xview)
        catalog_scroll.pack(fill='x')
        self.catalog_list.configure(xscrollcommand=catalog_scroll.set)
        self.catalog_list.bind('<<TreeviewSelect>>',lambda e:self.show_catalog_entry())
        self.term_text = self.desk.text_area(self.lexicon,'Segoe UI',10)
        self.term_text.configure(height=6,state='disabled')

    def load_catalog(self):
        def work(progress):
            from .scene_catalog import build_catalog
            progress('Reading current scene sources and rebuilding the noun inventory; the first load can take a minute.')
            return build_catalog(refresh=True)
        self.run('catalog',work)

    def filter_catalog(self):
        self.catalog_list.delete(*self.catalog_list.get_children())
        self.catalog_rows=[]
        if not self.catalog:
            return
        query = self.catalog_filter.get().casefold()
        for kind,items in [('term',self.catalog.get('terms',[])),('concept',self.catalog.get('concepts',[])),('noun',self.catalog.get('nouns',[]))]:
            for item in items:
                if query and query not in json.dumps(item,ensure_ascii=False).casefold():
                    continue
                i=len(self.catalog_rows)
                self.catalog_rows.append((kind,item))
                self.catalog_list.insert('', 'end', iid=str(i), values=(item.get('name',item.get('key',item.get('lemma',''))),item.get('category',item.get('domain','')),kind))
        self.catalog_status.set(f"{len(self.catalog.get('nouns',[]))} noun entries · {len(self.catalog.get('terms',[]))} terms · {len(self.catalog.get('concepts',[]))} concepts · {len(self.catalog.get('scenes',[]))} scenes")
        if self.catalog.get('warnings'):
            self.catalog_status.set(self.catalog_status.get()+f" · {len(self.catalog['warnings'])} source notes in export")

    def show_catalog_entry(self):
        selection=self.catalog_list.selection()
        if selection:
            kind,item=self.catalog_rows[int(selection[0])]
            self.term_text.configure(state='normal')
            self.term_text.delete('1.0','end')
            heading = item.get('name',item.get('lemma',item.get('key','')))
            description = item.get('definition') or item.get('explain') or item.get('example','')
            text = heading+'\n\n'+str(description)
            if item.get('claim'):
                text+='\n\nClaim: '+item['claim']
            if item.get('caveat'):
                text+='\n\nScope: '+item['caveat']
            if item.get('scene_ids'):
                text+='\n\nScenes: '+', '.join(item['scene_ids'])
            if item.get('recipe'):
                text+='\n\nVisual recipe: '+'; '.join(item['recipe'])
            text+='\n\nSource record\n'+json.dumps(item.get('source',item),indent=2,ensure_ascii=False)
            self.term_text.insert('1.0',text)
            self.term_text.configure(state='disabled')

    def export_catalog(self):
        if not self.catalog:
            self.load_catalog()
            return
        path=self.desk.store.write_export('visual-catalog','.json',json.dumps(self.catalog,indent=2,ensure_ascii=False))
        self.desk.message.set(f'Catalog exported: {path}')

    def build_publish(self):
        ttk.Label(self.publish,text='One book, three ways to read it',font=('Georgia',16)).pack(anchor='w')
        self.notice(self.publish,'Build a paginated PDF and matching page proofs. Export a silent video that holds each complete page long enough to read. Existing exports are retained.')
        row=ttk.Frame(self.publish)
        row.pack(fill='x')
        self.export_scope=tk.StringVar(value='Whole book')
        ttk.Combobox(row,textvariable=self.export_scope,state='readonly',values=('Whole book','Current chapter'),width=18).pack(side='left')
        ttk.Button(row,text='Build PDF + proofs',command=self.build_publication).pack(side='left',padx=5)
        ttk.Button(row,text='Open PDF',command=self.open_pdf).pack(side='left')
        timing=ttk.Frame(self.publish)
        timing.pack(fill='x',pady=7)
        ttk.Label(timing,text='Reading words/min').pack(side='left')
        self.wpm=tk.StringVar(value='130')
        ttk.Entry(timing,textvariable=self.wpm,width=6).pack(side='left',padx=5)
        ttk.Label(timing,text='Minimum seconds/page').pack(side='left')
        self.minimum=tk.StringVar(value='6')
        ttk.Entry(timing,textvariable=self.minimum,width=6).pack(side='left',padx=5)
        ttk.Button(timing,text='Export still readthrough',command=self.build_video).pack(side='left')
        ttk.Button(timing,text='Open video',command=self.open_video).pack(side='left',padx=4)
        self.publication_status=tk.StringVar(value='No publication yet. Build from the current manuscript above.')
        ttk.Label(self.publish,textvariable=self.publication_status,wraplength=730,style='BookMeta.TLabel').pack(fill='x',pady=4)
        navigation=ttk.Frame(self.publish)
        navigation.pack(fill='x')
        ttk.Button(navigation,text='◀ Page',command=lambda:self.show_proof(self.proof_index-1)).pack(side='left')
        ttk.Button(navigation,text='Page ▶',command=lambda:self.show_proof(self.proof_index+1)).pack(side='left',padx=5)
        self.proof_label=ttk.Label(navigation)
        self.proof_label.pack(side='left')
        self.proof=ttk.Label(self.publish,anchor='center')
        self.proof.pack(fill='both',expand=True,pady=6)

    def build_publication(self):
        self.desk.capture()
        book=deepcopy(self.desk.store.book)
        scope = self.export_scope.get()
        if scope=='Current chapter':
            book['pages']=[deepcopy(self.desk.page())]
        def work(progress):
            from .publication import export_publication
            from .book_visuals import book_fingerprint
            result=export_publication(book,self.desk.store.home,progress_callback=progress)
            result['book_sha256']=book_fingerprint(book)
            result['book_scope']=scope
            result['book_source_ids']=[page['id'] for page in book['pages']]
            return result
        self.run('publication',work)

    def open_pdf(self):
        if self.publication:
            self.desk.open_path(self.publication['pdf'])

    def open_video(self):
        if self.last_video:
            self.desk.open_path(self.last_video['video'])
        else:
            self.desk.message.set('Export a still readthrough first.')

    def publication_is_current(self):
        if not self.publication:
            return False
        from .book_visuals import book_fingerprint
        self.desk.capture()
        book=deepcopy(self.desk.store.book)
        if self.publication.get('book_scope') in ('Current chapter','Selected pages'):
            ids=self.publication.get('book_source_ids',[])
            book['pages']=[page for page in book['pages'] if page['id'] in ids]
        return book_fingerprint(book)==self.publication.get('book_sha256')

    def build_video(self):
        if not self.publication:
            self.desk.message.set('Build the PDF first. The video uses those exact page proofs.')
            return
        try:
            wpm=float(self.wpm.get()); minimum=float(self.minimum.get())
        except ValueError:
            self.desk.message.set('Reading pace and minimum time must be numbers.')
            return
        publication=deepcopy(self.publication)
        if not self.publication_is_current():
            self.publication_status.set('Exporting the existing PDF snapshot. Newer writing is included only after Build PDF + proofs.')
        def work(progress):
            from .publication import export_readthrough
            return export_readthrough(publication,words_per_minute=wpm,minimum_seconds=minimum,progress_callback=progress)
        self.run('video',work)

    def show_proof(self,index):
        if not self.publication or not self.publication.get('pages'):
            return
        pages=self.publication['pages']
        index=max(0,min(len(pages)-1,index))
        self.proof_index=index
        item=pages[index]
        try:
            from PIL import Image,ImageTk
            with Image.open(item['path']) as source:
                im=source.copy()
            height=max(220,self.proof.winfo_height()-10)
            width=max(300,self.proof.winfo_width()-10)
            im.thumbnail((min(width,740),min(height,650)))
            self.proof_images=[ImageTk.PhotoImage(im,master=self.desk)]
            self.proof.configure(image=self.proof_images[0],text='')
            self.proof_label.configure(text=f"{index+1} / {len(pages)} · {item.get('title','')[:65]}")
        except Exception as exc:
            self.proof.configure(image='',text=str(exc))

    def on_page_changed(self):
        if self.desk.tabs.select()==str(self.reader):
            self.refresh_reader()
        if self.last_query and self.last_query.get('page_id') != self.desk.current:
            self.matches=[]
            self.last_query=None
            self.scene_list.delete(*self.scene_list.get_children())
            self.match_details.set('Chapter changed. Match this chapter or a phrase to choose its illustration.')

    def tab_changed(self,_event=None):
        selected=self.desk.tabs.select()
        if selected==str(self.reader):
            self.refresh_reader()
        elif selected==str(self.publish):
            self.show_proof(self.proof_index)
            if self.publication and not self.publication_is_current():
                self.publication_status.set('Saved PDF snapshot; manuscript has changed. Build PDF + proofs to include newer writing.')

    def run(self,kind,callback):
        if self.running:
            self.desk.message.set('A media job is running; writing and reading remain available.')
            return
        self.running=True
        self.desk.message.set('Preparing book media…')
        def progress(message,*_):
            self.events.put(('progress',str(message),None))
        def worker():
            try:
                self.events.put((kind,callback(progress),None))
            except Exception as exc:
                self.events.put((kind,None,str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def poll(self):
        while True:
            try:
                kind,result,error=self.events.get_nowait()
            except queue.Empty:
                break
            if kind=='progress':
                self.desk.message.set(result)
                continue
            self.running=False
            if error:
                self.desk.message.set(f'Media job failed: {error}')
                messagebox.showerror('Book media',error,parent=self.desk)
                continue
            try:
                self.accept_result(kind,result)
            except Exception as exc:
                self.desk.message.set(f'Media result needs attention: {exc}')
                messagebox.showerror('Book media',str(exc),parent=self.desk)
        self.job_after=self.desk.after(150,self.poll)

    def accept_result(self,kind,result):
        if kind in ('catalog','match','plan'):
            self.catalog=result if kind=='catalog' else result['catalog']
            self.filter_catalog()
        if kind=='match':
            if result.get('page_id') != self.desk.current:
                self.desk.message.set('Scene search finished for the previous chapter. Match the selected chapter to continue.')
                return
            self.matches=result['matches']
            self.last_query=result
            self.scene_list.delete(*self.scene_list.get_children())
            for i,match in enumerate(self.matches):
                scene=match['scene']
                self.scene_list.insert('','end',iid=str(i),values=(scene['title'],scene['lesson_key'],round(match['score'],2)))
            if self.matches:
                self.scene_list.selection_set('0')
                self.show_match()
            self.desk.message.set(f"Found {len(self.matches)} scene suggestions. Their source passages explain each match.")
        elif kind=='catalog':
            self.desk.message.set('Visual catalog loaded from existing project sources.')
        elif kind=='plan':
            self.desk.message.set(f"Book scene plan saved: {result['path']}")
        elif kind in ('stills','book-stills'):
            from .book_visuals import attach_scene_still
            self.desk.capture()
            items=([{'page_id':result['page_id'],'result':frame,'source_text_sha256':result.get('source_text_sha256')} for frame in result['frames']]
                   if kind=='stills' else result['completed'])
            for item in items:
                key=attach_scene_still(self.desk.store,item['page_id'],item['result'],
                                       source_text_sha256=item.get('source_text_sha256'))
                if 'matching' in item:
                    self.desk.store.book['assets'][key]['scene_match']=item['matching']
            self.desk.dirty=True
            saved=self.desk.save()
            self.desk.refresh_images()
            failures=result.get('failures',[])
            if saved:
                self.desk.message.set(f"Attached {len(items)} scene stills. {len(failures)} render failures recorded." if failures else f'Attached {len(items)} scene stills with recipes and source provenance.')
            self.on_page_changed()
        elif kind=='publication':
            self.publication=result
            self.last_video=None
            folder=self.desk.store.home/'publication-index'
            folder.mkdir(parents=True,exist_ok=True)
            path=folder/(stamp()+'.json')
            path.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
            self.publication_status.set(f"PDF snapshot ready · {len(result['pages'])} physical pages · {result.get('book_scope','')}")
            self.show_proof(0)
            self.desk.message.set(f"PDF ready: {result['pdf']}")
        elif kind=='video':
            self.last_video=result
            self.desk.message.set(f"Silent still-page readthrough ready: {result['video']}")
            self.publication_status.set(f"Readthrough exported from this PDF snapshot: {Path(result['video']).name}")

    def destroyed(self,event):
        if event.widget is self.desk and self.job_after:
            self.desk.after_cancel(self.job_after)
            self.job_after=None
