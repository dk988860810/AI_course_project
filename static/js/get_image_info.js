// 获取 URL 参数
const urlParams = new URLSearchParams(window.location.search);
const clickedImage = urlParams.get('clickedImage');
const imageInfoMap = {
    "1F_Area_A": "1樓A區",
    "1F_Area_B": "1樓B區",
    "1F_Area_C": "1樓C區",
};

// 创建新的 URL
const url_clickedImage = "call_cancel.html?clickedImage=" + clickedImage;

// 显示被点击的图片信息
document.addEventListener("DOMContentLoaded", function() {
    const clickedImageInfoElement = document.getElementById('clickedImageInfo');
    const clickedImageInfo = imageInfoMap[clickedImage] || '测试';
    clickedImageInfoElement.textContent =  clickedImageInfo;

    // 将点击按钮的 href 设置为动态生成的 URL
    const checkButton = document.getElementById('checkButton');
    checkButton.href = url_clickedImage;
});