# Install gdown
pip install gdown

# Install espeak from pip
pacman -S espeak

# Get models
gdown --id 1dntzjWFg7ufWaTaFy80nRz-Tu02xWZos -O tts_model.pth.tar
gdown --id 18CQ6G6tBEOfvCHlPqP8EBI4xWbrr9dBc -O config.json
gdown --id 1Ty5DZdOc0F7OTGj9oJThYbL5iVu_2G0K -O vocoder_model.pth.tar
gdown --id 1Rd0R_nRCrbjEdpOwq6XwZAktvugiBvmu -O config_vocoder.json
gdown --id 11oY3Tv0kQtxK_JPgxrfesa99maVXHNxU -O scale_stats.npy

# Get TTS
git clone https://github.com/mozilla/TTS
cd TTS
git checkout b1935c97
pip install -r requirements.txt
python setup.py install
cd ..
