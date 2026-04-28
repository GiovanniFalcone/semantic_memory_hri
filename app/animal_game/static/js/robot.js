import { cardClickListener } from './gameplay.js';
import { language, state, url } from './state.js';
import { turnPopUp, hideTurnPopup, turnPopUpUser, hideTurnPopupUser, lookRobotPopup, hideRobotPopup } from './popups.js';
import { sendFlask } from './flask.js';


/** ******************************************************************************************************************
 *                                                   Robot turn                                                      *                                               
 * ******************************************************************************************************************* 
 * */ 

document.addEventListener("click", async function (e) {
    if (e.target.closest("#robot-button-math")) {
        // token from PLAYER → to ROBOT
        console.log("Token → ROBOT (math)");

        // if it's robot turn the user can't click cards
        const deckElement = document.querySelector('.deck');
        deckElement.classList.add('turn-blocked');

        // show popup
        turnPopUp("math");

        // wait one second
        await new Promise(r => setTimeout(r, 1000));

        // hide popup
        state.isRobotTurn = true;
        state.robotSubject = "math";
        await hideTurnPopup("math");
        console.log("popup hided.");

        // send token to flask after popup is closed
        console.log("Sending turn to flask...");
        sendFlask(
            "turn",
            { is_robot_turn: true, robot_type: "math" },
            "/turn_change"
        );
    }
});

document.addEventListener("click", async function(e) {
    if (e.target.closest("#robot-button-geography")) {
        // token from PLAYER → to ROBOT
        console.log("Token → ROBOT (geography)");

        // if it's robot turn the user can't click cards
        const deckElement = document.querySelector('.deck');
        deckElement.classList.add('turn-blocked');

        // show popup
        turnPopUp("geography");

        // wait one second
        await new Promise(r => setTimeout(r, 1000));

        // hide popup
        state.isRobotTurn = true;
        state.robotSubject = "geography";
        await hideTurnPopup("geography");
        console.log("popup hided.");

        // send token to flask after popup is closed
        console.log("Sending turn to flask...");
        sendFlask(
            "turn",
            { is_robot_turn: true, robot_type: "geography" },
            "/turn_change"
        );
    }
});

export function moveReceivedByRobot(msg) {
    const socket = io.connect(url);

    // IA card selection
    socket.on('AgentMove', handleRobotMoveEvent);
    // IA handover to human
    socket.on('AgentHandover', handleRobotHandover);

    function handleRobotMoveEvent(msg) {
        // get the card to click from robot
        const obj = JSON.parse(msg);
        const cardNameToClick = obj.card_clicked;
        const robot_type = obj.robot_type;
        state.robotSubject = robot_type;
        state.hasProvidedWrongCard = obj.wrong_card
        console.log("Robot (" + state.agentType + ") wants to click card: " + cardNameToClick);

        // now find the card element in the board
        const cardElement = document.querySelector(`.card[data-name="${cardNameToClick}"]:not(.match):not(.show)`);

        // click the card chosen
        cardClickListener(cardElement, cardNameToClick);
    }

    function handleRobotHandover(msg){
        setTimeout(() => {
            turnPopUpUser();
        }, 1000);
        
        setTimeout(() => {
            state.hasProvidedWrongCard = false;
            state.isRobotTurn = false;
            hideTurnPopupUser();
            const deckElement = document.querySelector('.deck');
            deckElement.classList.remove('turn-blocked');
        }, 1000);
        
        console.log("Token → Human");
    }
}


/** ******************************************************************************************************************
 *                                                     HINT                                                          *                                               
 * ******************************************************************************************************************* 
 * */ 

/**
 * This function makes sure that the suggestion is highlighted and 
 * that the suggestion is also written in the robot's speech-bubble.
 */
export function hintReceivedByRobot(msg) {
    const socket = io.connect(url);

    socket.on('Speech', handleSpeechEvent);
    socket.on('Feedback', handleFeedbackEvent);
    
    // Once the robot has finished uttering the suggestion, remove the pop-up 
    function handleSpeechEvent(msg) {
        const obj = JSON.parse(msg);
        const speech = obj.speech;
        const speech_status = obj.speech_status;
        const subject = obj.subject;

        console.log("speech event", speech, speech_status, subject);
        if(speech){
            if(speech_status == "uttering"){
                state.speechFinished = false;
                lookRobotPopup(subject);
            } else {
                state.speechFinished = true;
                hideRobotPopup(subject);
            }
        }
    }

    // if robot will provide a feedback, an alert will be shown (using robot icon on panel)
    function handleFeedbackEvent(msg) {
        console.log("feedback");

        // get message for speech-bubble
        if(language == 'italiano') 
            msg = '<span class="hint-text"> Sto per parlare! </span>';
        else 
            msg = 'span class="hint-text"> I\'m about to speak! </span>';

        // Show message near to robot icon if app is multithread
        const speechBubble = document.querySelector('.speech-bubble');
        speechBubble.innerHTML = msg;
        speechBubble.style.display = 'block';

        // Hide the speech bubble after 2.5 seconds
        setTimeout(() => {
            speechBubble.style.display = 'none';
        }, 2500);
    }
    
    function handleRobotHintEvent(msg) {
        const obj = JSON.parse(msg);
        const isRobotConnected = obj.action.isRobotConnected;

        if (isRobotConnected != false) {
            lookRobotPopup();
        } else {
            state.timeHint = 0;
        }

        setTimeout(applyHint, timeHint);

        function applyHint(){    
            const suggestion = obj.action.suggestion;
            const row = obj.action.position[0] - 1
            const col = obj.action.position[1] - 1

            console.log("suggestion", suggestion, row, col)

            // get message for speech-bubble
            msg = getMessageText(suggestion, row, col);

            // Show message near to robot icon if app is multithread
            document.querySelector('.speech-bubble').innerHTML = msg
            document.querySelector('.speech-bubble').style.display = 'block';

            // Highlight suggestion
            document.querySelectorAll(".card").forEach((card) => {
                if(card.classList.contains("flipInY") == true) //&& (turns + 1) % 2 != 0)
                    card.classList.remove('flipInY')

                if(card.classList.contains("match") == false && card.classList.contains("flipInY") == false 
                                                            && card.classList.contains("show") == false){
                    if(suggestion == "row"){
                        if(row == Math.floor(card.id/6))
                            card.classList.add('hint');
                    }

                    if(suggestion == "column"){
                        if(col == card.id % 6)
                            card.classList.add('hint');
                        }
                    }

                    if(suggestion == "card"){
                        if(row == Math.floor(card.id/6) && (col == card.id % 6))
                            card.classList.add('hint');
                    }
            });
        }
    }
}

/**
 * This function will return the sentence (ita or english, based on the chosen language)
 * that will be showed in the speech-bubble
 */
export function getMessageText(suggestion, row, col){
    if(language == 'italiano'){
        let textHint = '';
        if (suggestion == "row") 
            textHint = '<span class="hint-text">Prova la riga ' + (row + 1) + '!</span>';
        else if (suggestion == "column")
            textHint = '<span class="hint-text">Prova la colonna ' + (col + 1) + '!</span>';
        else
            textHint = '<span class="hint-text">Prova in riga ' + (row + 1) + ' e colonna ' + (col + 1) + '!</span>';

        return textHint
    } else {
        // inglese
        let textHint = '';
        if (suggestion == "row") 
            textHint = '<span class="hint-text">Try the row ' + (row + 1) + '!</span>';
        else if (suggestion == "column")
            textHint = '<span class="hint-text">Try the column ' + (col + 1) + '!</span>';
        else
            textHint = '<span class="hint-text">Try the card in row ' + (row + 1) + ' and column ' + (col + 1) + '!</span>';

        return textHint
    }
}