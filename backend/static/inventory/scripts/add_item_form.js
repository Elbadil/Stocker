// Form Elements
const addVarSwitch = document.getElementById('add-variants-switch');
const addVarContainer = document.getElementById('add-variants-container');
let variants = JSON.parse(addVarContainer.getAttribute('data-variants'));
const addItemForm = document.getElementById('add_item_form');

// Var: Number of Item's Variants
let variantsNum = 0;

// Var: Container Display
let containerDisplay = false;

// Fn: Generates Existing Variants Options
const generateOptions = (variants) => {
    return variants.map(variant => `<option value="${variant}">${variant}</option>`).join('');
};

// Fn: Populating the Items Variants Container with Field Elements
const formFields = (variantId, options) => {
    let variantFields =  `<div class='form-group variant-field' id="form-group-${variantId}">`
    if (variantId !== 1) {
        variantFields += '<hr>'
    }
    variantFields += `
            <!-- Item's Variant -->
            <div class="row align-items-center">
                <div class="col">
                    <div class="form-floating">
                        <input type="text" class="form-control mb-2 variant" name="variant-${variantId}" data-index=${variantId} id="floatingInputGrid-${variantId}" list="variant-list-${variantId}" placeholder="e.g. Color or Size" required>
                        <datalist id="variant-list-${variantId}">
                            <select id="item_variant">
                                ${options}
                            </select>
                        </datalist>
                        <label class="variant" for="floatingInputGrid-${variantId}" style="color: grey;">Variant (e.g. Color or Size)</label>
                    </div>
                </div>
                <!-- Delete Variant Button -->
                <div class="col-auto">
                    <button class="btn btn-outline-secondary delete-icon mb-2" type="button" data-index="${variantId}">
                        <i class="bi bi-archive-fill" style="font-size: 20px;"></i> <!-- Example using Bootstrap Icons -->
                    </button>
                </div>
            </div>
            <!-- Options (Variant Options) -->
            <div class="form-floating">
                <input type="text" class="form-control opt" name="variant-opt-${variantId}" id="floatingInputGrid-opt-${variantId}" placeholder="Type options separated by comma" required>
                <label class="opt" for="floatingInputGrid-opt-${variantId}" style="color: grey;">Options (Type options separated by comma)</label>
            </div>
            <!-- Validation Errors -->
            <div class="invalid-feedback" id="variant-error-${variantId}" data-index="${variantId}"></div>
        </div>`;
    return variantFields;
};

// Fn: Adds New Variant Fields
const addNewVariantFields = () => {
    variantsNum++;
    const newVariant = `
        ${formFields(variantsNum, options)}
    `;
    console.log(`---- length After Addition: ${variantsNum} -------`);
    document.getElementById('form-groups').insertAdjacentHTML('beforeend', newVariant);
    setupDynamicElements();
}

// Fn: Removes Element from the Page
const removeElement = (elementId) => {
    const element = document.getElementById(elementId);
    return element.parentNode.removeChild(element);
}

// Fn: Handles Variants fields deletion
const handleDeleteVariant = async (event) => {
    const varDeletion = event.currentTarget;
    const varIndex = varDeletion.getAttribute('data-index');
    // const varForm = document.getElementById(`form-group-${varIndex}`);
    // const varValue = varForm.querySelector('input.variant').value;
    // if (varValue) {
    //     updateVarFieldsErrors();
    // }

    console.log(`---- initial length before deletion: ${variantsNum} and varId: ${varIndex}`);

    if (variantsNum === 1) {
        console.log(`You are trying to delete variant ${varIndex} from handle`);
        variantsNum--;
        addVarSwitch.checked = false;
        containerDisplay = false;
        addVarContainer.innerHTML = ''; // Clear container
        console.log(`Deleted variant ${varIndex} from handle the length now is ${variantsNum}`);
    } else {
        console.log(`You are trying to delete variant ${varIndex} from remove`);
        variantsNum--;
        removeElement(`form-group-${varIndex}`);
        updateVariantsIDs();
        updateVarFieldsErrors(varIndex);
        console.log(`Variants Num: ${variantsNum}`)
        if (varIndex == 1) {
            const parentElement = document.getElementById(`form-group-${varIndex}`);
            const hrElement = parentElement.querySelector('hr');
            if (hrElement) {
                hrElement.remove();
            }
        }
        await updateVariantsIDs();
        updateVarFieldsErrors();
        console.log(`Deleted variant ${varIndex} from remove the length now is ${variantsNum}`);
    }
    // Re-setup delete buttons after a variant is deleted
    setupDynamicElements();
}

// Fn: Lists the Variants that the user has entered/selected
const selectedVariants = () => {
    const allVariants = document.querySelectorAll('input.variant');
    let varEnteredList = [];
    allVariants.forEach((variant) => {
        if (variant.value.trim().length > 0) { // trim() to handle leading/trailing spaces
            varEnteredList.push(variant.value.toLowerCase());
        }
    });
    console.log(`List Of Selected Variants: ${varEnteredList}`);
    return varEnteredList;
}

// Fn: Updates Variant Field Error When a Field is deleted
const updateVarFieldsErrors = () => {
    console.log('Updating Field Errors')
    const varFieldsErrors = document.querySelectorAll('.variant-errors');
    const addedVariants = selectedVariants();
    varFieldsErrors.forEach((variantError) => {
        console.log('Updating Field Errors For Each');
        const varIndex = variantError.getAttribute('data-index')
        console.log(`var Index in Field Errors: ${varIndex}`)
        if (variantError.classList.contains('d-block')) {
            const varForm = document.getElementById(`form-group-${varIndex}`);
            const varValue = varForm.querySelector('input.variant').value;
            console.log(`Updating Field Errors for Value: ${varValue}`)
            if (!addedVariants.includes(varValue.toLowerCase())
                || addedVariants.filter(variant => variant === varValue.toLowerCase()).length <= 1) {
                variantError.innerHTML = '';
                variantError.classList.remove('d-block', 'variant-errors');
            }
        }
    });
};

// Fn: Checks the new Added Variant is unique and wasn't selected in other fields
const handleNewVariantField = (event) => {
    const varField = event.currentTarget;
    const varFieldValue = varField.value.trim();
    const varFieldId = varField.getAttribute('data-index');
    const varFieldError = document.getElementById(`variant-error-${varFieldId}`);
    console.log(varFieldValue, varFieldId);

    const addedVariants = selectedVariants();

    if (addedVariants.filter(x => x === varFieldValue.toLowerCase()).length > 1) {
        varFieldError.innerHTML = `Variant ${varFieldValue} has already been selected. Please select another variant`;
        varFieldError.classList.add('d-block', 'variant-errors');
    } else {
        varFieldError.innerHTML = '';
        varFieldError.classList.remove('d-block', 'variant-errors');
    }
}

// Fn: Sets up delete button event listeners
// Adds a click listener to the variant's delete btn when the
// variant's field is dynamically added/updated
const setupDynamicElements = () => {
    document.querySelectorAll('.delete-icon').forEach((varDeletion) => {
        // removes any existing click event listeners attached to the
        // current varDeletion element. This ensures that we don’t
        // have multiple listeners attached to the same element.
        varDeletion.removeEventListener('click', handleDeleteVariant);
        // Adds the delete listener
        varDeletion.addEventListener('click', handleDeleteVariant);
    });
    document.querySelectorAll('input.variant').forEach((varField) => {
        varField.removeEventListener('blur', handleNewVariantField);
        varField.addEventListener('blur', handleNewVariantField);
    });
}

// Fn: Handles the display of fields form errors that were sent from the backend 
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
}

// Fn: Checks Validation Errors From Added Variants
const variantsValidationErrors = () => {
    const variantsErrors = document.querySelectorAll('.variant-errors');
    return variantsErrors.length > 0;
}

// Fn: Updates Variants IDs when an Variants field is deleted
const updateVariantsIDs = async () => {
    console.log('Updating Ids---')
    const formGroups = document.querySelectorAll('.variant-field');
    formGroups.forEach((formGroup, index) => {
        const newVarId = index + 1;
        // Form ID
        formGroup.id = `form-group-${newVarId}`;
        // Variant Input Field
        const varInput = formGroup.querySelector('input.variant');
        varInput.name = `variant-${newVarId}`;
        varInput.setAttribute('data-index', newVarId)
        varInput.setAttribute('list', `variant-list-${newVarId}`);
        varInput.id = `floatingInputGrid-${newVarId}`;
        // Variant Datalist Element
        const datalist = formGroup.querySelector('datalist');
        datalist.id = `variant-list-${newVarId}`;
        // Variant Label Element
        const varLabel = formGroup.querySelector('label.variant');
        varLabel.for = `floatingInputGrid-${newVarId}`;
        // Options Input Fields
        const optInput = formGroup.querySelector('input.opt');
        optInput.name = `variant-opt-${newVarId}`;
        optInput.id = `floatingInputGrid-opt-${newVarId}`;
        // Options Label Element
        const optLabel = formGroup.querySelector('label.opt');
        optLabel.for = `floatingInputGrid-opt-${newVarId}`;
        // Field Error
        const fieldError = formGroup.querySelector('.invalid-feedback');
        fieldError.id = `variant-error-${newVarId}`
        fieldError.setAttribute('data-index', newVarId)
        // Delete Button
        const deleteButton = formGroup.querySelector('.delete-icon');
        deleteButton.setAttribute('data-index', newVarId);
    });
    // Updating variantsNum to the new count
    variantsNum = formGroups.length;
};

// Var: initializing variants fields
let options = generateOptions(variants);
const initialFields = `
    <label for="variant" class="form-label">Variants And Options<span style="color: red;">*</span></label>
    <div id="form-groups">
        ${formFields(1, options)}
    </div>
    <!-- Add Other Variant Button -->
    <button type="button" id="add-variant-btn" class="btn btn-secondary mt-2">Add Variant</button>
`;

// Handling edit Item form with variants
if (addVarSwitch.hasAttribute('checked')) {
    const formGroups = document.querySelectorAll('.variant-field');
    variantsNum = formGroups.length;
    containerDisplay = true;
    document.getElementById('add-variant-btn').addEventListener('click', addNewVariantFields);
    setupDynamicElements();
}

// Listener: Adding/Removing Add Variants Container
addVarSwitch.addEventListener('click', () => {
    if (!containerDisplay) {
        variantsNum++;
        addVarContainer.innerHTML = initialFields;
        containerDisplay = true;
        document.getElementById('add-variant-btn').addEventListener('click', addNewVariantFields);
        setupDynamicElements();
    } else {
        variantsNum = 0;
        addVarContainer.innerHTML = '';
        containerDisplay = false;
    }
});

// Form Submission: Sends with form submission the number of item's variants
// And checks if there are any fields Validation Errors
addItemForm.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent default form submission

    // Checking if there are item's variants validation errors
    if (variantsValidationErrors()) {
        console.log('You have validation errors from Items Variants');
    } else {
        let formData = new FormData(addItemForm);
        if (variantsNum > 0) {
            formData.append('variants_num', variantsNum);
        }
        let formUrl;
        const formTitle = document.getElementById('form-title');
        if (formTitle.textContent.startsWith('Add')) {
            formUrl = '/inventory/add_item/';
        } else {
            const itemId = document.getElementById('item_id');
            formUrl = `/inventory/edit_item/${itemId.value}/`;
        }
        fetch(formUrl, {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`Success ${data.message}`);
                window.location.href = '/inventory/';
            }
            // Checking if there are backend fields validation errors
            else {
                console.log(`Error: Validation Errors from Django Form`);
                // Displays backend fields validation errors
                handleValidationErrors(data.errors, data.fields);
            }
        })
        .catch(error => console.error('Error:', error));
    }
});
