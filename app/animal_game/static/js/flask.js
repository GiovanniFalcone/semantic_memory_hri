// flask.js
// =============================
// This file contains functions to send data to the Flask server
// =============================

import { id_player } from './state.js';

// generic function to send data to flask using specified route
export function sendFlask(flag, data, route){
    console.log("Request by", route)
    fetch(route + "/" + id_player, {
        headers : {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        method : 'POST',
        body : JSON.stringify( {
          [flag]: data
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Data received", data)
    })
    .catch(function(error) {
        console.log(error);
    });  
}