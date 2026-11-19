const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const providers = {};
const monaco = {Range:class {constructor(...args){this.args=args;}},languages:{CompletionItemKind:{Method:1,Variable:2,Class:3,Snippet:4},CompletionItemInsertTextRule:{InsertAsSnippet:4},registerCompletionItemProvider(language,provider){providers[language]=provider;},registerSignatureHelpProvider(){},registerHoverProvider(){}}};
const scope={};vm.createContext(scope);vm.runInContext(fs.readFileSync('static/editor_assistance.js','utf8'),scope);
scope.registerEditorAssistance(monaco,{java:{suggestions:[]},python:{suggestions:[]},cpp:{suggestions:[]}});
function model(text){return {getValue:()=>text,getLinesContent:()=>text.split('\n'),getLineContent:n=>text.split('\n')[n-1],getLineCount:()=>text.split('\n').length,getLineMaxColumn:n=>text.split('\n')[n-1].length+1,getWordUntilPosition:position=>({startColumn:position.column-(text.split('\n')[position.lineNumber-1].slice(0,position.column-1).match(/\w+$/)?.[0].length||0),endColumn:position.column})};}
const list = providers.java.provideCompletionItems(model('class Main {\n Li\n}'),{lineNumber:2,column:4}).suggestions.find(s=>s.label==='List');
assert.equal(list.insertText,'List');assert.equal(list.additionalTextEdits[0].text,'import java.util.List;\n');
assert.equal(providers.java.provideCompletionItems(model('import java.util.List;\nLi'),{lineNumber:2,column:3}).suggestions.find(s=>s.label==='List').additionalTextEdits.length,0);
assert(providers.python.provideCompletionItems(model('math.'),{lineNumber:1,column:6}).suggestions.some(s=>s.label==='sqrt'));
assert(providers.cpp.provideCompletionItems(model('vec'),{lineNumber:1,column:4}).suggestions.find(s=>s.label==='vector').additionalTextEdits[0].text.includes('#include <vector>'));
const storage=new Map();const sizing={localStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value)},matchMedia:()=>({matches:false})};vm.createContext(sizing);
const source=fs.readFileSync('static/assessment.js','utf8');vm.runInContext(source.slice(source.indexOf('function splitter('),source.indexOf('function buildQuestion(')),sizing);
function handle(){const attrs=new Map([['aria-label','Resize stimulus and response']]);return {attrs,events:{},getAttribute:key=>attrs.get(key),setAttribute:(key,value)=>attrs.set(key,value),addEventListener(type,callback){this.events[type]=callback;}};}
let width;let first=handle();sizing.splitter(first,()=>.6,value=>width=value);first.events.keydown({key:'ArrowRight',preventDefault(){}});const saved=width;let second=handle();sizing.splitter(second,()=>.3,value=>width=value);assert.equal(width,saved);
console.log('Editor auto-imports, member completions, and shared pane sizing passed.');

const scoring={assessment:{questions:[{id:'q',response_config:{score_max:5}}],score_visibility:{score_format:'fraction'}},state:{score:{q:{earned:7,maximum:10}}}};
vm.createContext(scoring);vm.runInContext(source.slice(source.indexOf('function formatScore('),source.indexOf('function updateScore(')),scoring);assert.equal(scoring.formatScore(),'7/10');
scoring.state.score._assessment={earned:70,maximum:100};scoring.assessment.score_visibility.score_format='percent';assert.equal(scoring.formatScore(),'70%');
