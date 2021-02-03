# Setup TTS
git clone https://github.com/Edresson/TTS -b dev-gst-embeddings
#apt-get install espeak
cd TTS/
pip install -r requirements.txt
python setup.py develop
cd ../

# Get model checkpoint
wget -c -q --show-progress -O ./TTS-checkpoint.zip https://github.com/Edresson/TTS/releases/download/v1.0.0/Checkpoints-TTS-MultiSpeaker-Jia-et-al-2018-with-GST-CorentinJ_SpeakerEncoder_and_DDC.zip
unzip ./TTS-checkpoint.zip
wget https://github.com/Edresson/TTS/releases/download/v1.0.0/gst-style-example.wav
