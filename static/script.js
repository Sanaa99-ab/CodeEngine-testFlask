$(document).ready(function() {
    $('#convert-button').click(function() {
        let text = $('#text-to-read').val();
        let language = $('#language-select').val();
        $.ajax({
            type: 'POST',
            url: '/convert',
            contentType: 'application/json',
            data: JSON.stringify({text: text, voice: language}),
            success: function(response) {
                $('#audio').attr('src', response.audio_file);
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
            }
        });
    });

    $('#stop-button').click(function() {
        $('#audio').trigger('pause');
    });

    $('#download-button').click(function() {
        let audioSrc = $('#audio').attr('src');
        if (audioSrc) {
            let link = document.createElement('a');
            link.href = audioSrc;
            link.download = 'output.wav';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    });

    $('#upload-file').change(function() {
        let file = this.files[0];
        let reader = new FileReader();
        reader.onload = function(event) {
            let text = event.target.result;
            $('#text-to-read').val(text);
        };
        reader.readAsText(file);
    });
});
