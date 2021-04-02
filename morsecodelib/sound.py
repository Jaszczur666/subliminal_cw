# -*- coding: utf-8 -*-
"""
Make sounds or light pulses from Morse code data
"""

import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import time
from array import array
import math
import numpy as np
import pyaudio

try:
    import pygame
except ImportError:
    pygame = None
from six.moves import xrange

from morsecodelib import config
from morsecodelib import text
def koperta(x,w):
    #print(x)
#    w=15
    return np.tanh(w*x)+np.tanh(w*(1-x))-1.0
class MorsePlayer(object):
    """
    Take text and render it as something.

    Use subclasses to choose sound vs. laser vs. whatever.
    """

    def text_to_sound(self, message_text):
        """
        Play a text string as Morse code through speakers
        """
        message_morse = text.text_to_code(message_text)
        for word in message_morse.split('  '):
            self.play_word(word)

    def play_word(self, word):
        """
        Plays a Morse code word through the speakers
        This does all the official timing.
        """
        p = pyaudio.PyAudio()
        volume = 1     # range [0.0, 1.0]
        fs = config.config.SAMPLE_RATE# sampling rate, Hz, must be integer
        w=15
        f = config.config.FREQUENCY
        x=np.arange(fs*config.config.DIT_DURATION)
        xd=np.arange(fs*config.config.DAH_DURATION)
        nic=np.zeros(int(config.config.DIT_DURATION*fs)).astype(np.float32)
        dit =(koperta(x/(config.config.DIT_DURATION*fs),w)*np.sin(2*np.pi*x*(f/fs))).astype(np.float32)
        dah=(koperta(xd/(config.config.DAH_DURATION*fs),3*w)*np.sin(2*np.pi*xd*(f/fs))).astype(np.float32)
        a=np.zeros(1).astype(np.float32)
        for letter in word.split(' '):
            for char in letter:
                if char == '.':
                    a=np.append(a,dit)
                elif char == '-':
                    a=np.append(a,dah)
                a=np.append(a,nic)
            a=np.append(a,nic)
            a=np.append(a,nic)
            a=np.append(a,nic)
        time.sleep(config.config.DIT_DURATION * 7)
        stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=fs,
                output=True)

# play. May repeat with different volume values (if done interactively) 
#np.savetxt('my_filenmame', sumasamples, fmt='%4.6f', delimiter=' ')
        stream.write(volume*a.tobytes())
        stream.stop_stream()
        stream.close()
        p.terminate()

    def play_dit(self):
        """
        Play one dit
        """
        self._play_tone(config.config.DIT_DURATION)

    def play_dah(self):
        """
        Play one dah
        """
        self._play_tone(config.config.DAH_DURATION)

    def _play_tone(self, durationInSeconds):
        raise NotImplementedError

    def stop(self):
        pass


class MorseSoundPlayer(MorsePlayer):
    """
    Makes audible tones with speaker.
    """

    def __init__(self):
        """
        Set up the mixer and tone.

        Mixer buffer should be small to minimize latency.
        """
        pygame.mixer.pre_init(config.config.SAMPLE_RATE,
                              size=-16, channels=1, buffer=512)
        pygame.init()
        self.tone = ToneSound(frequency=config.config.FREQUENCY, volume=.5)

    def _play_tone(self, durationInSeconds):
        
        num_periods = int(durationInSeconds * config.config.FREQUENCY)
        duration = num_periods / config.config.FREQUENCY

        self.tone.play(-1)  # the -1 means to loop the sound
        time.sleep(duration)
        self.tone.stop()

    def stop(self):
        pygame.quit()


if pygame:
    class ToneSound(pygame.mixer.Sound):
        def __init__(self, frequency, volume):
            self.frequency = frequency
            pygame.mixer.Sound.__init__(self, self.build_samples())
            self.set_volume(volume)

        def build_samples(self, shape='sine'):
            mixer_frequency, mixer_format, _channels = pygame.mixer.get_init()
            period = int(round(mixer_frequency / self.frequency))

            amplitude = 2 ** (abs(mixer_format) - 1) - 1
            if shape == 'sine':
                samples = self.sine_wave(amplitude, period)
            elif shape == 'square':
                samples = self.square_wave(amplitude, period)

            return samples

        def _init_samples(self, period):
            return array("h", [0] * period)
        def sine_wave(self, amplitude, period):
            samples = self._init_samples(period)
            for time in xrange(period):
                samples[time] = int(
                    amplitude * math.sin(2 * math.pi * time / period))
            return samples

        def square_wave(self, amplitude, period):
            samples = self._init_samples(period)
            for time in xrange(period):
                if time < period / 2:
                    samples[time] = amplitude
                else:
                    samples[time] = -amplitude
            return samples


if __name__ == '__main__':
    morse_sound = MorseSoundPlayer()
    morse_sound.text_to_sound('KG7QDZ')
