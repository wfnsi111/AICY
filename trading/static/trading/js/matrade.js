

function selectedToRight() {

    // 获取select2标签
    var select2 = document.getElementById("select2");
    // 获取select1标签
    var select1 = document.getElementById("select1");
    // 获取option
    var option1 = select1.getElementsByTagName("option");
    // 遍历
    for (var i = 0; i < option1.length; i++) {
        var optioni = option1[i];
        //是否被选中
        if (optioni.selected == true) {
            // 添加到select2里面
            select2.appendChild(optioni);
            //数组长度发生变化，需要处理
            i--;
        }
    }
}

// 选中添加到左边
function selectedToLeft() {

    // 获取select2标签
    var select2 = document.getElementById("select2");
    // 获取select1标签
    var select1 = document.getElementById("select1");
    // 获取option
    var option2 = select2.getElementsByTagName("option");
    // 遍历
    for (var i = 0; i < option2.length; i++) {
        var optioni = option2[i];
        //是否被选中
        if (optioni.selected == true) {
            // 添加到select1里面
            select1.appendChild(optioni);
            //数组长度发生变化，需要处理
            i--;
        }
    }
}

// 全部添加到右边
function allToRight() {
    // 获取select2标签
    var select2 = document.getElementById("select2");
    // 获取select1标签
    var select1 = document.getElementById("select1");
    // 获取option
    var option1 = select1.getElementsByTagName("option");
    // 遍历
    for (var i = 0; i < option1.length; i++) {
        var optioni = option1[i];
        // 添加到select2里面
        select2.appendChild(optioni);
        //数组长度发生变化，需要处理
        i--;
    }
}


// 全部添加到左边
function allToLeft() {

    // 获取select2标签
    var select2 = document.getElementById("select2");
    // 获取select1标签
    var select1 = document.getElementById("select1");
    // 获取option
    var option2 = select2.getElementsByTagName("option");
    // 遍历
    for (var i = 0; i < option2.length; i++) {
        var optioni = option2[i];
        // 添加到select1里面
        select1.appendChild(optioni);
        //数组长度发生变化，需要处理
        i--;

    }
}


function my_prompt(){
     alert('启动成功');
}


function showFilename(file){
    $("#filename_label").html(file.name);
    console.log(file.name);
}