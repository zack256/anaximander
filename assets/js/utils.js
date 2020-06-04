function previewEdit () {
    var editForm = document.getElementById("editArticleForm")
    editForm.removeAttribute("action");
    editForm.submit()
}