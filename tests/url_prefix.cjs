// Run actual frontend handlers with a small DOM stub to verify public URLs.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const staticDir = path.join(__dirname, '..', 'static');

async function check(prefix) {
    const requests = [], beacons = [], nodes = new Map();
    const config = {baseUrl: prefix, homeUrl: prefix + '/', monacoBase: 'https://example.com/',
        assessment: {questions: [], score_visibility: {}, auto_submit_on_leave: false}};
    const document = {
        getElementById(id) {
            if (!nodes.has(id)) nodes.set(id, {textContent: id === 'assessment-config' ? JSON.stringify(config) : ''});
            return nodes.get(id);
        },
        addEventListener() {},
    };
    const context = vm.createContext({document, window: {addEventListener() {}}, location: {},
        navigator: {sendBeacon(url) { beacons.push(url); }}, Blob, structuredClone, clearTimeout,
        fetch: async url => { requests.push(url); return {ok: true, json: async () => ({
            server_time: Date.now()/1000, attempt: {score: {}, submitted: null},
        })}; },
    });
    const source = fs.readFileSync(path.join(staticDir, 'assessment.js'), 'utf8');
    vm.runInContext(source.replace(/initialize\(\);\s*$/, ''), context);
    await vm.runInContext("state.id = 'attempt-id'; persist();", context);
    vm.runInContext('beaconSave();', context);
    assert.deepEqual(requests, [prefix + '/api/attempt/attempt-id']);
    assert.deepEqual(beacons, [prefix + '/api/attempt/attempt-id']);
    nodes.get('complete-home').onclick();
    assert.equal(context.location.href, prefix + '/');
    await nodes.get('exit-assessment').onclick({preventDefault() {}});
    assert.equal(context.location.href, prefix + '/');

    const homeRequests = [], events = {};
    const homeContext = vm.createContext({
        document: {getElementById: id => id === 'credentials-form' ? null : ({textContent: JSON.stringify({assignmentsUrl: prefix + '/api/assignments'})}),
            querySelectorAll: () => []},
        window: {addEventListener(name, handler) { events[name] = handler; }},
        fetch: async url => { homeRequests.push(url); return {ok: true, json: async () => ({})}; },
    });
    vm.runInContext(fs.readFileSync(path.join(staticDir, 'home.js'), 'utf8'), homeContext);
    await events.pageshow();
    assert.deepEqual(homeRequests, [prefix + '/api/assignments']);
}

(async () => {
    for (const prefix of ['/tryouts', '/club/tryouts', '']) await check(prefix);
    console.log('Frontend requests, autosave beacons, and navigation passed for all three mounts.');
})().catch(error => { console.error(error); process.exitCode = 1; });
