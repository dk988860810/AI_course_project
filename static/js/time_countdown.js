// countdown.js

function startCountdown(minutesToAdd) {
    const targetTime = new Date();
    targetTime.setMinutes(targetTime.getMinutes() + minutesToAdd);

    // 每秒更新倒數計時器
    const interval = setInterval(() => {
        const currentTime = new Date().getTime();
        const distance = targetTime - currentTime;

        // 計算剩餘的分鐘和秒
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        // 將計算結果顯示在網頁上
        const countdownElement = document.getElementById('countdown');
        countdownElement.innerHTML = `剩餘時間：<br>${minutes} 分鐘 ${seconds} 秒`;

        // 如果時間到，清除倒數計時器並顯示訊息
        if (distance <= 0) {
            clearInterval(interval);
            countdownElement.innerHTML = '時間到！';
            alert("時間到 已報警")
        }
    }, 1000); // 每秒更新一次
}
