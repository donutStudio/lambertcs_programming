// End-to-end reference windows and passcode regression checks.
// Requires Playwright; set PLAYWRIGHT_MODULE to an existing package path if needed.
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const serverSource = String.raw`
import logging, tempfile
from pathlib import Path
from club import create_app
from club.references import normalize_references
from club import routes
from werkzeug.serving import make_server
logging.getLogger('werkzeug').setLevel(logging.ERROR)
temp = tempfile.TemporaryDirectory()
content = '# Fixture reference\n\n' + '\n\n'.join(
    '## Topic ' + str(i) + '\n\n' + ('UniqueNeedle $x^2$.\n\n' if i == 25 else '') +
    '\n\n'.join('Line ' + str(j) + ' of the document section.' for j in range(15))
    for i in range(35))
items = []
for key, passcode in [('demo', ''), ('locked', 'fixture-password'), ('disabled', '')]:
    item = dict(id=key, title='Reference test', questions=[], stimuli={},
        time_limit_seconds=0, number_of_attempts=0, passcode=passcode,
        score_visibility={}, reference_sheets={'notes': {'name': 'Exam notes', 'content': content}},
        allowed_reference_sheets=[] if key == 'disabled' else ['py_reference', 'java_reference', 'cpp_reference', 'notes'])
    normalize_references(item)
    items.append(item)
routes.parser.load_all = lambda: items
app = create_app({'TESTING': True, 'SECRET_KEY': 'browser-test',
    'APP_URL_PREFIX': '/club/tryouts', 'ATTEMPT_DATABASE': Path(temp.name)/'attempts.sqlite3'})
server = make_server('127.0.0.1', 0, app, threaded=True)
print('http://127.0.0.1:' + str(server.server_port) + '/club/tryouts', flush=True)
server.serve_forever()
`;

async function main() {
    const root = path.join(__dirname, '..');
    const python = process.env.PYTHON || path.join(root, '.venv', 'Scripts', 'python.exe');
    const server = spawn(python, ['-u', '-c', serverSource], {cwd: root, windowsHide: true});
    let stderr = '';
    server.stderr.on('data', data => { stderr = (stderr + data).slice(-6000); });
    let browser;
    try {
        const base = await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => reject(new Error('Fixture server did not start: '+stderr)), 15000);
            server.once('exit', code => { clearTimeout(timeout); reject(new Error(`Server exited (${code}): ${stderr}`)); });
            server.stdout.once('data', data => { clearTimeout(timeout); resolve(String(data).trim()); });
        });
        browser = await chromium.launch({headless: true});
        const page = await browser.newPage({viewport: {width: 1280, height: 900}});
        const errors = [], requests = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('request', request => { if (request.url().includes('/references/')) requests.push(request.url()); });
        // Monaco is irrelevant to this fixture; retain the real KaTeX CDN scripts.
        await page.route('**/vs/loader.js', route => route.fulfill({body: '', contentType: 'text/javascript'}));
        await page.goto(base+'/assessment/demo');
        await page.waitForTimeout(300);
        assert.equal(requests.length, 0, 'References should not load before opening');
        await page.getByRole('button', {name: 'Reference ▾'}).click();
        await page.locator('#reference-menu').getByRole('button', {name: 'Python', exact: true}).click();
        const pythonWindow = page.getByRole('dialog', {name: 'Python reference', exact: true});
        await pythonWindow.getByRole('heading', {name: 'Python reference', exact: true}).waitFor();
        assert.equal(await page.locator('#reference-menu').isVisible(), false);
        assert(requests.some(url => url.includes('section=')));
        assert(await pythonWindow.locator('.reference-section pre').count() < 8, 'Only nearby body sections should load');
        await page.getByRole('button', {name: 'Reference ▾'}).click();
        await page.locator('#reference-menu').getByRole('button', {name: 'Python', exact: true}).click();
        assert.equal(await page.locator('.reference-window').count(), 1, 'Reopening should focus the existing window');
        await page.getByRole('button', {name: 'Reference ▾'}).click();
        await page.locator('#reference-menu').getByRole('button', {name: 'Java', exact: true}).click();
        const javaWindow = page.getByRole('dialog', {name: 'Java reference', exact: true});
        await javaWindow.getByRole('heading', {name: 'Java reference', exact: true}).waitFor();
        assert.equal(await page.locator('.reference-window').count(), 2, 'Different sheets can remain open together');
        await javaWindow.getByRole('button', {name: 'Close reference'}).click();

        const original = await pythonWindow.boundingBox();
        const bar = await pythonWindow.locator('.reference-title').boundingBox();
        await page.mouse.move(bar.x+15, bar.y+10); await page.mouse.down();
        await page.mouse.move(bar.x+115, bar.y+65, {steps: 5}); await page.mouse.up();
        const moved = await pythonWindow.boundingBox();
        assert(moved.x > original.x+80 && moved.y > original.y+40);
        const handle = await pythonWindow.locator('.reference-resize').boundingBox();
        await page.mouse.move(handle.x+6, handle.y+6); await page.mouse.down();
        await page.mouse.move(handle.x+56, handle.y+46, {steps: 5}); await page.mouse.up();
        const resized = await pythonWindow.boundingBox();
        assert(resized.width > moved.width+30 && resized.height > moved.height+20);
        await pythonWindow.locator('.reference-titlebar').focus();
        await page.keyboard.press('ArrowLeft');
        assert.equal((await pythonWindow.boundingBox()).x, resized.x-10);
        await pythonWindow.locator('.reference-resize').focus();
        await page.keyboard.press('ArrowLeft');
        assert.equal((await pythonWindow.boundingBox()).width, resized.width-10);
        await pythonWindow.getByRole('button', {name: 'Close reference'}).click();
        assert.equal(await page.locator('.reference-window').count(), 0);

        await page.getByRole('button', {name: 'Reference ▾'}).click();
        await page.locator('#reference-menu').getByRole('button', {name: 'Exam notes', exact: true}).click();
        const notes = page.getByRole('dialog', {name: 'Exam notes reference', exact: true});
        await notes.getByRole('heading', {name: 'Fixture reference'}).waitFor();
        assert.equal(await notes.getByText('UniqueNeedle', {exact: false}).count(), 0);
        await notes.getByRole('searchbox').fill('uniqueneedle');
        const result = notes.locator('.reference-result');
        await result.waitFor();
        await result.click();
        await notes.locator('mark').filter({hasText: 'UniqueNeedle'}).waitFor();
        await page.waitForTimeout(300);
        assert.equal(await notes.getByRole('heading', {name: 'Fixture reference'}).count(), 0, 'Distant content must be released');
        assert(await notes.locator('.reference-section').filter({has: page.locator('p')}).count() < 8);
        // Real KaTeX should render the custom sheet math if the CDN is reachable.
        const katexAvailable = await page.evaluate(() => Boolean(window.katex));
        if (katexAvailable) assert(await notes.locator('.katex').count() > 0);
        await notes.getByRole('searchbox').fill('[.*');
        await page.waitForFunction(() => document.querySelector('.reference-status').textContent === 'No matches.');
        await notes.getByRole('searchbox').fill('');
        assert.equal(await notes.locator('.reference-results').isVisible(), false);
        await page.setViewportSize({width: 390, height: 700});
        const mobile = await notes.boundingBox();
        assert(mobile.x >= 0 && mobile.x+mobile.width <= 391);
        assert(mobile.y >= 0 && mobile.y+mobile.height <= 701);
        await notes.press('Escape');
        assert.equal(await page.locator('.reference-window').count(), 0);

        await page.setViewportSize({width: 1280, height: 900});
        for (const name of ['Java', 'C++']) {
            await page.getByRole('button', {name: 'Reference ▾'}).click();
            await page.locator('#reference-menu').getByRole('button', {name, exact: true}).click();
            const frame = page.getByRole('dialog', {name: `${name} reference`, exact: true});
            await frame.getByRole('heading', {name: `${name} reference`, exact: true}).waitFor();
            if (process.env.REFERENCE_SCREENSHOT && name === 'C++') await page.screenshot({path: process.env.REFERENCE_SCREENSHOT});
            await frame.getByRole('button', {name: 'Close reference'}).click();
        }
        await page.goto(base+'/assessment/disabled');
        assert.equal(await page.locator('#reference-toggle').count(), 0);

        // Incorrect -> prompt again -> correct -> usable assessment.
        let prompts = 0;
        const retryHandler = async dialog => {
            prompts++;
            if (prompts === 1) await dialog.accept('wrong');
            else { assert(dialog.message().includes('Incorrect passcode')); await dialog.accept('fixture-password'); }
        };
        page.on('dialog', retryHandler);
        await page.goto(base+'/assessment/locked');
        await page.waitForFunction(() => document.getElementById('save-status').textContent === 'Saved');
        assert.equal(prompts, 2);
        page.off('dialog', retryHandler);
        // Dismissing immediately or after a wrong password must navigate home.
        for (let i = 0; i < 2; i++) {
            const context = await browser.newContext(); const cancelPage = await context.newPage();
            let count = 0;
            cancelPage.on('dialog', dialog => (++count === 1 && i === 1) ? dialog.accept('wrong') : dialog.dismiss());
            await cancelPage.goto(base+'/assessment/locked');
            await cancelPage.waitForURL(base+'/');
            assert.equal(await cancelPage.locator('.assessment-list').count(), 1);
            await context.close();
        }
        assert.deepEqual(errors, []);
        console.log('Browser checks passed: lazy delivery/release, literal search/jump, '+
            'window drag/resize/focus/close, three built-ins, disabled references, '+
            `mobile layout, passcode retry/cancel. KaTeX CDN: ${katexAvailable ? 'verified' : 'unavailable'}.`);
    } finally {
        if (browser) await browser.close();
        server.kill();
    }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
