var protocol = (new URL(document.location)).protocol;
var socket = io.connect(protocol + '//' + document.domain + ':' + location.port + '/document');

var canvases = document.getElementsByClassName('documentCanvas');
var pageContainer = document.getElementById('pageContainer');
var ctxArr = [];

var canDraw = false;

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

var setVisibility = function(public) {
    socket.emit('setVisibility', public);
    console.log("bwoop");
}

var addCollab = function(collaborator, write) {
    socket.emit('addCollab', [collaborator, write]);
}

var removeCollab = function(collaborator) {
    socket.emit('removeCollab', collaborator);
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

socket.on('enableDraw', function() {
    canDraw = true;
});

for (var page = 0; page < canvases.length; page++) {

    let canvasNum = page;

    var currCtx = canvases[canvasNum].getContext('2d');
    currCtx.lineCap = 'round';
    ctxArr.push(currCtx);

    canvases[canvasNum].addEventListener('mousedown', function(e) {
        if (canDraw) {
            prevX = e.offsetX;
            prevY = e.offsetY;
            isDrawing = true;
            drawLine(canvasNum, prevX, prevY, prevX, prevY, lineWidth, eraserMode ? 'e' : color);
        }
    });

    canvases[canvasNum].addEventListener('touchstart', function(e) {
        if (canDraw && e.touches.length == 1) {
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
        if (canDraw && isDrawing) {
            drawLine(canvasNum, prevX, prevY, e.offsetX, e.offsetY, lineWidth, eraserMode ? 'e' : color);
            prevX = e.offsetX;
            prevY = e.offsetY;
        }
    });

    canvases[canvasNum].addEventListener('touchmove', function(e) {
        if (canDraw && e.touches.length == 1) {
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

var pubpriv = document.getElementById('pubpriv');
pubpriv.addEventListener("click", function(e) {
    if (pubpriv.classList.contains("disabled")) {
        event.preventDefault();
        return;
    }
    if (pubpriv.classList.contains("btn-success")) { // currently public
        setVisibility(false); // to private
        pubpriv.classList.remove("btn-success");
        pubpriv.classList.add("btn-danger");
        pubpriv.innerHTML = 'private <i class="material-icons md-doc">lock</i>'; 
    }
    else if (pubpriv.classList.contains("btn-danger")) { // currently private
        setVisibility(true); // to public 
        pubpriv.classList.remove("btn-danger");
        pubpriv.classList.add("btn-success");
        pubpriv.innerHTML = 'public <i class="material-icons md-doc">lock_open</i>'; 
    }
});

function updatecolor(jscolor) {
    // 'jscolor' instance can be used as a string
    console.log(jscolor);
    console.log(jscolor.valueElement.value);
    color = jscolor.valueElement.value;
    console.log(color);
}

var eraser_button = document.getElementById('eraser_button');
function updateeraser(e) {
    eraserMode=!eraserMode;
    if (eraser_button.classList.contains("btn-light")) {
        eraser_button.classList.remove("btn-light");
        eraser_button.classList.add("btn-dark");
        eraser_button.childNodes[0].style.filter="invert(100%)";
    }
    else if (eraser_button.classList.contains("btn-dark")) {
        eraser_button.classList.remove("btn-dark");
        eraser_button.classList.add("btn-light");
        eraser_button.childNodes[0].style.filter="invert(0)";
    }
}

//$(document).ready(function () {
//  bsCustomFileInput.init()
//})
