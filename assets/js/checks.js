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
function addMemberCheck () {
    return baseFinalCheck("Are you sure you want to add this user to the wiki?");
}
function createArticleCheck () {
    var articleName = document.getElementById("createArticleName").value;
    var articleBody = document.getElementById("createArticleBody").value;
    if (articleName.length == 0) {
        return alertError("Article name cannot be blank.");
    }
    if (articleName[0] != articleName[0].toUpperCase()) {
        return alertError("First letter of article name cannot be lowercase.");
    }
    if (articleBody.length == 0) {
        return alertError("Article body cannot be blank.");
    }
    return baseFinalCheck("Are you sure you want to create this article?");
}

function editArticleCheck () {
    return baseFinalCheck("Are you sure you want to edit this article?");
}

function createNewsArticleCheck () {
    return baseFinalCheck("Are you sure you want to create this news article?");
}

function editTagCheck () {
    return baseFinalCheck("Are you sure you want to edit this news tag?");
}

function editWikiSettingsCheck () {
    return baseFinalCheck("Are you sure you want to edit the settings of this wiki?");
}