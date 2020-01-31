document.querySelector('.custom-file-input').addEventListener('change',function(e){
    var fileName = document.getElementById("customFile").files[0].name;
    console.log(fileName);
    var nextSibling = e.target.nextElementSibling;
    nextSibling.innerText = fileName;
    document.getElementById("docName").value=fileName;
})

