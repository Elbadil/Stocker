const registerForm = document.getElementById('register-form');

function handleValidationErrors (errors, fields) {
    console.log('Handling Errors');
    fields.forEach(field => {
        const fieldErrors = errors[field];
        const fieldErrorElement = document.getElementById(`${field}-errors`);

        if (fieldErrors && fieldErrors.length > 0) {
            const errorMessage = fieldErrors.join(', '); // Join error messages if multiple
            fieldErrorElement.innerHTML = errorMessage;
            fieldErrorElement.classList.add('d-block');
        } else {
            fieldErrorElement.innerHTML = '';
            fieldErrorElement.classList.remove('d-block');
        }
    });
}

registerForm.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent default form submission

    let formData = new FormData(registerForm);

    fetch("/signup/", {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        // Checking if there are backend fields validation errors
        if (data.success) {
            console.log(`Success: ${data.message}`);
            window.location.href = '/confirm-account/';
        } else {
            console.log(`Error: Validation Errors from Django Form`);
            // Displays backend fields validation errors
            handleValidationErrors(data.errors, data.fields);
        }
    })
    .catch(error => console.error('Error:', error));
});