// 存放名字的列表
var nameList = [];
var tmp_name = ''

function checkFfFlag() {
    // 使用 Flask 提供的 URL 获取 ff_flag 的值
    fetch('/get_ff_flag')
        .then(response => response.json())
        .then(data => {
            console.log(data.ff_flag);
            console.log(data.name_list);
            if (data.ff_flag && !nameList.includes(data.name_list)) {
                // 将名字输出到控制台
                console.log("Received name:", data.name_list);
                // 将名字添加到列表中
                nameList.push(data.name_list);
                // 更新 name_list_content 的值
                document.getElementById('name_list_content').innerText = '你好！' + data.name_list + '\n是否打卡？';
                tmp_name = data.name_list
                // 显示 Bootstrap 5 Modal
                var myModal = new bootstrap.Modal(document.getElementById('successModal'));
                myModal.show();
                // 一分钟后从列表中移除名字
                setTimeout(function() {
                    var index = nameList.indexOf(data.name_list);
                    if (index > -1) {
                        nameList.splice(index, 1);
                    }
                }, 15000); // 一分钟后执行
            }
        })
        .catch(error => console.error('Error:', error));
}

// 每隔一秒检查一次 ff_flag 的值
setInterval(checkFfFlag, 1000);

// 当用户点击"确定"按钮时执行打卡操作

document.addEventListener("DOMContentLoaded", function() {
    var confirmButton = document.getElementById("confirmButton");
    if (confirmButton) {
        confirmButton.addEventListener("click", function() {
            axios.get('/get_ff_flag')
                .then(response => {
//                    var nameList = response.data.name_list;
                    axios.post('/clock_in', { name: tmp_name })
                        .then(response => {
                            console.log(tmp_name);
                            console.log(response.data.message);
                        })
                        .catch(error => {
                            console.error('An error occurred:', error);
                        });
                })
                .catch(error => {
                    console.error('An error occurred:', error);
                });
        });
    }
});


//document.getElementById('confirmButton').addEventListener('click', function() {
//    console.log("123123123");
//    var name = data.name_list;
//    axios.post('/clock_in', { name: name })
//        .then(response => {
//            console.log(response.data.message);
//        })
//        .catch(error => {
//            console.error('An error occurred:', error);
//        });
//});