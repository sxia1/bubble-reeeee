var protocol = (new URL(document.location)).protocol;
var socket = io.connect(protocol + '//' + document.domain + ':' + location.port + '/document');

var canvases = document.getElementsByClassName('documentCanvas');
var ctxArr = [];

var lineWidth = 3;
var color = 'rgba(0,0,0,1)';
var prevX = 0;
var prevY = 0;
var isDrawing = false;

var drawLine = function(page, x0, y0, x1, y1, inputWidth, inputColor, sendBack = true) {
    var ctx = ctxArr[page];
    ctx.lineWidth = inputWidth;
    ctx.beginPath();
    ctx.moveTo(x0, y0); //Offset x and y by vector
    ctx.lineTo(x1, y1); //Draw line to center of the next circle
    ctx.strokeStyle = inputColor
    ctx.stroke();
    if (sendBack) {
        socket.emit('newLine', [page, x0, y0, x1, y1, inputWidth, inputColor]);
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
        drawLine(currLine[0], currLine[1], currLine[2], currLine[3], currLine[4], currLine[5], currLine[6], sendBack = false);
    }
});

socket.on('newLine', function(line) {
    drawLine(line[0], line[1], line[2], line[3], line[4], line[5], line[6], sendBack = false);
});

socket.on('message', function(msg) {
    console.log(msg);
});

for (var page = 0; page < canvases.length; page++) {

    let canvasNum = page;

    var currCtx = canvases[canvasNum].getContext('2d');
    currCtx.lineCap = 'round';
    ctxArr.push(currCtx);

    canvases[canvasNum].addEventListener('mousedown', function(e) {
        prevX = e.offsetX;
        prevY = e.offsetY;
        isDrawing = true;
        drawLine(canvasNum, prevX, prevY, prevX, prevY, lineWidth, color);
    });

    canvases[canvasNum].addEventListener('touchstart', function(e) {
        if (e.touches.length == 1) {
            var rect = e.target.getBoundingClientRect();
            var bodyRect = document.body.getBoundingClientRect();
            prevX = e.targetTouches[0].pageX - (rect.left - bodyRect.left);
            prevY = e.targetTouches[0].pageY - (rect.top - bodyRect.top);
            isDrawing = true;
            drawLine(canvasNum, prevX, prevY, prevX, prevY, lineWidth, color);
            if (e.cancelable) {
                e.preventDefault();
            }
        }
    });

    canvases[canvasNum].addEventListener('mousemove', function(e) {
        if (isDrawing) {
            drawLine(canvasNum, prevX, prevY, e.offsetX, e.offsetY, lineWidth, color);
            prevX = e.offsetX;
            prevY = e.offsetY;
        }
    });

    canvases[canvasNum].addEventListener('touchmove', function(e) {
        if (e.touches.length == 1) {
            var rect = e.target.getBoundingClientRect();
            var bodyRect = document.body.getBoundingClientRect();
            offsetX = e.targetTouches[0].pageX - (rect.left - bodyRect.left);
            offsetY = e.targetTouches[0].pageY - (rect.top - bodyRect.top);
            if (isDrawing) {
                drawLine(canvasNum, prevX, prevY, offsetX, offsetY, lineWidth, color);
                prevX = offsetX;
                prevY = offsetY;
            }
            if (e.cancelable) {
                e.preventDefault();
            }
        }
    });
    
    canvases[canvasNum].addEventListener('mouseout', function(e) {
        isDrawing = false;
    });
    
    canvases[canvasNum].addEventListener('mouseup', function(e) {
        isDrawing = false;
    });
    
    canvases[canvasNum].addEventListener('touchend', function(e) {
        isDrawing = false;
        if (e.cancelable) {
            e.preventDefault();
        }
    });
}



