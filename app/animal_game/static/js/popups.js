
import { stopTimer, runTimer, myStopTimer, myRunTimer } from './timers.js';
import { state, language } from './state.js';
import { finishMsg, finishImg } from './config.js';

/**
 * Set a pop-up when robot provide a hint.
 * In this way the user will look to the robot and they will not be able to click any card.
 */
export function lookRobotPopup(subject) {
    var textContent = ''

    if (language === 'en') {
        textContent = 'Hey, it\'s robot turn now!';
    } 

    showPopup('curiosity-popup-' + subject, textContent);
}

/**
 * Hide pop-up when robot has finished to speak.
 */
export function hideRobotPopup(subject) {
    return hidePopup(
        'curiosity-popup-' + subject,
        'popup-' + subject
    );
}

/**
 * When the game is finished it shows a pop-up/form 
 * where the user can see the result of the game and answer the questions in the form.
 */
export function congrats() {
    stopTimer();
    myStopTimer()
    const popup = document.getElementById('congrats-popup');

    // html elements to update
    const title = popup.querySelector('label[for="formText"] h1');
    const image = popup.querySelector('#congrats-image');

    
    // msg and image based on the number of stars
    title.textContent = finishMsg[state.numStars - 1] + '!'; 
    image.src = `static/images/${finishImg[state.numStars - 1]}.svg`;

    // show the pop-up
    setTimeout(() => {
        popup.style.display = 'flex';
    }, 500);
};

/**
 * 
 */

export function turnPopUp(subject) {
    var textContent = ''

    if (language === 'en') {
        textContent = 'Hey, it\'s robot turn now!';
    } 

    showPopup('robotmove-popup-' + subject, textContent);
}

export function hideTurnPopup(subject) {
    return hidePopup(
        'robotmove-popup-' + subject,
        'popup-' + subject
    );
}

export function turnPopUpUser() {
    var textContent = ''

    if (language === 'en') {
        textContent = 'Hey, it\'s your turn now!';
    } 

    showPopup('usermove-popup', textContent);
}

export function hideTurnPopupUser() {
    hidePopup('usermove-popup', 'popup-turnPlayer');
}

export function showPopup(popupId, textContent) {
    stopTimer();
    myStopTimer();

    const popup = document.getElementById(popupId);

    if (textContent !== '') {
        const title = popup.querySelector('.popup-title');
        title.textContent = textContent;
    }

    setTimeout(() => {
        popup.style.display = 'flex';
    }, 10);
}

export function hidePopup(popupId, cardClass) {
    return new Promise(resolve => {
        const popup = document.getElementById(popupId);
        const card = popup.querySelector(`.${cardClass}`);

        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease';
            card.style.opacity = '0';

            popup.style.backgroundColor = 'transparent';
            popup.style.backdropFilter = 'none';

            setTimeout(() => {
                popup.style.display = 'none';
                card.style.opacity = '1';

                popup.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
                popup.style.backdropFilter = 'blur(8px)';
                
                console.log("finito")
                resolve(); // done
            }, 200);

            stopTimer();
            myStopTimer();

            runTimer();
            myRunTimer();
        }, 1000);
    });
}