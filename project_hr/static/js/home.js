const loginLink = document.getElementById('login-link');

// 添加单击事件监听器
loginLink.addEventListener('click', function(event) {
    event.preventDefault(); // 阻止默认链接行为
    window.location.href = '/templates/login.html'; // 跳转到登录页面
});
​
// 初始化动画
const rotateTL = new TimelineMax({ paused: true })
  .to(".play-circle-01", .7, {
    opacity: .1,
    rotation: '+=360',
    strokeDasharray: "456 456",
    ease: Power1.easeInOut
  }, 0)
  .to(".play-circle-02", .7, {
    opacity: .1,
    rotation: '-=360',
    strokeDasharray: "411 411",
    ease: Power1.easeInOut
  }, 0)
​
const openTL = new TimelineMax({ paused: true })
  .to(".play-backdrop", 1, {
    opacity: .95,
    visibility: "visible",
    ease: Power2.easeInOut
  }, 0)
  .to(".play-close", 1, {
    opacity: 1,
    ease: Power2.easeInOut
  }, 0)
  .to(".play-perspective", 1, {
    xPercent: 0,
    scale: 1,
    ease: Power2.easeInOut
  }, 0)
  .to(".play-triangle", 1, {
    scaleX: 1,
    ease: ExpoScaleEase.config(2, 1, Power2.easeInOut)
  }, 0)
  .to(".play-triangle", 1, {
    rotationY: 0,
    ease: ExpoScaleEase.config(10, .01, Power2.easeInOut)
  }, 0)
  .to(".play-video", 1, {
    visibility: "visible",
    opacity: 1
  }, .5)
​
​
const button = document.querySelector(".play-button")
const backdrop = document.querySelector(".play-backdrop")
const close = document.querySelector(".play-close")
​
button.addEventListener("mouseover", () => rotateTL.play())
button.addEventListener("mouseleave", () => rotateTL.reverse())
button.addEventListener("click", () => openTL.play())
backdrop.addEventListener("click", () => openTL.reverse())
close.addEventListener("click", e => {
  e.stopPropagation()
  openTL.reverse()
})