// countdown.js

let countdownInterval; // 用于存储计时器的全局变量

function startCountdown(minutesToAdd, modalname) {
    clearInterval(countdownInterval); // 停止之前的计时器（如果有）

    const targetTime = new Date();
    targetTime.setMinutes(targetTime.getMinutes() + minutesToAdd);

    // 每秒更新倒数计时器
    countdownInterval = setInterval(() => {
        const currentTime = new Date().getTime();
        const distance = targetTime - currentTime;

        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        const countdownElement = document.getElementById(modalname);
        countdownElement.innerHTML = `剩餘時間：<br>${minutes} 分鐘 ${seconds} 秒`;

        if (distance <= 0) {
            clearInterval(countdownInterval);
            countdownElement.innerHTML = '時間到！';
            $('#check').modal('hide');
            $('#countdownreport').modal('show');
        }
    }, 1000); // 每秒更新一次
}

function stopCountdown(modalname) {
    clearInterval(countdownInterval); // 停止计时器
    const countdownElement = document.getElementById(modalname);
    countdownElement.innerHTML = ''; // 清空倒计时元素内容
}
