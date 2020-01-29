var protocol = (new URL(document.location)).protocol;
var socket = io.connect(protocol + '//' + document.domain + ':' + location.port + '/document');

var canvases = document.getElementsByClassName('documentCanvas');
var pageContainer = document.getElementById('pageContainer');
var ctxArr = [];

var lineWidth = 3;
var color = 'rgba(0,0,0,1)';
var prevX = 0;
var prevY = 0;
var isDrawing = false;
var eraserMode = false;

var cursorStyle = document.createElement('style');
document.head.appendChild(cursorStyle);

var drawLine = function(page, x0, y0, x1, y1, inputWidth, inputColor, sendBack = true) {
    var ctx = ctxArr[page];
    ctx.lineWidth = inputWidth;
    if (inputColor == 'e') { //Eraser mode
        ctx.globalCompositeOperation = 'destination-out';
    } else {
        ctx.globalCompositeOperation = 'source-over';
    }
    ctx.beginPath();
    ctx.moveTo(x0, y0); //Offset x and y by vector
    ctx.lineTo(x1, y1); //Draw line to center of the next circle
    ctx.strokeStyle = inputColor
    ctx.stroke();
    if (sendBack) {
        socket.emit('newLine', [page, x0, y0, x1, y1, inputWidth, inputColor]);
    }
}

var changeCursor = function() {
    let newCursor = `cursor: url('data:image/svg+xml;utf8,\
      <svg id="svg" xmlns="http://www.w3.org/2000/svg" version="1.1" width="32" height="32">\
        <circle cx="12.5" cy="12.5" r="${lineWidth / 2 + 1}" fill-opacity="0" style="stroke: black;"/>\
        <circle cx="12.5" cy="12.5" r="${lineWidth / 2}" fill-opacity="0" style="stroke: white;"/>\
      </svg>')
    12.5 12.5, pointer;`
    cursorStyle.innerHTML = `.documentCanvas { ${newCursor} }`;
}

changeCursor();

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
        drawLine(canvasNum, prevX, prevY, prevX, prevY, lineWidth, eraserMode ? 'e' : color);
    });

    canvases[canvasNum].addEventListener('touchstart', function(e) {
        if (e.touches.length == 1) {
            var rect = e.target.getBoundingClientRect();
            var bodyRect = document.body.getBoundingClientRect();
            prevX = e.targetTouches[0].pageX - (rect.left - bodyRect.left);
            prevY = e.targetTouches[0].pageY - (rect.top - bodyRect.top);
            isDrawing = true;
            drawLine(canvasNum, prevX, prevY, prevX, prevY, lineWidth, eraserMode ? 'e' : color);
            if (e.cancelable) {
                e.preventDefault();
            }
        }
    });

    canvases[canvasNum].addEventListener('mousemove', function(e) {
        if (isDrawing) {
            drawLine(canvasNum, prevX, prevY, e.offsetX, e.offsetY, lineWidth, eraserMode ? 'e' : color);
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
                drawLine(canvasNum, prevX, prevY, offsetX, offsetY, lineWidth, eraserMode ? 'e' : color);
                prevX = offsetX;
                prevY = offsetY;
            }
            if (e.cancelable) {
                e.preventDefault();
            }
        }
    });
    
}

pageContainer.addEventListener('wheel', function(e) {
    if (e.target.matches('.documentCanvas')) { //Activated only when a canvas is targetted
        var change;
        if (e.deltaY > 0) {
            change = -1;
        } else {
            change = 1;
        }
        lineWidth += change;
        if (lineWidth < 3) { //Clamp min brush size to 3 pixels
            lineWidth = 3;
        } else if (lineWidth > 20) { //Clamp max brush size to 20 pixels
            lineWidth = 20;
        }
        changeCursor();
        e.preventDefault(); //Prevent user from scrolling down the page
    }
});

pageContainer.addEventListener('mouseout', function(e) {
    if (e.target.matches('.documentCanvas')) {
        isDrawing = false;
    }
});

pageContainer.addEventListener('mouseup', function(e) {
    if (e.target.matches('.documentCanvas')) {
        isDrawing = false;
    }
});

pageContainer.addEventListener('touchend', function(e) {
    isDrawing = false;
    if (e.cancelable) {
        e.preventDefault();
    }
});

document.getElementById("customFile").addEventListener('change',function(e){
    var fileName = document.getElementById("customFile").files[0].name;
    console.log(fileName);
    var nextSibling = e.target.nextElementSibling;
    nextSibling.innerText = fileName;
    document.getElementById("docName").value=fileName;
})

//$(document).ready(function () {
//  bsCustomFileInput.init()
//})
