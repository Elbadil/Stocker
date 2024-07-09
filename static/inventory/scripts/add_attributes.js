const addAttrButton = document.getElementById('add-attr-btn');
const addAttrContainer = document.getElementById('add-attr-container')

addAttrButton.addEventListener('click', () => {
    const newAttrFields = `
        <div class='form-group'>
            <label for="attribute_name">Attributes And Options</label>
            <input type="text" name="attribute" class="form-control" required>
            <input type="text" name="attribute_value" class="form-control mt-2" required>
        </div>
    `;

    addAttrContainer.innerHTML += newAttrFields;
});
