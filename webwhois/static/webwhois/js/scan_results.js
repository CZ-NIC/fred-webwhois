import { copy_to_clipboard, truncate_public_key } from './scan_results_functions.js'

document.addEventListener('DOMContentLoaded', () => {
    const public_keys = document.querySelectorAll('.public-key')
    const copy_buttons = document.querySelectorAll('.public-key-copy')
    for(const public_key of public_keys) {
        public_key.innerText = truncate_public_key(public_key.innerText)
    }

    for(const copy_button of copy_buttons) {
        copy_button.addEventListener('click', copy_to_clipboard)
    }
})
