$(document).ready(function () {
    var audioChunks = []; // Array to store audio chunks

    $('#recordBtn').on('click', function () {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function (stream) {
                var mediaRecorder = new MediaRecorder(stream);
                var startTime = Date.now(); // Record start time
                var duration = 7000; // Duration of recording in milliseconds
                var updateInterval = 100; // Update interval for progress bar in milliseconds

                // Show progress bar
                $('#progressBar').show();

                // Start recording
                mediaRecorder.start();

                // Update progress bar during recording
                var intervalId = setInterval(function () {
                    var elapsedTime = Date.now() - startTime;
                    var progress = (elapsedTime / duration) * 100; // Calculate progress percentage

                    // Update progress bar width
                    $('#progressBarInner').width(progress + '%');

                    // Change progress bar color based on progress
                    if (progress < 50) {
                        $('#progressBarInner').removeClass('bg-warning bg-danger').addClass('bg-info');
                    } else if (progress < 75) {
                        $('#progressBarInner').removeClass('bg-info bg-danger').addClass('bg-warning');
                    } else {
                        $('#progressBarInner').removeClass('bg-info bg-warning').addClass('bg-danger');
                    }

                    // Check if recording duration exceeds specified time
                    if (elapsedTime >= duration) {
                        clearInterval(intervalId); // Stop updating progress bar
                        mediaRecorder.stop(); // Stop recording
                        $('#progressBar').hide(); // Hide progress bar

                        // Save recorded audio to a single blob
                        var audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

                        // Log audio blob before sending
                        console.log("Sending audio blob:", audioBlob);

                        // Display audio playback controls
                        $('#audioPlayback').show();
                        $('#audioPlayback').attr('src', URL.createObjectURL(audioBlob));

                        // Send recorded audio to the server for transcription
                        var formData = new FormData();
                        formData.append('audio', audioBlob, 'audio.wav');

                        // Log form data before sending
                        console.log("Sending form data:", formData);

                        $.ajax({
                            type: 'POST',
                            url: '/process_audio', // Corrected route
                            data: formData,
                            processData: false,
                            contentType: false,
                            success: function (response) {
                                $('#result').text(response.translated_text);
                            },
                            error: function () {
                                $('#result').text('Error: Recording failed');
                            }
                        });
                    }
                }, updateInterval);
                
                // Store recording data in chunks
                mediaRecorder.ondataavailable = function (event) {
                    audioChunks.push(event.data);
                    console.log("Received audio chunk:", event.data); // Log the received audio chunk
                };
            })
            .catch(function (err) {
                console.error('Error accessing microphone:', err);
            });
    });
});
