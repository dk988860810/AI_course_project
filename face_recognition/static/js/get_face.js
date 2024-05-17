document.addEventListener("DOMContentLoaded", function() {
    var stopButton = document.getElementById("stop_button");
    if (stopButton) {
        stopButton.addEventListener("click", function() {
            console.log("Video capture stopped.");
            fetch("/stop_video_capture")
                .then(response => {
                    if (response.ok) {
                        console.log("Video capture stopped.");
                    } else {
                        console.error("Error stopping video capture.");
                    }
                })
                .catch(error => console.error("Error stopping video capture:", error));
        });
    }
});


function checklabelwarning() {
    var labelElement = document.getElementById('label_warning_content');
    if(labelElement) {
        var labelWarning = labelElement.innerText;
        // 使用 Flask 提供的 URL 获取 label_warning 的值
        fetch('/get_label_warning')
            .then(response => response.json())
            .then(data => {
//                console.log(data.label_warning);
                if (data.label_warning === "OUT OF RANGE") {
                    labelElement.style.color = "red"; // 如果是OUT OF RANGE，设置为红色
                } else if (data.label_warning === "IN RANGE") {
                    labelElement.style.color = "green"; // 如果是IN RANGE，设置为绿色
                }
                labelElement.innerText = data.label_warning;
            })
            .catch(error => console.error('Error:', error));
    }
}
// 每隔一秒检查一次 labelwarning 的值
setInterval(checklabelwarning, 1000);


function goToIndex() {
window.location.href = "/profile"
}

function handleSubmit(event) {
            event.preventDefault(); // 阻止表单的默认提交行为

            const name = document.getElementById('name').value;
            const xhr = new XMLHttpRequest();
            const url = '/input_name';

            xhr.open('POST', url, true);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    alert('Name submitted: ' + xhr.responseText); // 处理响应数据
                }
            };

            xhr.send('name=' + encodeURIComponent(name));
        }

function handleSaveFace(event) {
            event.preventDefault(); // 阻止表单的默认提交行为

            const xhr = new XMLHttpRequest();
            const url = '/save_face';

            xhr.open('POST', url, true);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    alert('Face data saved: ' + xhr.responseText); // 处理响应数据
                }
            };

            xhr.send();
        }