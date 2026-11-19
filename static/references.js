/* Independent reference windows. Bodies are fetched only near the viewport;
   offscreen sections and closed windows retain no document content. */
(() => {
    const config = JSON.parse(document.getElementById('assessment-config').textContent);
    const sheets = config.assessment.references || [];
    const toggle = document.getElementById('reference-toggle');
    if (!toggle || !sheets.length) return;
    const menu = document.getElementById('reference-menu');
    const windows = new Map();
    let topWindow = 20;
    const node = (tag, className, text) => {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (text !== undefined) element.textContent = text;
        return element;
    };
    function showMenu(show) {
        menu.hidden = !show; toggle.setAttribute('aria-expanded', String(show));
    }
    toggle.onclick = () => showMenu(menu.hidden);
    document.addEventListener('pointerdown', event => {
        if (!event.target.closest('.reference-picker')) showMenu(false);
    });
    toggle.addEventListener('keydown', event => {
        if (event.key === 'ArrowDown') { event.preventDefault(); showMenu(true); menu.firstElementChild.focus(); }
    });
    menu.addEventListener('keydown', event => {
        const buttons = [...menu.children];
        const index = buttons.indexOf(document.activeElement);
        if (event.key === 'Escape') { showMenu(false); toggle.focus(); }
        if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
            event.preventDefault();
            const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 :
                (index + (event.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length;
            buttons[next].focus();
        }
    });
    for (const sheet of sheets) {
        const button = node('button', '', sheet.name);
        button.onclick = () => { showMenu(false); openSheet(sheet); };
        menu.append(button);
    }

    async function openSheet(sheet) {
        if (windows.has(sheet.id)) { windows.get(sheet.id).focus(); return; }
        const frame = node('section', 'reference-window');
        frame.setAttribute('role', 'dialog'); frame.setAttribute('aria-label', `${sheet.name} reference`);
        frame.tabIndex = -1;
        const titlebar = node('div', 'reference-titlebar'); titlebar.tabIndex = 0;
        titlebar.setAttribute('aria-label', 'Move reference window (arrow keys)');
        const title = node('strong', 'reference-title', sheet.name);
        const search = node('input', 'reference-search'); search.type = 'search';
        search.placeholder = 'Search reference…'; search.maxLength = 200;
        search.setAttribute('aria-label', `Search ${sheet.name} reference`);
        const close = node('button', 'reference-close', '×'); close.setAttribute('aria-label', 'Close reference');
        titlebar.append(title, search, close);
        const status = node('div', 'reference-status', 'Loading reference…');
        status.setAttribute('role', 'status');
        const results = node('div', 'reference-results'); results.hidden = true;
        results.setAttribute('aria-label', 'Search results');
        const documentPane = node('div', 'reference-document'); documentPane.tabIndex = 0;
        documentPane.setAttribute('aria-label', `${sheet.name} document`);
        const resize = node('button', 'reference-resize', '◢');
        resize.setAttribute('aria-label', 'Resize reference window (arrow keys)');
        frame.append(titlebar, status, results, documentPane, resize);
        const offset = windows.size * 24;
        frame.style.left = `${Math.min(70 + offset, Math.max(0, innerWidth - 380))}px`;
        frame.style.top = `${Math.min(65 + offset, Math.max(0, innerHeight - 260))}px`;
        document.body.append(frame);
        let closed = false, searchTimer, searchController, searchVersion = 0, query = '';
        const requests = new Set(), sections = [];
        const focus = () => { frame.style.zIndex = String(++topWindow); frame.focus({preventScroll: true}); };
        windows.set(sheet.id, {focus}); focus();
        frame.addEventListener('pointerdown', () => { frame.style.zIndex = String(++topWindow); });
        async function fetchData(params, signal) {
            const controller = new AbortController();
            const abort = () => controller.abort();
            if (signal?.aborted) controller.abort();
            else signal?.addEventListener('abort', abort, {once: true});
            requests.add(controller);
            try {
                const url = new URL(sheet.url, location.origin);
                Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, value));
                const response = await fetch(url, {signal: controller.signal, cache: 'no-store'});
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Could not load reference');
                return data;
            } finally { requests.delete(controller); signal?.removeEventListener('abort', abort); }
        }
        function clearHighlights(element) {
            element.querySelectorAll('mark').forEach(mark => mark.replaceWith(document.createTextNode(mark.textContent)));
            element.normalize();
        }
        function highlight(element) {
            clearHighlights(element);
            if (!query) return;
            const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {
                acceptNode: text => text.parentElement.closest('.katex, .math-expression, script, style') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
            });
            const texts = [];
            while (walker.nextNode()) texts.push(walker.currentNode);
            const pattern = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
            for (const text of texts) {
                const matches = [...text.textContent.matchAll(pattern)];
                if (!matches.length) continue;
                const fragment = document.createDocumentFragment(); let start = 0;
                for (const match of matches) {
                    fragment.append(document.createTextNode(text.textContent.slice(start, match.index)), node('mark', '', match[0]));
                    start = match.index + match[0].length;
                }
                fragment.append(document.createTextNode(text.textContent.slice(start))); text.replaceWith(fragment);
            }
        }
        async function loadSection(section, scrollToMatch = false) {
            if (!section.loaded) {
                if (!section.pending) {
                    const controller = new AbortController(); section.controller = controller;
                    section.element.textContent = 'Loading…';
                    section.pending = (async () => {
                        try {
                            const data = await fetchData({section: section.id}, controller.signal);
                            if (closed || controller.signal.aborted) return;
                            section.element.innerHTML = data.html;
                            section.element.style.minHeight = '';
                            section.loaded = true;
                            if (window.katex) section.element.querySelectorAll('.math-expression').forEach(element => {
                                katex.render(element.dataset.math, element, {displayMode: element.dataset.display === 'true', throwOnError: false, trust: false});
                            });
                        } catch (error) {
                            if (error.name !== 'AbortError' && !closed) {
                                const retry = node('button', '', 'Retry loading section');
                                retry.onclick = () => loadSection(section);
                                section.element.replaceChildren(node('p', '', error.message), retry);
                            }
                        } finally { if (section.controller === controller) section.pending = null; }
                    })();
                }
                await section.pending;
            }
            if (closed || !section.loaded) return;
            highlight(section.element);
            if (scrollToMatch) (section.element.querySelector('mark') || section.element).scrollIntoView({block: 'start'});
        }
        const observer = new IntersectionObserver(entries => {
            if (closed) return;
            for (const entry of entries) {
                const section = sections[Number(entry.target.dataset.section)];
                if (entry.isIntersecting) loadSection(section);
                else {
                    section.controller?.abort();
                    section.controller = null; section.pending = null;
                    if (section.loaded) {
                        section.element.style.minHeight = `${section.element.getBoundingClientRect().height}px`;
                        section.element.replaceChildren(); section.loaded = false;
                    }
                }
            }
        }, {root: documentPane, rootMargin: '250px 0px'});
        search.addEventListener('input', () => {
            clearTimeout(searchTimer); searchController?.abort();
            const version = ++searchVersion;
            query = search.value.trim(); results.replaceChildren(); results.hidden = !query;
            sections.filter(section => section.loaded).forEach(section => highlight(section.element));
            if (!query) { status.textContent = 'Search this reference or scroll to read.'; return; }
            status.textContent = 'Searching…';
            searchTimer = setTimeout(async () => {
                searchController = new AbortController();
                try {
                    const data = await fetchData({q: query}, searchController.signal);
                    if (closed || version !== searchVersion) return;
                    const total = data.results.reduce((sum, result) => sum + result.count, 0);
                    status.textContent = total ? `${total} matches in ${data.results.length} sections. Select a result to jump to it.` : 'No matches.';
                    for (const result of data.results) {
                        const button = node('button', 'reference-result');
                        button.append(node('strong', '', `${result.title} (${result.count})`), node('span', '', result.excerpt));
                        button.onclick = async () => {
                            const section = sections[result.section];
                            if (!section) return;
                            section.element.scrollIntoView({block: 'start'});
                            await loadSection(section, true);
                        };
                        results.append(button);
                    }
                } catch (error) {
                    if (error.name !== 'AbortError' && !closed && version === searchVersion) status.textContent = `Search failed: ${error.message}. Edit the query to retry.`;
                }
            }, 250);
        });
        const clamp = (value, min, max) => Math.max(min, Math.min(value, max));
        function constrain() {
            frame.style.width = `${Math.min(frame.offsetWidth, innerWidth)}px`;
            frame.style.height = `${Math.min(frame.offsetHeight, innerHeight)}px`;
            frame.style.left = `${clamp(frame.offsetLeft, 0, innerWidth - frame.offsetWidth)}px`;
            frame.style.top = `${clamp(frame.offsetTop, 0, innerHeight - frame.offsetHeight)}px`;
        }
        function manipulate(handle, resizing) {
            handle.addEventListener('pointerdown', event => {
                if (event.button !== 0 || (!resizing && event.target.closest('input,button,a'))) return;
                event.preventDefault(); handle.setPointerCapture(event.pointerId);
                const start = {x: event.clientX, y: event.clientY, left: frame.offsetLeft, top: frame.offsetTop,
                    width: frame.offsetWidth, height: frame.offsetHeight};
                const move = event => {
                    if (resizing) {
                        frame.style.width = `${clamp(start.width + event.clientX - start.x, Math.min(340, innerWidth), innerWidth - start.left)}px`;
                        frame.style.height = `${clamp(start.height + event.clientY - start.y, Math.min(220, innerHeight), innerHeight - start.top)}px`;
                    } else {
                        frame.style.left = `${clamp(start.left + event.clientX - start.x, 0, innerWidth - frame.offsetWidth)}px`;
                        frame.style.top = `${clamp(start.top + event.clientY - start.y, 0, innerHeight - frame.offsetHeight)}px`;
                    }
                };
                const stop = () => {
                    handle.removeEventListener('pointermove', move);
                    handle.removeEventListener('pointerup', stop); handle.removeEventListener('pointercancel', stop);
                    handle.removeEventListener('lostpointercapture', stop);
                };
                handle.addEventListener('pointermove', move); handle.addEventListener('pointerup', stop);
                handle.addEventListener('pointercancel', stop); handle.addEventListener('lostpointercapture', stop);
            });
            handle.addEventListener('keydown', event => {
                if (event.target !== handle || !['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)) return;
                event.preventDefault(); event.stopPropagation();
                const amount = (event.shiftKey ? 40 : 10) * (['ArrowLeft','ArrowUp'].includes(event.key) ? -1 : 1);
                const horizontal = ['ArrowLeft','ArrowRight'].includes(event.key);
                const property = resizing ? (horizontal ? 'width' : 'height') : (horizontal ? 'left' : 'top');
                frame.style[property] = `${parseFloat(getComputedStyle(frame)[property]) + amount}px`;
                constrain();
            });
        }
        manipulate(titlebar, false); manipulate(resize, true);
        window.addEventListener('resize', constrain);
        function dispose() {
            closed = true; clearTimeout(searchTimer); observer.disconnect();
            requests.forEach(controller => controller.abort());
            window.removeEventListener('resize', constrain);
            frame.remove(); sections.length = 0; windows.delete(sheet.id); toggle.focus();
        }
        close.onclick = dispose;
        frame.addEventListener('keydown', event => {
            // Keep editor shortcuts from navigating questions while using a reference.
            if (event.altKey && ['ArrowLeft','ArrowRight'].includes(event.key)) event.stopPropagation();
            if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); dispose(); }
        });
        try {
            const data = await fetchData({});
            if (closed) return;
            for (const descriptor of data.sections) {
                const element = node('article', 'reference-section');
                element.dataset.section = descriptor.id; element.setAttribute('aria-label', descriptor.title);
                element.style.minHeight = '300px';
                sections.push({...descriptor, element, loaded: false}); documentPane.append(element);
                observer.observe(element);
            }
            status.textContent = sections.length ? 'Search this reference or scroll to read.' : 'This reference sheet is empty.';
        } catch (error) {
            if (error.name !== 'AbortError' && !closed) {
                status.textContent = error.message;
                const retry = node('button', '', 'Retry opening reference');
                retry.onclick = () => { dispose(); openSheet(sheet); }; documentPane.append(retry);
            }
        }
    }
})();
