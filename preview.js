const viewer = document.getElementById('mascot');
const play = document.getElementById('play');
const restart = document.getElementById('restart');
const reset = document.getElementById('reset');
const timeline = document.getElementById('timeline');
const time = document.getElementById('time');
let ready = false;
viewer.addEventListener('load', () => {
  ready = true;
  document.getElementById('loading').hidden = true;
  for (const control of [play, restart, reset, timeline]) control.disabled = false;
  viewer.play();
});
viewer.addEventListener('error', () => {
  const notice = document.getElementById('notice');
  notice.hidden = false;
  notice.textContent = '3Dアニメーションを読み込めませんでした。ChromeまたはSafariでお試しください。';
  document.getElementById('loading').hidden = true;
});
play.addEventListener('click', () => {
  if (viewer.paused) { viewer.play(); play.textContent = '一時停止'; }
  else { viewer.pause(); play.textContent = '再生'; }
});
restart.addEventListener('click', () => { viewer.currentTime = 0; viewer.play(); play.textContent = '一時停止'; });
reset.addEventListener('click', () => {
  viewer.cameraOrbit = '0deg 78deg 3.1m';
  viewer.cameraTarget = '-.36m .76m 0m';
  viewer.fieldOfView = '36deg';
  viewer.jumpCameraToGoal();
});
timeline.addEventListener('input', () => {
  viewer.pause();
  viewer.currentTime = Number(timeline.value);
  play.textContent = '再生';
});
function updateTime() {
  if (ready) {
    timeline.value = viewer.currentTime;
    time.textContent = `${viewer.currentTime.toFixed(1)} / 10秒`;
  }
  requestAnimationFrame(updateTime);
}
requestAnimationFrame(updateTime);
