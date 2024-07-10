// Form Elements
const addVarSwitch = document.getElementById('add-variants-switch');
const addAttrContainer = document.getElementById('add-attr-container');
let addAttributes = JSON.parse(addAttrContainer.getAttribute('data-add-attr'));
const addItemForm = document.getElementById('add_item_form');

// Number of additional attributes
let attrLength = 0;

// Container Display
let containerDisplay = false;

// Additional Attributes Options
const generateOptions = (attributes) => {
    return attributes.map(attr => `<option value="${attr}">${attr}</option>`).join('');
};

// Container initial content
const formFields = (attrLength, options) => {
    const attrId = attrLength + 1;
    const attrFields =  `
        <div class='form-group' id="form-group-${attrId}">
            <!-- Additional Attribute ${attrId} -->
            <div class="row align-items-center">
                <div class="col">
                    <div class="form-floating">
                        <input type="text" class="form-control mb-2" name="add-attr-${attrId}" id="floatingInputGrid-${attrId}" list="add-attr-list-${attrId}" placeholder="e.g. Color or Size" required>
                        <datalist id="add-attr-list-${attrId}">
                            <select id="product_add-attr">
                                ${options}
                            </select>
                        </datalist>
                        <label for="floatingInputGrid-${attrId}" style="color: grey;">Attribute (e.g. Color or Size)</label>
                    </div>
                </div>
                <!-- Delete Attribute Button ${attrId} -->
                <div class="col-auto">
                    <button class="btn btn-outline-secondary delete-icon mb-2" type="button" data-index="${attrId}">
                        <i class="bi bi-archive-fill" style="font-size: 20px;"></i> <!-- Example using Bootstrap Icons -->
                    </button>
                </div>
            </div>
            <!-- Options (Additional Attribute ${attrId} Descriptions) -->
            <div class="form-floating">
                <input type="text" class="form-control" name="add-attr-desc-${attrId}" id="floatingInputGrid-desc-${attrId}" placeholder="Type options separated by comma" required>
                <label for="floatingInputGrid-desc-${attrId}" style="color: grey;">Options (Type options separated by comma)</label>
            </div>
        </div>`;
    return attrFields;
};

let options = generateOptions(addAttributes);
const initialFields = `
    <label for="add-attr">Attributes And Options<span style="color: red;">*</span></label>
    <div id="form-groups">
        ${formFields(attrLength, options)}
    </div>
    <!-- Add Other Attributes Button -->
    <button type="button" id="add-attr-btn" class="btn btn-secondary">Add Attribute</button>
`;

// Additional Attributes Form Display
addVarSwitch.addEventListener('click', () => {
    if (!containerDisplay) {
        addAttrContainer.innerHTML = initialFields;
        containerDisplay = true;
        document.getElementById('add-attr-btn').addEventListener('click', addNewAttribute);
    } else {
        addAttrContainer.innerHTML = '';
        containerDisplay = false;
    }
});

// Gets input field entered value by name
const getFieldValueByName = (name) => {
    const inputField = document.querySelector(`input[name="${name}"]`);
    return inputField ? inputField.value : null;
};

// Adding New Attribute Fields
const addNewAttribute = () => {
    attrLength++;
    let newOptions;
    const previousAttribute = getFieldValueByName(`add-attr-${attrLength}`);
    if (previousAttribute) {
        addAttributes = addAttributes.filter(item => item !== previousAttribute);
        newOptions = generateOptions(addAttributes);
    }
    const newAttribute = `
        <hr>
        ${formFields(attrLength, newOptions)}
    `;
    document.getElementById('form-groups').insertAdjacentHTML('beforeend', newAttribute);
}


// Sending with form submission the number of additional Attributes
addItemForm.addEventListener('submit', (event) =>{
    event.preventDefault(); // Prevents default form submission
    // Collect form data
    let formData = new FormData(addItemForm);

    // Append additional attributes
    formData.append('attr_length', attrLength);
    
    // Make an HTTP POST request to Django
    fetch('inventory/add_item/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Handle response from Django if needed
        console.log('Response from Django:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
});