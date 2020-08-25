function previewEdit (formID) {
    var editForm = document.getElementById(formID)
    editForm.removeAttribute("action");
    editForm.submit()
}

function selectCorrectOption (elID, val) {
    var selectElement = document.getElementById(elID);
    for (var i = 0; i < selectElement.children.length; i++) {
        if (selectElement.children[i].value == val) {
            selectElement.children[i].defaultSelected = true;
        } else {
            selectElement.children[i].defaultSelected = false;
        }
    }
}