#!/usr/bin/env python3

import numpy
import pyaudio
import random
import time
import curses
import tkinter

DEBUG = False
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
STREAM_FORMAT = pyaudio.paFloat32
# CURRENT_MODE = 'OFF'  # Options: ON, OFF, STOPPING

frequency_map = {9: 440,        # A
                 10: 466.16,    # A# / Bb
                 11: 493.88,    # B
                 0: 523.25,     # C
                 1: 554.37,     # C# / Db
                 2: 587.33,     # D
                 3: 622.25,     # D# / Eb
                 4: 659.26,     # E
                 5: 698.46,     # F
                 6: 739.99,     # F# / Gb
                 7: 783.99,     # G
                 8: 830.61}     # G# / Ab


class Oscillator:
    """
    A sine wave oscillator.
    """
    def __init__(self, frequency, sample_rate, starting_amp=0,
                 start_mode='OFF'):
        """
        Args:
            frequency (float):
            sample_rate (int):
            starting_amp (float):
            start_mode (str): legal values: ON, OFF, STOPPING
        """
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.last_played_sample = 0
        self.play_mode = start_mode  # legal values: ON, OFF, STOPPING

        # Build self.wave chunk, a numpy array of a full period of the wave
        self.cache_length = int(round((self.sample_rate / self.frequency) * 10))
        factor = float(self.frequency) * (numpy.pi * 2) / self.sample_rate
        self.wave_cache = numpy.sin(numpy.arange(self.cache_length) * factor)

        # Set up amplitude
        if starting_amp:
            self._raw_amp = starting_amp
        else:
            self._raw_amp = 0
        self.amp_drift_target = 0
        self.amp_baseline = 0.01
        self.amp_change_rate = 0.0001

    @property
    def amp(self):
        """
        float: Adjusted amplitude. Negative values return 0
        """
        if self._raw_amp < 0:
            return 0
        else:
            return self._raw_amp

    @amp.setter
    def amp(self, value):
        self._raw_amp = value

    def step_amp(self, new_amp):
        if self.play_mode == 'OFF':
            self.amp = 0
        else:
            if self.play_mode == 'ON':
                if random.randint(0, 1000) == 0:
                    self.amp_drift_target = random.uniform(0, 1)
                    if DEBUG:
                        print("Moving drift target to %f" %
                              self.amp_drift_target)
                target_amplitude = (((new_amp - 1) * -1) +
                                    self.amp_drift_target) / 2
            elif self.play_mode == 'STOPPING':
                target_amplitude = -1
            else:
                raise ValueError("Oscillator.play_mode of %s is not valid." %
                                 str(self.play_mode))
            difference = target_amplitude - self.amp
            delta = difference / 500
            if self.amp > 0.2:
                delta -= 0.01
            self.amp += delta

    def get_samples(self, sample_count):
        """
        Fetch a number of samples from self.wave_cache

        Args:
            sample_count (int): Number of samples to fetch

        Returns: ndarray
        """
        rolled_array = numpy.roll(self.wave_cache, -1 * self.last_played_sample)
        full_count, remainder = divmod(sample_count, self.cache_length)
        final_subarray = rolled_array[:remainder]
        return_array = numpy.concatenate((numpy.tile(rolled_array, full_count),
                                         final_subarray))

        self.last_played_sample = self.last_played_sample + remainder
        if self.last_played_sample > self.cache_length:
            self.last_played_sample -= self.cache_length
        return return_array * self.amp


def find_amplitude(chunk):
    chunk = numpy.fromstring(chunk, numpy.float32)
    return abs(chunk.max()) + abs(chunk.min()) / 2


oscillators = [Oscillator(frequency_map[4] / 2.0,
                          SAMPLE_RATE, random.uniform(-3, 0)),
               Oscillator(frequency_map[4],
                          SAMPLE_RATE, random.uniform(-3, 0)),
               Oscillator(frequency_map[4] * 2.0,
                          SAMPLE_RATE, random.uniform(-3, 0))
               ]


def main_callback(in_data, frame_count, time_info, status):
    # Get amplitude of input
    in_amplitude = find_amplitude(in_data)
    subchunks = []
    for osc in oscillators:
        osc.step_amp(in_amplitude)
        subchunks.append(osc.get_samples(CHUNK_SIZE))
    # e1_chunk = e1_osc.get_samples(CHUNK_SIZE)  # * e1_amp.amplitude
    # e0_chunk = e0_osc.get_samples(CHUNK_SIZE)  # * (e0_amp.amplitude / 6)
    # e2_chunk = e2_osc.get_samples(CHUNK_SIZE)  # * (e2_amp.amplitude / 10)
    new_chunk = sum(subchunks)
    # Play sound
    return new_chunk.astype(numpy.float32).tostring(), pyaudio.paContinue

pa_host = pyaudio.PyAudio()
out_stream = pyaudio.Stream(pa_host, format=STREAM_FORMAT,
                            channels=1, rate=SAMPLE_RATE,
                            output=True, input=True,
                            frames_per_buffer=CHUNK_SIZE,
                            stream_callback=main_callback)
out_stream.start_stream()

# Initialize tkinter
tk_host = tkinter.Tk()

tk_host.geometry("300x100+300+300")
tk_host.resizable(0, 0)

main_note_text = ('This is the drone program for [PIECENAME].\n'
                  'The program starts with the oscillator paused.\n'
                  'See part for further instructions.')
main_note = tkinter.Label(tk_host, text=main_note_text, justify='left')
main_note.grid(row=0, column=0, columnspan=3, sticky='NE')

play_pause_text = tkinter.StringVar(tk_host, 'Play', 'Pause/Pause')


def pause_resume_action():
    for osc in oscillators:
        if osc.play_mode == 'ON':
            osc.play_mode = 'OFF'
            play_pause_text.set('Play')
        else:
            osc.play_mode = 'ON'
            play_pause_text.set('Pause')
            # Set amplitudes to negative numbers so it fades back in
            osc.amp = random.uniform(-3, 0)


def cue_p_action():
    for osc in oscillators:
        osc.play_mode = 'STOPPING'
        play_pause_text.set('PLAY')


def quit_action():
    out_stream.close()
    pa_host.terminate()
    quit()


def close_button():
    quit_action()
    tk_host.destroy()

tk_host.protocol('WM_DELETE_WINDOW', close_button)

pause_resume_button = tkinter.Button(tk_host, textvariable=play_pause_text,
                                     command=pause_resume_action)
pause_resume_button.grid(row=1, column=0, sticky='SW')
cue_p_button = tkinter.Button(tk_host, text="Cue P", command=cue_p_action)
cue_p_button.grid(row=1, column=1, sticky='S')
quit_button = tkinter.Button(tk_host, text="Quit", command=quit_action)
quit_button.grid(row=1, column=2, sticky='SE')

tk_host.mainloop()

while True:
    time.sleep(CHUNK_SIZE / SAMPLE_RATE)

out_stream.close()
pa_host.terminate()
