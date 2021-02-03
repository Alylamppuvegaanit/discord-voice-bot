import argparse
import json
# pylint: disable=redefined-outer-name, unused-argument
import os
import string
import time
import sys
import numpy as np

TTS_PATH = "../content/TTS"
# add libraries into environment
sys.path.append(TTS_PATH) # set this if TTS is not installed globally

import torch

from TTS.tts.utils.generic_utils import setup_model
from TTS.tts.utils.synthesis import synthesis
from TTS.tts.utils.text.symbols import make_symbols, phonemes, symbols
from TTS.utils.audio import AudioProcessor
from TTS.utils.io import load_config
from TTS.vocoder.utils.generic_utils import setup_generator


SPEAKER_JSON = 'speakers.json'
def setup():
    TEXT = ''
    OUT_PATH = 'tests-audios/'
    # create output path
    os.makedirs(OUT_PATH, exist_ok=True)

    SPEAKER_FILEID = None # if None use the first embedding from speakers.json

    # model vars 
    MODEL_PATH = 'best_model.pth.tar'
    CONFIG_PATH = 'config.json'

    # vocoder vars
    VOCODER_PATH = ''
    VOCODER_CONFIG_PATH = ''

    USE_CUDA = True


    # load the config
    C = load_config(CONFIG_PATH)
    C.forward_attn_mask = True

    # load the audio processor
    ap = AudioProcessor(**C.audio)

    # if the vocabulary was passed, replace the default
    if 'characters' in C.keys():
        symbols, phonemes = make_symbols(**C.characters)

    speaker_embedding = None
    speaker_embedding_dim = None
    num_speakers = 0
    # load speakers
    if SPEAKER_JSON != '':
        speaker_mapping = json.load(open(SPEAKER_JSON, 'r'))
        num_speakers = len(speaker_mapping)
        if C.use_external_speaker_embedding_file:
            if SPEAKER_FILEID is not None:
                speaker_embedding = speaker_mapping[SPEAKER_FILEID]['embedding']
            else: # if speaker_fileid is not specificated use the first sample in speakers.json
                choise_speaker = list(speaker_mapping.keys())[0]
                print(" Speaker: ",choise_speaker.split('_')[0],'was chosen automatically', "(this speaker seen in training)")
                speaker_embedding = speaker_mapping[choise_speaker]['embedding']
            speaker_embedding_dim = len(speaker_embedding)
            print(speaker_embedding_dim)

    # load the model
    num_chars = len(phonemes) if C.use_phonemes else len(symbols)
    model = setup_model(num_chars, num_speakers, C, speaker_embedding_dim)
    cp = torch.load(MODEL_PATH, map_location=torch.device('cpu'))
    model.load_state_dict(cp['model'])
    model.eval()

    if USE_CUDA:
        model.cuda()

    model.decoder.set_r(cp['r'])

    # load vocoder model
    if VOCODER_PATH!= "":
        VC = load_config(VOCODER_CONFIG_PATH)
        vocoder_model = setup_generator(VC)
        vocoder_model.load_state_dict(torch.load(VOCODER_PATH, map_location="cpu")["model"])
        vocoder_model.remove_weight_norm()
        if USE_CUDA:
            vocoder_model.cuda()
        vocoder_model.eval()
    else:
        vocoder_model = None
        VC = None

    # synthesize voice
    use_griffin_lim = VOCODER_PATH== ""

    if not C.use_external_speaker_embedding_file:
        if SPEAKER_FILEID.isdigit():
            SPEAKER_FILEID = int(SPEAKER_FILEID)
        else:
            SPEAKER_FILEID = None
    else:
        SPEAKER_FILEID = None

    return model, vocoder_model, C, USE_CUDA, ap, SPEAKER_FILEID, speaker_embedding

def tts(model, vocoder_model, text, CONFIG, use_cuda, ap, use_gl, speaker_fileid, speaker_embedding=None, gst_style=None):
    t_1 = time.time()
    waveform, _, _, mel_postnet_spec, _, _ = synthesis(model, text, CONFIG, use_cuda, ap, speaker_fileid, gst_style, False, CONFIG.enable_eos_bos_chars, use_gl, speaker_embedding=speaker_embedding)
    if CONFIG.model == "Tacotron" and not use_gl:
        mel_postnet_spec = ap.out_linear_to_mel(mel_postnet_spec.T).T
    if not use_gl:
        waveform = vocoder_model.inference(torch.FloatTensor(mel_postnet_spec.T).unsqueeze(0))
    if use_cuda and not use_gl:
        waveform = waveform.cpu()
    if not use_gl:
        waveform = waveform.numpy()
    waveform = waveform.squeeze()
    rtf = (time.time() - t_1) / (len(waveform) / ap.sample_rate)
    tps = (time.time() - t_1) / len(waveform)
    print(" > Run-time: {}".format(time.time() - t_1))
    print(" > Real-time factor: {}".format(rtf))
    print(" > Time per step: {}".format(tps))
    return waveform


model, vocoder_model, CONFIG, use_cuda, ap, speaker_fileid, speaker_embedding = setup()

def getSpeaker(choice=4):
    # VCTK speakers not seen in training (new speakers)
    VCTK_test_Speakers = ["p225", "p234", "p238", "p245", "p248", "p261", "p294", "p302", "p326", "p335", "p347"]

    # VCTK speakers seen in training
    VCTK_train_Speakers = ['p244', 'p300', 'p303', 'p273', 'p292', 'p252', 'p254', 'p269', 'p345', 'p274', 'p363', 'p285', 'p351', 'p361', 'p295', 'p266', 'p307', 'p230', 'p339', 'p253', 'p310', 'p241', 'p256', 'p323', 'p237', 'p229', 'p298', 'p336', 'p276', 'p305', 'p255', 'p278', 'p299', 'p265', 'p267', 'p280', 'p260', 'p272', 'p262', 'p334', 'p283', 'p247', 'p246', 'p374', 'p297', 'p249', 'p250', 'p304', 'p240', 'p236', 'p312', 'p286', 'p263', 'p258', 'p313', 'p376', 'p279', 'p340', 'p362', 'p284', 'p231', 'p308', 'p277', 'p275', 'p333', 'p314', 'p330', 'p264', 'p226', 'p288', 'p343', 'p239', 'p232', 'p268', 'p270', 'p329', 'p227', 'p271', 'p228', 'p311', 'p301', 'p293', 'p364', 'p251', 'p317', 'p360', 'p281', 'p243', 'p287', 'p233', 'p259', 'p316', 'p257', 'p282', 'p306', 'p341', 'p318']


    num_samples_speaker = 1 # In theory the more samples of the speaker the more similar to the real voice it will be!
    # get embedding
    Speaker_choise = VCTK_train_Speakers[choice] # choise one of training speakers
    # load speakers
    if SPEAKER_JSON != '':
        speaker_mapping = json.load(open(SPEAKER_JSON, 'r'))
        if CONFIG.use_external_speaker_embedding_file:
            speaker_embeddings = []
            for key in list(speaker_mapping.keys()):
                if Speaker_choise in key:
                    if len(speaker_embeddings) < num_samples_speaker:
                        speaker_embeddings.append(speaker_mapping[key]['embedding'])
            # takes the average of the embedings samples of the announcers
            speaker_embedding = np.mean(np.array(speaker_embeddings), axis=0).tolist()
    return speaker_embeddings
