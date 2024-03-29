// Function to handle recording
function startRecording() {
    // Check if the browser supports MediaRecorder
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Request access to the user's microphone
        navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            // Create a new MediaRecorder instance
            var mediaRecorder = new MediaRecorder(stream);
            var chunks = [];

            // Start recording when the record button is clicked
            mediaRecorder.start();

            // Event listener for when data is available
            mediaRecorder.ondataavailable = function(e) {
                chunks.push(e.data);
            };

            // Event listener for when recording is stopped
            mediaRecorder.onstop = function() {
                // Combine the recorded chunks into a single Blob
                var blob = new Blob(chunks, { type: 'audio/wav' });

                // Create a URL for the Blob
                var audioURL = URL.createObjectURL(blob);

                // Send the recorded audio to the server for translation
                sendAudioForTranslation(blob);
            };

            // Stop recording after a specified duration (e.g., 7 seconds)
            setTimeout(function() {
                mediaRecorder.stop();
            }, 7000);
        })
        .catch(function(err) {
            console.log('The following error occurred: ' + err);
        });
    } else {
        console.log('MediaRecorder is not supported on this browser.');
    }
}

// Function to send recorded audio to the server for translation
function sendAudioForTranslation(audioData) {
    // Create a FormData object to send the audio data as multipart/form-data
    var formData = new FormData();
    formData.append('audio', audioData);

    // Send the FormData object to the server using fetch or XMLHttpRequest
    fetch('/translate', {
        method: 'POST',
        body: formData
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        // Handle the response from the server
        displayTranslatedText(data.translatedText);
        displayBill(data.billData);
        displayQRCode(data.qrCodeURL);
    })
    .catch(function(error) {
        console.error('Error:', error);
    });
}
