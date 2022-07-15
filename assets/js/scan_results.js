/* global gettext */

const copy_to_clipboard = async e => {
    const button = e.target
    const { public_key } = button.dataset
    try {
        await navigator.clipboard.writeText(public_key)
    } catch (error) {
        throw new TypeError(error)
    }

    button.innerText = gettext('Copied')
    setTimeout(() => { button.innerText = gettext('Copy'), 2000 })
}

const truncate_public_key = public_key => {
    const length = public_key.length

    // Don't truncate if the key is short
    if (length <= 20) return public_key

    const beginning = public_key.substring(0, 10)
    const ending = public_key.substring(length - 10, length)

    return `${beginning}...${ending}`
}

const view_key = e => {
    const public_key = e.target.parentElement.parentElement.querySelector('.public-key')
    const public_key_full = e.target.parentElement.parentElement.querySelector('.public-key-full')

    if (public_key_full.classList.contains('d-none')) {
        public_key_full.classList.remove('d-none')
        public_key.classList.add('d-none')
        e.target.textContent = gettext('Hide')
    } else {
        public_key_full.classList.add('d-none')
        public_key.classList.remove('d-none')
        e.target.textContent = gettext('View')
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const public_keys = document.querySelectorAll('.public-key')
    const copy_buttons = document.querySelectorAll('.public-key-copy')
    const view_buttons = document.querySelectorAll('.public-key-view')

    for (const public_key of public_keys) {
        public_key.innerText = truncate_public_key(public_key.innerHTML)
    }

    for (const copy_button of copy_buttons) {
        copy_button.addEventListener('click', copy_to_clipboard)
    }

    for (const view_button of view_buttons) {
        view_button.parentElement.parentElement.insertAdjacentHTML('afterbegin',
            `<p class="public-key-full d-none">${view_button.dataset.text}</p>`)
        view_button.addEventListener('click', view_key)
    }
})
