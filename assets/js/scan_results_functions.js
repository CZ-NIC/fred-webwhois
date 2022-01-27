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

export { copy_to_clipboard, truncate_public_key }
