var protocol = (new URL(document.location)).protocol;
var socket = io.connect(protocol + '//' + document.domain + ':' + location.port + '/document');

var canvas = document.getElementById('mainCanvas');
var ctx = canvas.getContext('2d');
ctx.lineCap = 'round';

var lineWidth = 3;
var color = 'rgba(0,0,0,1)';
var prevX = 0;
var prevY = 0;
var isDrawing = false;

var drawLine = function(x0, y0, x1, y1, inputWidth, inputColor, sendBack = true) {
    ctx.lineWidth = inputWidth;
    ctx.beginPath();
    ctx.moveTo(x0, y0); //Offset x and y by vector
    ctx.lineTo(x1, y1); //Draw line to center of the next circle
    ctx.strokeStyle = inputColor
    ctx.stroke();
    if (sendBack) {
        socket.emit('newLine', [x0, y0, x1, y1, inputWidth, inputColor]);
    }
}

socket.on('connect', function() { //Executed upon opening the site
    var documentID = (new URL(document.location)).pathname.split('/').pop();
    socket.emit('joinDocument', documentID);
    console.log('Successfully connected');
});

socket.on('lines', function(lines) {
    for (var i = 0; i < lines.length; i++) {
        var currLine = lines[i];
        drawLine(currLine[0], currLine[1], currLine[2], currLine[3], currLine[4], currLine[5], sendBack = false);
    }
});

socket.on('newLine', function(line) {
    drawLine(line[0], line[1], line[2], line[3], line[4], line[5], sendBack = false);
});

socket.on('message', function(msg) {
    console.log(msg);
});

canvas.addEventListener('mousedown', function(e) {
    prevX = e.offsetX;
    prevY = e.offsetY;
    isDrawing = true;
    drawLine(prevX, prevY, prevX, prevY, lineWidth, color);
});

canvas.addEventListener('touchstart', function(e) {
    var rect = e.target.getBoundingClientRect();
    prevX = e.targetTouches[0].pageX - rect.left;
    prevY = e.targetTouches[0].pageY - rect.top;
    isDrawing = true;
    drawLine(prevX, prevY, prevX, prevY, lineWidth, color);
    e.preventDefault();
});

canvas.addEventListener('mousemove', function(e) {
    if (isDrawing) {
        drawLine(prevX, prevY, e.offsetX, e.offsetY, lineWidth, color);
        prevX = e.offsetX;
        prevY = e.offsetY;
    }
});

canvas.addEventListener('touchmove', function(e) {
    var rect = e.target.getBoundingClientRect();
    offsetX = e.targetTouches[0].pageX - rect.left;
    offsetY = e.targetTouches[0].pageY - rect.top;
    if (isDrawing) {
        drawLine(prevX, prevY, offsetX, offsetY, lineWidth, color);
        prevX = offsetX;
        prevY = offsetY;
    }
    e.preventDefault();
});

canvas.addEventListener('mouseout', function(e) {
    isDrawing = false;
});

canvas.addEventListener('mouseup', function(e) {
    isDrawing = false;
});

canvas.addEventListener('touchend', function(e) {
    isDrawing = false;
    e.preventDefault();
});

$(function(){
	$('[data-toggle="popover"]').popover();
});
