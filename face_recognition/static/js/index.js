function executeRoute(event) {
    event.preventDefault();
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/features_extraction", true);
    xhr.send();
}