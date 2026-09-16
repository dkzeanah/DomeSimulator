import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url)), work=path.dirname(root);
const skill='C:/Users/Don/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.11814/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/Don/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const r=await finalizePresentation({workspaceDir:work,candidatePath:path.join(root,'candidate.pptx'),finalPath:path.join(work,'output','The-many-values-of-one-tree.pptx'),pythonExecutable:'C:/Users/Don/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[4,15,18].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[4,15,18],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(root,'validation.json')});
console.log(JSON.stringify(r));
