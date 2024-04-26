// 获取 URL 参数
const urlParams = new URLSearchParams(window.location.search);
const clickedImage = urlParams.get('clickedImage');
const imageInfoMap = {
    "1F_Area_A":"1樓A區",
    "1F_Area_B":"1樓B區",
    "1F_Area_C":"1樓C區",
}

const clickedImageInfo = imageInfoMap[clickedImage] || 'test'
// 显示被点击的图片信息
const clickedImageInfoElement = document.getElementById('clickedImageInfo');
clickedImageInfoElement.textContent = clickedImageInfo;