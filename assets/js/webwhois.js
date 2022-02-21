/* global gettext */

/*
    Webwhois and Public requests
*/

function emailInRegistry(inputCustomEmail, confirmationMethodSelect, confirmationMethodOptions) {
    inputCustomEmail.value = ''
    inputCustomEmail.disabled = true
    inputCustomEmail.classList.remove('required')
    confirmationMethodSelect.selectedIndex = confirmationMethodOptions.indexOf('signed_email')
    confirmationMethodSelect.disabled = true
}

function customEmail(inputCustomEmail, confirmationMethodSelect) {
    inputCustomEmail.disabled = false
    inputCustomEmail.classList.add('required')
    confirmationMethodSelect.disabled = false
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('form.webwhois-public-request')) {
        const form = document.querySelector('form.webwhois-public-request')
        const emailChoice = document.querySelectorAll('input[name=send_to_0]')
        const inputCustomEmail = document.querySelector('input[name=send_to_1]')
        const confirmationMethodSelect = document.querySelector('select[name=confirmation_method]')
        const confirmationMethodOptions = []

        Array.from(confirmationMethodSelect.options).forEach(option => {
            confirmationMethodOptions.push(option.value)
        })

        emailChoice.forEach(email => {
            email.addEventListener('click', (e) => {
                e.target.value === 'email_in_registry' ?
                    emailInRegistry(inputCustomEmail, confirmationMethodSelect, confirmationMethodOptions) :
                    customEmail(inputCustomEmail, confirmationMethodSelect)
            })

            if (email.checked && email.value === 'email_in_registry') {
                emailInRegistry(inputCustomEmail, confirmationMethodSelect, confirmationMethodOptions)
            } else if (email.checked) {
                customEmail(inputCustomEmail, confirmationMethodSelect)
            }
        })

        document.querySelector('input[name=handle]').classList.add('required')
        form.addEventListener('submit', (e) => {
            document.querySelectorAll('.errorlist').forEach(error => error.remove())
            document.querySelectorAll('input.required').forEach(input => {
                if (!input.value) {
                    input.insertAdjacentHTML('beforebegin', `
                    <div class='errorlist'>${gettext('This field is required.')}</div>
                `)
                    e.preventDefault()
                }
            })
        })
    }
})
