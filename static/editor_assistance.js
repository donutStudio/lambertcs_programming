/* Practical standard-library completions, auto-imports, snippets and signatures.
   This is deliberately separate from Monaco's tokenizer and compiler diagnostics. */
function registerEditorAssistance(monaco, languages) {
    const imports = {
        java: Object.fromEntries(['List','ArrayList','LinkedList','Map','HashMap','TreeMap','Set','HashSet','TreeSet','Queue','Deque','ArrayDeque','PriorityQueue','Collections','Arrays','Comparator','Scanner','Iterator','Optional','StringTokenizer','Stack','Vector','Objects','Random'].map(name => [name, `java.util.${name}`]).concat(['BufferedReader','InputStreamReader','PrintWriter','IOException'].map(name => [name, `java.io.${name}`]))),
        python: {Counter:'collections',defaultdict:'collections',deque:'collections',namedtuple:'collections',heappush:'heapq',heappop:'heapq',heapify:'heapq',bisect_left:'bisect',bisect_right:'bisect',insort:'bisect',accumulate:'itertools',combinations:'itertools',permutations:'itertools',product:'itertools',lru_cache:'functools',reduce:'functools',gcd:'math',lcm:'math',sqrt:'math',ceil:'math',floor:'math',factorial:'math'},
        cpp: {vector:'vector',string:'string',map:'map',unordered_map:'unordered_map',set:'set',unordered_set:'unordered_set',queue:'queue',priority_queue:'queue',stack:'stack',deque:'deque',sort:'algorithm',lower_bound:'algorithm',upper_bound:'algorithm',reverse:'algorithm',min:'algorithm',max:'algorithm',accumulate:'numeric',gcd:'numeric',pair:'utility',tuple:'tuple',cin:'iostream',cout:'iostream'}
    };
    const modules = ['math','sys','collections','heapq','bisect','itertools','functools','statistics','random','re','string'];
    const members = {
        java: ['add','addAll','get','set','remove','contains','size','isEmpty','clear','indexOf','subList','sort','put','getOrDefault','containsKey','keySet','values','entrySet','offer','poll','peek','push','pop','length','charAt','substring','equals','split','trim','toCharArray','nextInt','nextLong','nextLine','hasNext','println','print'],
        python: ['append','extend','insert','pop','remove','sort','reverse','count','index','clear','copy','get','keys','values','items','setdefault','update','add','discard','split','strip','join','replace','startswith','endswith','lower','upper'],
        cpp: ['push_back','pop_back','size','empty','begin','end','clear','insert','erase','find','count','front','back','top','push','pop','substr']
    };
    const signatures = {
        print: ['print(*objects, sep=" ", end="\\n")','Write objects to standard output.'],
        input: ['input(prompt="") -> str','Read one line from standard input.'],
        range: ['range(start, stop, step=1)','Generate an integer sequence; stop is excluded.'],
        len: ['len(object) -> int','Return the number of items.'],
        get: ['get(index)','Return the element at the specified index.'],
        add: ['add(element)','Append or insert an element.'],
        substring: ['substring(beginIndex, endIndex)','Return characters in the half-open range.'],
        sort: ['sort(container)','Sort elements.'],
        lower_bound: ['lower_bound(first, last, value)','Find the first element not less than value.']
    };
    function importEdit(model, language, name, module) {
        const source = model.getValue();
        let statement;
        if (language === 'java') {
            if (source.includes(`import ${module};`) || source.includes(`import ${module.slice(0,module.lastIndexOf('.'))}.*;`)) return [];
            statement = `import ${module};\n`;
        } else if (language === 'python') {
            if (new RegExp(`from ${module} import [^\\n]*\\b${name}\\b`).test(source)) return [];
            statement = modules.includes(name) ? `import ${name}\n` : `from ${module} import ${name}\n`;
            if (source.split('\n').some(line => line.trim() === statement.trim())) return [];
        } else {
            if (source.includes(`#include <${module}>`) || source.includes('#include <bits/stdc++.h>')) return [];
            statement = `#include <${module}>\n`;
        }
        let line = 1;
        model.getLinesContent().forEach((text, i) => {
            if ((language === 'java' && /^\s*(package|import)\s/.test(text)) || (language === 'python' && /^(#!|#.*coding|from __future__ import)/.test(text))) line = i + 2;
        });
        // At EOF after a package/import line without a newline, prepend one.
        if (line > model.getLineCount()) return [{range: new monaco.Range(model.getLineCount(), model.getLineMaxColumn(model.getLineCount()), model.getLineCount(), model.getLineMaxColumn(model.getLineCount())), text: '\n' + statement}];
        return [{range: new monaco.Range(line,1,line,1), text: statement}];
    }
    Object.entries(languages).forEach(([language, settings]) => {
        monaco.languages.registerCompletionItemProvider(language, {
            triggerCharacters: ['.'],
            provideCompletionItems(model, position) {
                const word = model.getWordUntilPosition(position);
                const range = new monaco.Range(position.lineNumber, word.startColumn, position.lineNumber, word.endColumn);
                const prefix = model.getLineContent(position.lineNumber).slice(0,word.startColumn-1);
                const member = prefix.endsWith('.');
                const owner = prefix.match(/([\w]+)\.$/)?.[1];
                const staticMembers = {
                    math: ['sqrt','gcd','lcm','ceil','floor','factorial','pi','inf','isqrt','pow'],
                    heapq: ['heappush','heappop','heapify','nlargest','nsmallest'],
                    itertools: ['accumulate','combinations','permutations','product','chain'],
                    collections: ['Counter','defaultdict','deque'],
                    Arrays: ['sort','binarySearch','fill','copyOf','asList','stream','equals','toString'],
                    Collections: ['sort','reverse','min','max','binarySearch','frequency'],
                    Math: ['sqrt','pow','abs','min','max','floor','ceil','round','PI']
                };
                const names = new Set(member ? (staticMembers[owner] || members[language]) : [...settings.suggestions, ...(model.getValue().match(/\b[A-Za-z_]\w*\b/g)||[])]);
                const suggestions = [...names].filter(name => member || !(name in imports[language])).map(name => ({label:name,insertText:name,range,kind:member?monaco.languages.CompletionItemKind.Method:monaco.languages.CompletionItemKind.Variable,sortText:'2'+name}));
                if (!member) {
                    Object.entries(imports[language]).concat(language === 'python' ? modules.map(m=>[m,m]) : []).forEach(([name,module]) => {
                        const insertText = language === 'cpp' && !model.getValue().includes('using namespace std;') && !prefix.endsWith('std::') ? `std::${name}` : name;
                        suggestions.push({label:name,insertText,range,kind:monaco.languages.CompletionItemKind.Class,detail:language==='java'?module:`${module} — standard library`,documentation:`Use ${name} from ${module}. Adds the import/include if needed.`,additionalTextEdits:importEdit(model,language,name,module),sortText:'0'+name});
                    });
                    const snippets = language === 'python' ? {for:'for ${1:item} in ${2:items}:\n\t$0',if:'if ${1:condition}:\n\t$0',def:'def ${1:name}(${2:args}):\n\t$0'} : language === 'java' ? {for:'for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n\t$0\n}',sout:'System.out.println(${1:value});',main:'public static void main(String[] args) {\n\t$0\n}'} : {for:'for (int ${1:i} = 0; ${1:i} < ${2:n}; ++${1:i}) {\n\t$0\n}'};
                    Object.entries(snippets).forEach(([name,text])=>suggestions.push({label:name,insertText:text,insertTextRules:monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,kind:monaco.languages.CompletionItemKind.Snippet,range,detail:'Code snippet'}));
                }
                return {suggestions};
            }
        });
        monaco.languages.registerSignatureHelpProvider(language, {signatureHelpTriggerCharacters:['(',','],provideSignatureHelp(model,position) {
            const match=model.getLineContent(position.lineNumber).slice(0,position.column-1).match(/(\w+)\(([^()]*)$/);
            const signature=match&&signatures[match[1]];
            if(!signature)return null;
            return {value:{signatures:[{label:signature[0],documentation:signature[1],parameters:[]}],activeSignature:0,activeParameter:0},dispose(){}};
        }});
        monaco.languages.registerHoverProvider(language,{provideHover(model,position){const word=model.getWordAtPosition(position)?.word;const module=imports[language][word];if(!module)return null;return {contents:[{value:`**${word}** — standard library`},{value:language==='java'?`Import: \`${module}\``:`Module/header: \`${module}\``}]};}});
    });
}
