/* eslint-env jest */
import '../scan_results'

// Globally mock gettext
global.gettext = jest.fn((text) => text)

const LOAD_NODE = `
    <div class="public-key-wrapper">
        <p class="public-key">abcdefghijklmnopqrstuvwxyz==</p>
        <div class="public-key-actions">
            <span class="public-key-view" data-text="abcdefghijklmnopqrstuvwxyz==">View</span>
            <button class="public-key-copy" data-public_key="abcdefghijklmnopqrstuvwxyz==">
                Copy
            </button>
        </div>
    </div>
`

const LOAD_NODE_VIEW = `
<div class="public-key-wrapper">>
    <p class="public-key-full d-none">full</p>
    <p class="public-key">short</p>
    <div><span class="public-key-view">View</span></div>
</div>
`

const LOAD_NODE_HIDE = `
<div class="public-key-wrapper">
    <p class="public-key-full">full</p>
    <p class="public-key d-none">short</p>
    <div><span class="public-key-view">Hide</span></div>
</div>
`
Object.assign(navigator, {
    clipboard: {
        writeText: () => { },
    },
})

describe('scan results', () => {
    test('Load pageb click to copy', () => {
        document.body.innerHTML = LOAD_NODE
        document.dispatchEvent(new Event('DOMContentLoaded'))
        document.querySelector('.public-key-copy').dispatchEvent(new Event('click'))
    })

    test('Event listener click to view', () => {
        document.body.innerHTML = LOAD_NODE_VIEW
        document.dispatchEvent(new Event('DOMContentLoaded'))
        document.querySelector('.public-key-view').dispatchEvent(new Event('click'))
    })

    test('Event listener click to hide', () => {
        document.body.innerHTML = LOAD_NODE_HIDE
        document.querySelector('.public-key-view').dispatchEvent(new Event('click'))
    })
})
