
const categoryForm = document.getElementById('add_category_form');
const checkedProducts = document.querySelectorAll('input[name=category_products]:checked');

const handleValidationErrors = (errors, fields) => {
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
};

categoryForm.addEventListener('submit', (event) => {
    // Prevents the default form submission to handle it via JavaScript
    event.preventDefault();

    // Handling checked products
    let categoryProducts = [];
    const checkedProducts = document.querySelectorAll('input.category_products:checked');
    checkedProducts.forEach((product) => {
        categoryProducts.push(product.id)
    });
    console.log(categoryProducts);

    const formData = new FormData(categoryForm);
    if (categoryProducts.length > 0) {
        // Since the append method of FormData expects and converts into a string
        // We have utilized JSON.stringify so we can explicitly convert the array 
        // into a JSON-formatted string, preserving the array structure.
        formData.append('category_products', JSON.stringify(categoryProducts));
    }

    fetch('/inventory/add_category/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`Success: ${data.message}`);
            window.location.href = '/inventory/';
        // Checking if there are backend fields validation errors
        } else {
            console.log(`Error: Validation Errors from Django Form`);
            // Displays backend fields validation errors
            handleValidationErrors(data.errors, data.fields);
        }
    })
    .catch(error => console.error('Error:', error));
});
