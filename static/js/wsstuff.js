var socket = io.connect('https://' + document.domain + ":" + location.port);
var hiButton = document.getElementById('hiButton');
var hiList = document.getElementById('hiList');

socket.on('connect', function() { //Executed upon opening the site
    console.log('Successfully connected');
});

socket.on('receiveHi', function() {
    var newHi = document.createElement('li');
    newHi.innerText = "hi";
    hiList.appendChild(newHi);
});

hiButton.addEventListener('click', function() {
    socket.emit('sendHi');
});