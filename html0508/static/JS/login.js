document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    // 获取用户选择的身份类型
    var identity = document.getElementById('identity').value;
    
    // 根据不同的身份类型跳转到不同的页面
    switch (identity) {
        case 'hr':
            window.location.href = "/hr_home"; 
            break;
        case 'fire':
            window.location.href = "/119_home"; 
            break;
        case 'police':
            window.location.href = "/police_home"; 
            break;
        default:
            alert("請選擇有效的身分類型");
            break;
    }
});
