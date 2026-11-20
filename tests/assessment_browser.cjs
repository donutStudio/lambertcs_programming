// Real browser coverage for credentials, reset undo, navigation, and final grading.
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const serverSource = String.raw`
import json, tempfile, logging
from pathlib import Path
from club import create_app, routes
from club.assessments import AssessmentParser
from werkzeug.serving import make_server
logging.getLogger('werkzeug').setLevel(logging.ERROR)
temp = tempfile.TemporaryDirectory()
root = Path(temp.name)
manifest = {'id':'demo','title':'Browser fixture','number_of_attempts':1,
    'required_credentials':['full_name','email','student_id'],
    'questions':[{'id':key,'response_type':'code_editor','response_config':{
        'supported_languages':['python'],'intellisense':False,'runnable':False,
        'runnable_tests':False,'default_code':{'python':'print(0)'},
        'grader':{'max_score':10,'code':'def grade(ctx): ctx.check("21\\n", "42", points=10)'}}}
        for key in ['one','two']]}
(root/'assessment.json').write_text(json.dumps(manifest))
item=AssessmentParser(root).load('assessment.json')
routes.parser.load_all=lambda:[item]
app=create_app({'SECRET_KEY':'browser-test','APP_URL_PREFIX':'','ATTEMPT_DATABASE':root/'db.sqlite3'})
server=make_server('127.0.0.1',0,app,threaded=True)
print('http://127.0.0.1:'+str(server.server_port),flush=True)
server.serve_forever()
`;
(async () => {
    const root = path.join(__dirname, '..');
    const server = spawn(process.env.PYTHON || path.join(root, '.venv', 'Scripts', 'python.exe'), ['-u', '-c', serverSource], {cwd:root, windowsHide:true});
    let stderr = '', browser;
    server.stderr.on('data', data => stderr = (stderr + data).slice(-5000));
    try {
        const base = await new Promise((resolve, reject) => {
            const timer = setTimeout(() => reject(Error(stderr || 'Fixture startup timed out')), 15000);
            server.stdout.once('data', data => {clearTimeout(timer); resolve(String(data).trim());});
            server.once('exit', code => {clearTimeout(timer); reject(Error('Server exited '+code+': '+stderr));});
        });
        browser = await chromium.launch({headless:true});
        const page = await browser.newPage({viewport:{width:1280,height:900}});
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(base);
        const start = page.locator('.assessment-list .button');
        await page.waitForFunction(() => document.querySelector('.assessment-list .button').textContent === 'Start');
        assert.equal(await start.getAttribute('aria-disabled'), 'true');
        await page.locator('[name=full_name]').fill('Jane Doe');
        await page.locator('[name=email]').fill('jane@example.com');
        await page.locator('[name=student_id]').fill('12345');
        assert.equal(await start.getAttribute('aria-disabled'), 'false');
        await start.click();
        await page.waitForFunction(() => typeof editorInstances !== 'undefined' && editorInstances.length > 0, {timeout:45000});
        assert.equal(await page.locator('.test-header').innerText().then(text => text.startsWith('← Exit')), true);
        assert.equal(await page.locator('button', {hasText:/^Submit$/}).count(), 0);
        const source = 'print(int(input("Different prompt: ")) * 2)';
        await page.evaluate(code => editorInstances[0].setValue(code), source);
        page.once('dialog', dialog => dialog.dismiss());
        await page.getByRole('button', {name:'Reset', exact:true}).click();
        assert.equal(await page.evaluate(() => editorInstances[0].getValue()), source);
        page.once('dialog', dialog => dialog.accept());
        await page.getByRole('button', {name:'Reset', exact:true}).click();
        assert.equal(await page.evaluate(() => editorInstances[0].getValue()), 'print(0)');
        await page.evaluate(() => {editorInstances[0].focus();});
        await page.keyboard.press('Control+z');
        assert.equal(await page.evaluate(() => editorInstances[0].getValue()), source);
        await page.getByRole('button', {name:'Next', exact:true}).click();
        await page.waitForFunction(() => editorInstances.length > 0);
        await page.evaluate(code => editorInstances[0].setValue(code), source);
        assert.equal(await page.locator('.test-header button', {hasText:/^Submit$/}).count(), 0);
        page.once('dialog', dialog => dialog.accept());
        await page.getByRole('button', {name:'Submit', exact:true}).click();
        await page.waitForFunction(() => !document.getElementById('complete-dialog').hidden);
        await page.waitForFunction(() => document.getElementById('complete-message').textContent === 'Score: 20/20', {timeout:30000});
        await page.getByRole('button', {name:'Return to assessments'}).click();
        await page.waitForFunction(() => document.querySelector('.assessment-score').textContent === 'Score: 20/20');
        assert.deepEqual(errors, []);
        console.log('Credentials, last-question submit, reset confirmation + Ctrl+Z, automatic grading, and score list passed.');
    } finally {if (browser) await browser.close(); server.kill();}
})().catch(error => {console.error(error); process.exitCode=1;});
