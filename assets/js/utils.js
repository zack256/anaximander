function previewEdit (formID) {
    var editForm = document.getElementById(formID)
    editForm.removeAttribute("action");
    editForm.submit()
}