#!/usr/bin/env python3

import numpy
import pyaudio
import random
import time
import curses
import tkinter

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
STREAM_FORMAT = pyaudio.paFloat32
IS_PAUSED = False

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
    def __init__(self, frequency, sample_rate):
        """
        Args:
            frequency (float):
            sample_rate (int):
        """
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.last_played_sample = 0

        # Build self.wave chunk, a numpy array of a full period of the wave
        self.cache_length = int(round((self.sample_rate / self.frequency) * 10))
        factor = float(self.frequency) * (numpy.pi * 2) / self.sample_rate
        self.wave_cache = numpy.sin(numpy.arange(self.cache_length) * factor)
        # self.wave_cache[-1] = 0

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
        return return_array


class WaveAmplitude:

    baseline = 0.01
    change_rate = 0.0001

    def __init__(self, starting_amplitude=None):
        if starting_amplitude is None:
            self._raw_amplitude = 0
        else:
            self._raw_amplitude = starting_amplitude
        self.drift_target = 0

    @property
    def amplitude(self):
        """
        float: Adjusted amplitude. Negative values return 0
        """
        if self._raw_amplitude < 0:
            return 0
        else:
            return self._raw_amplitude

    @amplitude.setter
    def amplitude(self, value):
        self._raw_amplitude = value

    def step(self, new_amplitude):
        # print(new_amplitude)
        if random.randint(0, 1000) == 0:
            self.drift_target = random.uniform(0, 1)
            # print("Moving drift target to {0}".format(self.drift_target))
        target_amplitude = (((new_amplitude - 1) * -1) + self.drift_target) / 2
        difference = (target_amplitude) - self._raw_amplitude
        delta = difference / 500
        if self._raw_amplitude > 0.2:
            delta -= 0.01
        self._raw_amplitude += delta


def find_amplitude(chunk):
    chunk = numpy.fromstring(chunk, numpy.float32)
    return abs(chunk.max()) + abs(chunk.min()) / 2


e1_osc = Oscillator(frequency_map[4], SAMPLE_RATE)
e2_osc = Oscillator(frequency_map[4] * 2.0, SAMPLE_RATE)
e0_osc = Oscillator(frequency_map[4] / 2.0, SAMPLE_RATE)

e0_amp = WaveAmplitude(random.uniform(-3, 0))
e1_amp = WaveAmplitude(random.uniform(-3, 0))
e2_amp = WaveAmplitude(random.uniform(-3, 0))


def main_callback(in_data, frame_count, time_info, status):
    if IS_PAUSED:
        # Return an empty chunk
        new_chunk = numpy.zeros(frame_count, numpy.float32)
        return new_chunk.astype(numpy.float32).tostring(), pyaudio.paContinue
    # Get amplitude of input
    in_amplitude = find_amplitude(in_data)
    e1_amp.step(in_amplitude)
    e2_amp.step(in_amplitude)
    e0_amp.step(in_amplitude)
    e1_chunk = e1_osc.get_samples(CHUNK_SIZE) * e1_amp.amplitude
    e0_chunk = e0_osc.get_samples(CHUNK_SIZE) * (e0_amp.amplitude / 6)
    e2_chunk = e2_osc.get_samples(CHUNK_SIZE) * (e2_amp.amplitude / 10)
    new_chunk = e1_chunk + e2_chunk + e0_chunk
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
# TODO: Use tk instead of curses
tk_host = tkinter.Tk()
tk_host.geometry("100x100+300+300")
tk_host.mainloop()
# window.
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.nodelay(0)

while True:  # Try changing to while True:
    time.sleep(CHUNK_SIZE / SAMPLE_RATE)
    # Check for input
    key = stdscr.getch()
    if key == 32:
        IS_PAUSED = True
        stdscr.clear()
        stdscr.addstr(0, 0, 'Drone paused. Press [Space bar] to resume.')
        stdscr.refresh()
        key = -1
        while not key == 32:
            time.sleep(0.1)
            key = stdscr.getch()
            stdscr.refresh()
        # Set amplitudes to negative numbers so it fades back in
        e0_amp.amplitude = random.uniform(-3, 0)
        e1_amp.amplitude = random.uniform(-3, 0)
        e2_amp.amplitude = random.uniform(-3, 0)
        stdscr.clear()
        stdscr.addstr(0, 0, 'Drone active. Press [Space bar] to pause.')
        stdscr.refresh()
        IS_PAUSED = False
    if key == 27:
        curses.endwin()
        break

out_stream.close()
pa_host.terminate()
