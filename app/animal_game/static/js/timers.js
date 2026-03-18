// timer.js
// =============================
// Game Timer and Pair Timer
// =============================

import { state } from './state.js';

export function twoDigits(number) {
    return (number < 10 ? '0' : '') + number;
}

export function myTimer() {
    state.mySeconds++
    if (state.mySeconds >= 60) {
        state.mySeconds = 0;
        state.myMinutes++;
    }
    myRunTimer();
}

export function myRunTimer() {
    state.myT = setTimeout(myTimer, 1000);
}

export function timer() {
    state.seconds++;
    if (state.seconds >= 60) {
        state.seconds = 0;
        state.minutes++;
    }

    updateTimer();
    runTimer();
}

export function runTimer() {
    state.t = setTimeout(timer, 1000);
}

export function resetTimer() {
    stopTimer();
    state.seconds = 0;
    state.minutes = 0;
    updateTimer();
}

export function myResetTimer() {
    myStopTimer();
    state.mySeconds = 0;
    state.myMinutes = 0;
}

export function updateTimer() {
    document.querySelectorAll(".timer-seconds").forEach(item => item.textContent = twoDigits(state.seconds));
    document.querySelectorAll(".timer-minutes").forEach(item => item.textContent = twoDigits(state.minutes));
}

export function stopTimer() {
    clearTimeout(state.t);
}

export function myStopTimer() {
    clearTimeout(state.myT)
}