// Form Elements
const addVarSwitch = document.getElementById('add-variants-switch');
const addAttrContainer = document.getElementById('add-attr-container');
let addAttributes = JSON.parse(addAttrContainer.getAttribute('data-add-attr'));
const addItemForm = document.getElementById('add_item_form');

// Var: Number of additional attributes
let attrNum = 0;

// Var: Container Display
let containerDisplay = false;

// Fn: Generates Additional Attributes Options
const generateOptions = (attributes) => {
    return attributes.map(attr => `<option value="${attr}">${attr}</option>`).join('');
};

// Fn: Gets input field entered value by name
const getFieldValueByName = (name) => {
    const inputField = document.querySelector(`input[name="${name}"]`);
    return inputField ? inputField.value : null;
};

// Fn: Populating the Add Attributes Container with Elements
const formFields = (attrId, options) => {
    let attrFields =  `<div class='form-group attribute-field' id="form-group-${attrId}">`
    if (attrId !== 1) {
        attrFields += '<hr>'
    }
    attrFields += `
            <!-- Additional Attribute -->
            <div class="row align-items-center">
                <div class="col">
                    <div class="form-floating">
                        <input type="text" class="form-control mb-2 attr" name="add-attr-${attrId}" id="floatingInputGrid-${attrId}" list="add-attr-list-${attrId}" placeholder="e.g. Color or Size" required>
                        <datalist id="add-attr-list-${attrId}">
                            <select id="product_add-attr">
                                ${options}
                            </select>
                        </datalist>
                        <label class="attr" for="floatingInputGrid-${attrId}" style="color: grey;">Attribute (e.g. Color or Size)</label>
                    </div>
                </div>
                <!-- Delete Attribute Button -->
                <div class="col-auto">
                    <button class="btn btn-outline-secondary delete-icon mb-2" type="button" data-index="${attrId}">
                        <i class="bi bi-archive-fill" style="font-size: 20px;"></i> <!-- Example using Bootstrap Icons -->
                    </button>
                </div>
            </div>
            <!-- Options (Additional Attribute Descriptions) -->
            <div class="form-floating">
                <input type="text" class="form-control opt" name="add-attr-desc-${attrId}" id="floatingInputGrid-desc-${attrId}" placeholder="Type options separated by comma" required>
                <label class="opt" for="floatingInputGrid-desc-${attrId}" style="color: grey;">Options (Type options separated by comma)</label>
            </div>
        </div>`;
    return attrFields;
};

// Fn: Adds New Attribute Fields
const addNewAttribute = () => {
    attrNum++;
    const newAttribute = `
        ${formFields(attrNum, options)}
    `;
    document.getElementById('form-groups').insertAdjacentHTML('beforeend', newAttribute);
    setupDeleteButtons();
}

// Fn: Removes Element from the Page
const removeElement = (elementId) => {
    const element = document.getElementById(elementId);
    return element.parentNode.removeChild(element);
}

// Fn: Handles attribute fields deletion
const handleDeleteAttribute = (event) => {
    const attrDeletion = event.currentTarget;
    const attrIndex = attrDeletion.getAttribute('data-index');

    console.log(`---- initial length before deletion: ${attrNum} and attrId: ${attrIndex}`);

    if (attrNum === 1) {
        console.log(`You are trying to delete attribute ${attrIndex} from handle`);
        attrNum--;
        addVarSwitch.checked = false;
        containerDisplay = false;
        addAttrContainer.innerHTML = ''; // Clear container
        console.log(`Deleted attr ${attrIndex} from handle the length now is ${attrNum}`);
    } else {
        console.log(`You are trying to delete attribute ${attrIndex} from remove`);
        attrNum--;
        removeElement(`form-group-${attrIndex}`);
        updateAttributeIDs();
        console.log(`Deleted attr ${attrIndex} from remove the length now is ${attrNum}`);
    }
    // Re-setup delete buttons after an attribute is deleted
    setupDeleteButtons();
}

// Fn: Sets up delete button event listeners
// Adds a click listener to the attribute's delete btn when the
// attribute's field is dynamically added/updated
const setupDeleteButtons = () => {
    document.querySelectorAll('.delete-icon').forEach((attrDeletion) => {
        // removes any existing click event listeners attached to the
        // current attrDeletion element. This ensures that we don’t
        // have multiple listeners attached to the same element.
        attrDeletion.removeEventListener('click', handleDeleteAttribute);
        // Adds the delete listener
        attrDeletion.addEventListener('click', handleDeleteAttribute);
    });
}

// Fn: Updates Attribute IDs when an Attribute field is deleted
const updateAttributeIDs = () => {
    const formGroups = document.querySelectorAll('.attribute-field');
    formGroups.forEach((formGroup, index) => {
        const newAttrId = index + 1;
        // Form ID
        formGroup.id = `form-group-${newAttrId}`;
        // Attribute Input Field
        const attrInput = formGroup.querySelector('input.attr');
        attrInput.name = `add-attr-${newAttrId}`;
        attrInput.list = `add-attr-list-${newAttrId}`;
        // Attribute Datalist Element
        const datalist = formGroup.querySelector('datalist');
        datalist.id = `add-attr-list-${newAttrId}`;
        // Attribute Label Element
        const attLabel = formGroup.querySelector('label.attr');
        attLabel.for = `floatingInputGrid-${newAttrId}`;
        // Options Input Fields
        const optInput = formGroup.querySelector('input.opt');
        optInput.name = `add-attr-desc-${newAttrId}`;
        // Options Label Element
        const optLabel = formGroup.querySelector('label.opt');
        optLabel.for = `floatingInputGrid-desc-${newAttrId}`
        // Delete Button
        const deleteButton = formGroup.querySelector('.delete-icon');
        deleteButton.setAttribute('data-index', newAttrId);
    });
    // Updating attrNum to the new count
    attrNum = formGroups.length;
}

// Var: initializing fields and attributes options
let options = generateOptions(addAttributes);
const initialFields = `
    <label for="add-attr">Attributes And Options<span style="color: red;">*</span></label>
    <div id="form-groups">
        ${formFields(1, options)}
    </div>
    <!-- Add Other Attributes Button -->
    <button type="button" id="add-attr-btn" class="btn btn-secondary">Add Attribute</button>
`;

// Listener: Adding/Removing Additional Attributes Container
addVarSwitch.addEventListener('click', () => {
    if (!containerDisplay) {
        attrNum++;
        addAttrContainer.innerHTML = initialFields;
        containerDisplay = true;
        document.getElementById('add-attr-btn').addEventListener('click', addNewAttribute);
        setupDeleteButtons();
    } else {
        attrNum = 0;
        addAttrContainer.innerHTML = '';
        containerDisplay = false;
    }
});


// Form Submission: Sending with form submission the number of additional Attrs
addItemForm.addEventListener('submit', (event) =>{
    event.preventDefault(); // Prevents default form submission
    
    const attr_num = document.getElementById('attr_num');
    attr_num.value = JSON.stringify(attrNum);

    addItemForm.submit();
});