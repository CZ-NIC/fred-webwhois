/* eslint-env jest */
import '../webwhois'

// Globally mock gettext
global.gettext = jest.fn((text) => text);

const LOAD_NODE = `
    <form class="webwhois-public-request">
        <input name="handle" required="">
        <input name="send_to_0" value="email_in_registry" checked required>
        <input name="send_to_0" value="custom_email" required>
        <input  name="send_to_1">
        <select name="confirmation_method">
            <option value="signed_email">Email signed by a qualified certificate</option>
        </select>
    </form>
`

const LOAD_NODE_REGISTRY = `
    <form class="webwhois-public-request">
        <input name="handle" required="" class="required">
        <input name="send_to_0" value="email_in_registry" checked required>
        <input name="send_to_0" value="custom_email" checked>
        <input name="send_to_1" disabled>
        <select name="confirmation_method">
            <option value="signed_email">Email signed by a qualified certificate</option>
        </select>
    </form>
`
const LOAD_NODE_SUBMIT = `
    <form class="webwhois-public-request">
        <div class="errorlist">This field is required.</div>
        <input name="handle" class="required" value="test">
        <input name="handle" class="required" value="">
        <select name="confirmation_method"></select>
    </form>
`

describe('webwhois', () => {
    test('Load page', () => {
        document.dispatchEvent(new Event('DOMContentLoaded'))
        expect(document.body).toMatchSnapshot()
    })

    test('Event listeners click to email_in_registry', () => {
        document.body.innerHTML = LOAD_NODE
        document.dispatchEvent(new Event('DOMContentLoaded'))
        document.querySelector('input[value=email_in_registry]').dispatchEvent(new Event('click'))
    })

    test('Event listeners click to custom_email', () => {
        document.body.innerHTML = LOAD_NODE_REGISTRY
        document.dispatchEvent(new Event('DOMContentLoaded'))
        document.querySelector('input[value=custom_email]').dispatchEvent(new Event('click'))
    })

    test('Event listeners submit', () => {
        document.body.innerHTML = LOAD_NODE_SUBMIT
        document.dispatchEvent(new Event('DOMContentLoaded'))
        document.querySelector('.webwhois-public-request').dispatchEvent(new Event('submit'))
    })
})
