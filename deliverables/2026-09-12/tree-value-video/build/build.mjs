import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import sharp from 'sharp';
const root=path.dirname(fileURLToPath(import.meta.url));
const work=path.dirname(root), output=path.join(work,'output');
const skill='C:/Users/Don/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.11814/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/Don/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const scenes=JSON.parse(await fs.readFile(path.join(root,'scenes.json'),'utf8'));
const repo='C:/Users/Don/Desktop/DomeSim';
const art=repo+'/two_trees_codex/workspace/expanded-art/tools-20260912T064848369517Z-cc4b2b/';
const imgs={forest:path.join(root,'forest.png'),frame:art+'forge-double-frame.png',jig:art+'forge-jig-loaded.png',shell:art+'forge-split-log-shell.png',wedges:repo+'/two_trees_codex/workspace/expanded-art/video-20260912T103813587203Z-f337b60b/01-why-wedges-no-sawmill-v2-000333.000s.png'};
await sharp(imgs.wedges).extract({left:740,top:315,width:550,height:315}).png().toFile(path.join(root,'wedge-crop.png'));
imgs.wedges=path.join(root,'wedge-crop.png');
const p=Presentation.create({slideSize:{width:1280,height:720}});
const C={bg:'#080D10',white:'#F3F0E7',muted:'#BAC6C4',gold:'#EAC184',green:'#9ED0B5'};
function text(s,txt,x,y,w,h,size=32,color=C.white,bold=false){
 const el=s.shapes.add({geometry:'textbox',name:txt.slice(0,55),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 el.text=txt;el.text.style={typeface:'Arial',fontSize:size,color,bold,wrap:'none',autoFit:'none',insets:{left:0,right:0,top:0,bottom:0}};return el;
}
async function image(s,key,x,y,w,h,fit='contain'){
 s.images.add({blob:new Uint8Array(await fs.readFile(imgs[key])),contentType:'image/png',alt:key==='forest'?'Generated conceptual southern pine woodland':`Existing DomeSim ${key} illustration`,position:{left:x,top:y,width:w,height:h},fit});
}
function wrapped(str,max){
 return String(str).split('\n').map(line=>{let out=[],cur='';for(const word of line.split(' ')){if((cur+' '+word).trim().length>max&&cur){out.push(cur);cur=word;}else cur+=(cur?' ':'')+word;}out.push(cur);return out.join('\n')}).join('\n');
}
for(let i=0;i<scenes.length;i++){
 const c=scenes[i],s=p.slides.add();s.background.fill=C.bg;
 if(['cover','closing'].includes(c.layout)){
  await image(s,'forest',0,0,1280,720,'cover');
  // A flat translucent backdrop keeps the source photograph visible and the title legible.
  s.shapes.add({geometry:'rect',position:{left:0,top:0,width:860,height:720},fill:'#07100DDD',line:{fill:'none',width:0}});
  text(s,c.title,64,145,790,195,c.layout==='cover'?70:52,C.white,true);
  text(s,c.body.join('\n\n'),68,380,740,225,c.layout==='cover'?30:28,C.gold);
 }else{
  text(s,c.title,64,50,1150,84,46,C.white,true);
  if(c.layout==='table'){
   const vals=c.body,cols=vals[0].length;
   const t=s.tables.add({rows:vals.length,columns:cols,left:64,top:163,width:1152,height:vals.length*58,values:vals,columnWidths:cols===3?[430,278,444]:[700,452]});
   t.borders.assign({fill:'#243531',width:0.65});
   t.cells.block({row:0,column:0,rowCount:vals.length,columnCount:cols}).assign({fill:C.bg,textStyle:{typeface:'Arial',fontSize:25,color:C.white},margins:{left:12,right:8,top:10,bottom:8},anchor:'center'});
   t.cells.block({row:0,column:0,rowCount:1,columnCount:cols}).assign({fill:'#152A23',textStyle:{typeface:'Arial',fontSize:24,bold:true,color:C.green}});
   for(let r=1;r<vals.length;r++)t.getCell(r,cols===3?1:1).text.style={typeface:'Arial',fontSize:25,color:C.gold,bold:true};
  }else if(c.layout==='numbers'){
   c.body.forEach((row,j)=>{let y=163+j*135;text(s,row[0],68,y,1120,73,60,C.gold,true);text(s,row[1],71,y+76,1100,46,27,C.muted);});
  }else if(c.layout==='equation'){
   c.body.forEach((line,j)=>text(s,wrapped(line,58),68,175+j*135,1140,103,j===0?50:40,j===1?C.gold:C.white,j<2));
  }else if(c.layout==='compare'){
   c.body.forEach((row,j)=>{let y=175+j*205;text(s,row[0],68,y,1140,92,76,C.gold,true);text(s,wrapped(row[1],67),72,y+104,1120,82,31,C.white);});
  }else if(c.layout==='image'){
   await image(s,c.image,585,152,635,430);
   c.body.forEach((line,j)=>text(s,wrapped(line,29),68,177+j*137,490,122,30,j===0?C.gold:C.white,j===0));
  }else if(c.layout==='paths'){
   c.body.forEach((row,j)=>{let y=162+j*220;text(s,row[0],68,y,1100,50,32,C.gold,true);text(s,row[1].replaceAll(' · ','   /   '),68,y+62,1130,125,34,C.white);});
  }else if(c.layout==='list'){
   c.body.forEach((line,j)=>text(s,wrapped(line,64),68,160+j*(c.body.length===5?87:109),1130,100,32,j%2===0?C.white:C.green));
  }else if(c.layout==='quote'){
   text(s,c.body[0],68,201,1130,310,i===24?45:61,C.gold,true);
  }else if(c.layout==='formula'){
   c.body.forEach((line,j)=>text(s,line,68,175+j*94,1130,77,42,j===3?C.gold:C.white,j===3));
  }
  if(c.note)text(s,wrapped(c.note,114),68,626,1090,66,18,C.muted);
  text(s,String(i+1).padStart(2,'0'),1193,667,45,28,18,C.muted);
 }
 s.speakerNotes.textFrame.setText(c.narration+'\n\nOn-screen qualification: '+c.note+'\n\nSources: '+c.source+(c.image?'\nIllustration: '+imgs[c.image]:'')+(['cover','closing'].includes(c.layout)?'\nForest background: built-in ImageGen conceptual illustration, generated for this presentation.':''));
}
await fs.mkdir(path.join(root,'slides'),{recursive:true});
await (await PresentationFile.exportPptx(p)).save(path.join(root,'candidate.pptx'));
for(let i=0;i<p.slides.items.length;i++){
 if(process.env.RENDER_SLIDE&&i+1!==Number(process.env.RENDER_SLIDE))continue;
 const s=p.slides.items[i];
 const png=await p.export({slide:s,format:'png',scale:1.5});
 await fs.writeFile(path.join(root,'slides',`${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
 console.log(`Rendered ${i+1}/${scenes.length}`);
}
await finalizePresentation({workspaceDir:work,candidatePath:path.join(root,'candidate.pptx'),finalPath:path.join(output,'The-many-values-of-one-tree-final.pptx'),pythonExecutable:'C:/Users/Don/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[4,15,18].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[4,15,18],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(root,'validation-final.json')});
console.log('Finalized deck');
