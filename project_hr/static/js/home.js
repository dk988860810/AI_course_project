const loginLink = document.getElementById('login-link');

// 添加點擊事件監聽器
loginLink.addEventListener('click', function(event) {
    event.preventDefault(); // 阻止默認連結行為
    window.location.href = '/templates/login.html'; // 跳轉到登錄頁面
});
​
// 初始化動畫
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



// 添加平滑滾動效果
$('a[href*="#"]').on('click', function (e) {
  e.preventDefault();
  $('html, body').animate(
    {
      scrollTop: $($(this).attr('href')).offset().top,
    },
    500,
    'linear'
  );
});

// 添加視差效果
$(window).on('scroll', function () {
  const scrollPos = $(this).scrollTop();
  $('.hero').css('background-position', `center ${-(scrollPos * 0.5)}px`);
});

// 添加動畫效果
$(window).on('load', function () {
  $('.fade-in').addClass('animate__animated animate__fadeIn');
});

// 添加懸停效果
$('.feature-card').on('mouseenter', function () {
  $(this).addClass('animate__animated animate__pulse');
});

$('.feature-card').on('mouseleave', function () {
  $(this).removeClass('animate__animated animate__pulse');
});
