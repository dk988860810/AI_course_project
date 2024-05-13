// 获取所有的导航栏选项
var navItems = document.querySelectorAll('nav ul li');

// 遍历每个导航栏选项
navItems.forEach(function(navItem) {
  // 监听鼠标悬停事件
  navItem.addEventListener('mouseover', function() {
    // 获取当前选项的子菜单
    var subMenu = navItem.querySelector('ul');
    // 将子菜单的透明度设置为 1，实现渐入效果
    subMenu.style.opacity = 1;
  });

  // 监听鼠标离开事件
  navItem.addEventListener('mouseout', function() {
    // 获取当前选项的子菜单
    var subMenu = navItem.querySelector('ul');
    // 将子菜单的透明度设置为 0，实现渐出效果
    subMenu.style.opacity = 0;
  });
});
