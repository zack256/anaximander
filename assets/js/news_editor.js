function updateEditTagModal (tagID, tagObj) {
    if (tagID == 0) {
        tagID = document.getElementById("ETID").value;
    }
    var tagArr = tagObj[tagID];
    document.getElementById("ETID").value = tagID;
    document.getElementById("ETName").innerHTML = tagArr[0];
    document.getElementById("ETDesc").value = tagArr[1];
}