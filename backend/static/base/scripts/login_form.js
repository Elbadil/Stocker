
const loginForm = document.getElementById('login-form');

function handleLoginValidationErrors (errors) {
        const fieldErrors = errors['login'];
        const fieldErrorElement = document.getElementById(`login-errors`);
        const errorMessage = fieldErrors.join(', '); // Join error messages if multiple
        fieldErrorElement.innerHTML = errorMessage;
        fieldErrorElement.classList.add('d-block');
}

function getQueryParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

const nextPage = getQueryParameter('next');

loginForm.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent default form submission

    let formData = new FormData(loginForm);

    if (nextPage) {
        formData.append('next', nextPage);
    }

    fetch("/login/", {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        // Checking if there are backend fields validation errors
        if (data.success) {
            console.log(`Success: ${data.message}`);
            window.location.href = data.redirect_url;
        } else {
            console.log(`Error: Validation Errors from Django Form`);
            // Displays backend fields validation errors
            handleLoginValidationErrors(data.errors);
        }
    })
    .catch(error => console.error('Error:', error));
});
