function baseFinalCheck (msg) {
    var res = confirm (msg);
    return res;
}

function alertError (msg) {
    alert(msg);
    return false;
}

function addWikiCheck () {
    return baseFinalCheck("Are you sure you want to add this wiki?");
}
function createArticleCheck () {
    var articleName = document.getElementById("createArticleName").value;
    if (articleName.length == 0) {
        return alertError("Article name cannot be blank.");
    }
    if (articleName[0] != articleName[0].toUpperCase()) {
        return alertError("First letter of article name cannot be lowercase.");
    }
    return baseFinalCheck("Are you sure you want to create this article?");
}

function editArticleCheck () {
    return baseFinalCheck("Are you sure you want to edit this article?");
}

function createNewsArticleCheck () {
    return baseFinalCheck("Are you sure you want to create this news article?");
}