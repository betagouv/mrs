import { CountUp } from 'countup.js';

const countUpOptions = {
  separator: ' ',
  decimal: ',',
};

window.onload = function () {
  let countUp = new CountUp('test', countUpVal, countUpOptions);
  if (!countUp.error) {
    countUp.start();
  } else {
    console.error(countUp.error);
  }
};
