const baseUrl = ""
const TB = document.getElementById("algo");
var oldVal = "";
var GO = "";
var RES;
var pname = "";
var subtn =document.getElementById('subtn');
var res_dom = document.getElementById("res");

var toggle = document.getElementById("dark")

window.addEventListener("load", () => {
    let theme = localStorage.getItem("theme")
    if (theme === null) {
        localStorage.setItem("theme", "default")
    } else {
        toggle.checked = theme == "material"
    }
});

var editor = CodeMirror.fromTextArea(TB, {
    matchBrackets: true,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: true,
    lineNumbers: true,
    autoCloseBrackets: true,
    theme: localStorage.getItem("theme") || "default",
    mode: 'algo'
});

editor.on("change", (cm) => {
    TB.value = cm.getValue(); 
 });


toggle.addEventListener("change", (e) => {
    if (e.target.checked){
        localStorage.setItem("theme", "material")
    } else {
        localStorage.setItem("theme", "default")
    }
    editor.setOption("theme", localStorage.getItem("theme"))
});

  

//TB.addEventListener("click", function() {
//    if (localStorage.getItem("ft") === null) {
//        var c = confirm("Sebelum melanjutkan, mohon baca dokumentasi dahulu supaya anda bisa menulis pseudocode dengan benar.\n Tekan Ok untuk membaca.")
//        if (c) {
//            localStorage.setItem("ft", "ok")
//            window.open("https://github.com/versa-syahptr/pseudocode-parser", "tab")
//            //document.getElementById("gh").click()
//        }
//    }
//});


function sendData() {
    // (A) GET FORM DATA
    if (oldVal != TB.value) {
        oldVal = TB.value;
        subtn.disabled=true;
    } else {
        return false;
    }
    if (oldVal.includes("<script>")) {
        alert("no programming languages allowed!\nincluding javascript!");
        TB.value = "";
        return false;
    }
    
    var data = new FormData();
    data.append("algo", oldVal);

    // (B) INIT FETCH POST
    fetch(baseUrl+"/auto", {
        method: "POST",
        body: data
    })

    // (C) RETURN SERVER RESPONSE AS TEXT
    .then((result) => {
        if (result.status != 200) {
            throw new Error("Bad Server Response: "+result.status);
        }
        return result.json();
    })

    // (D) SERVER RESPONSE
    .then((response) => {
        
        res_dom.innerHTML = response.res;
        res_dom.parentElement.scrollIntoView();
        activate(response);
        subtn.disabled=false;
    })

    // (E) HANDLE ERRORS - OPTIONAL
    .catch((error) => {
        console.error(error)
        alert(error);
        subtn.disabled=false;
    });

    // (F) PREVENT FORM SUBMIT
    return false;
}

function activate(go) {
    // activate prism.js if no error from BE
    var div = document.getElementById("run")
    if (go.success) {
//        var rex = /^program (\w+)$/gm
//        var match = rex.exec(oldVal)
        pname = go.filename
        res_dom.classList.add("language-go")
        Prism.highlightElement(res_dom);
        div.classList.remove("hide")
        GO = go.res;
    } else {
        res_dom.classList.remove("language-go")
        res_dom.parentElement.classList.remove("language-go")
        div.classList.add("hide")
    }

}

function gorun() {
    var obj = {
        "name": "Go",
        "title": "Go Hello World!",
        "mode": "golang",
        "description": null,
        "extension": "go",
        "languageType": "programming",
        "active": true,
        "properties": {
            "language": "go",
            "stdin": document.getElementById("input").value,
            "files": [{
                "name": pname + ".go",
                "content": GO
            }]
        },
        "visibility": "public"
    }

    fetch(baseUrl+"/pass.php", {
            method: 'POST',
            body: JSON.stringify(obj),
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then((result) => {
            if (result.status != 200) {
                throw new Error("Bad Server Response");
            }
            return result.json();
        })
        .then((resp) => {
            RES = resp;
            console.log(resp)
            display(resp);
        })
        .catch((error) => {
            alert(error);
        });
}

function display(res) {
// display output from running golang
    document.getElementById("runres").classList.remove("hide")
    var field = document.getElementById("resf")
    if (res.stdout !== null) {
        field.innerHTML = res.stdout
        field.style.color = "black"
    } else if (res.stderr !== null) {
        field.innerHTML = res.stderr
        field.style.color = "red"
    } else {
        field.innerHTML = "Unknown error occured"
        field.style.color = "red"
    }

}