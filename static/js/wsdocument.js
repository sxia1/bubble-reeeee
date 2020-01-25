var protocol = (new URL(document.location)).protocol;
var socket = io.connect(protocol + '//' + document.domain + ':' + location.port + '/document');

socket.on('connect', function() { //Executed upon opening the site
    var documentID = (new URL(document.location)).pathname.split('/').pop();
    socket.emit('joinDocument', documentID);
    console.log('Successfully connected');
});

socket.on('message', function(msg) {
    console.log(msg);
});