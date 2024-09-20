
const addCategorySupplierForm = document.getElementById('add_category_supplier_form');

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

addCategorySupplierForm.addEventListener('submit', (event) => {
    // Prevents the default form submission to handle it via JavaScript
    event.preventDefault();

    // Handling checked products
    let userItems = [];
    const checkedItems = document.querySelectorAll('input.user_items:checked');
    checkedItems.forEach((item) => {
        userItems.push(item.id)
    });
    console.log(userItems);

    const formData = new FormData(addCategorySupplierForm);
    if (userItems.length > 0) {
        // Since the append method of FormData expects and converts into a string
        // We have utilized JSON.stringify so we can explicitly convert the array 
        // into a JSON-formatted string, preserving the array structure.
        formData.append('user_items', JSON.stringify(userItems));
    }

    const formTitle = document.getElementById('form_title');
    let formUrl;
    if (formTitle.textContent.includes('Category')) {
        formUrl = '/inventory/add_category/';
    } else {
        formUrl = '/inventory/add_supplier/';
    }

    fetch(formUrl, {
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
