#!/usr/bin/env python

import numpy
import pyaudio
import random
import time
import sys

from chance.rand import weighted_rand

# Make sure we're running the right version of Python
if sys.version_info[0] == 3:
    import tkinter as tk
    from tkinter import messagebox
else:
    print("This program must be run on Python 3, make sure Python 3 \n"
          "is on your system path, see the Python website for help.")
    quit(1)


SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
STREAM_FORMAT = pyaudio.paFloat32

frequency_map = {9: 440,  # A
                 10: 466.16,  # A# / Bb
                 11: 493.88,  # B
                 0: 523.25,  # C
                 1: 554.37,  # C# / Db
                 2: 587.33,  # D
                 3: 622.25,  # D# / Eb
                 4: 659.26,  # E
                 5: 698.46,  # F
                 6: 739.99,  # F# / Gb
                 7: 783.99,  # G
                 8: 830.61}  # G# / Ab


class Oscillator:
    """
    A sine wave oscillator.
    """

    def __init__(self, frequency, sample_rate,
                 amp_factor=1, starting_amp=0,
                 start_mode='OFF'):
        """
        Args:
            frequency (float):
            sample_rate (int):
            starting_amp (float):
            amp_factor (float):
            start_mode (str): legal values: ON, OFF, STOPPING
        """
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.last_played_sample = 0
        self.play_mode = start_mode  # legal values: ON, OFF, STOPPING

        # Build self.wave chunk, a numpy array of a full period of the wave
        self.cache_length = round(self.sample_rate / self.frequency)
        factor = self.frequency * (numpy.pi * 2) / self.sample_rate
        self.wave_cache = numpy.sin(numpy.arange(self.cache_length) * factor)

        # Set up amplitude
        self._raw_amp = starting_amp
        self.amp_factor = amp_factor
        self.amp_drift_target_weights = [
            (-0.3, 0), (0.1, 12), (0.2, 4), (0.3, 0)]
        self.amp_drift_target = 0
        self.amp_change_rate_weights = [(0.0001, 100), (0.001, 5), (0.01, 1)]
        self.amp_change_rate = 0.000001
        self.amp_move_freq_weights = [(0.001, 10), (0.01, 2)]
        self.amp_move_freq = 0.0015

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

    def refresh_amp_elements(self):
        self.amp_move_freq = weighted_rand(self.amp_move_freq_weights)
        self.amp_drift_target = weighted_rand(self.amp_drift_target_weights)
        self.amp_change_rate = weighted_rand(self.amp_change_rate_weights)

    def step_amp(self):
        if self.play_mode == 'OFF':
            self.amp = 0
        else:
            if self.play_mode == 'ON':
                # Roll for a chance to change the drift target and change rate
                if random.uniform(0, 1) < self.amp_move_freq:
                    self.refresh_amp_elements()
                # step the amplitude
                # target_amplitude = (((input_amp - 1) * -1) +
                #                     self.amp_drift_target)
                target_amplitude = self.amp_drift_target
            elif self.play_mode == 'STOPPING':
                self.amp_change_rate = 0.00015
                target_amplitude = -1
            else:
                raise ValueError

            difference = target_amplitude - self.amp
            delta = self.amp_change_rate * numpy.sign(difference)
            if self.amp > 0.5:
                delta -= 0.001
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
        return return_array * (self.amp * self.amp_factor)


def find_amplitude(chunk):
    chunk = numpy.fromstring(chunk, numpy.float32)
    return abs(chunk.max()) + abs(chunk.min()) / 2


pitches = [
    frequency_map[4] / 2.0,
    frequency_map[4],
    frequency_map[4] * 2.0
    ]

oscillators = [Oscillator(freq, SAMPLE_RATE,
                          1, random.uniform(-8, 0))
               for freq in pitches
               ]


def main_callback(in_data, frame_count, time_info, status):
    # Get amplitude of input
    # in_amplitude = find_amplitude(in_data)
    subchunks = []
    for osc in oscillators:
        osc.step_amp()
        subchunks.append(osc.get_samples(CHUNK_SIZE))
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
tk_host = tk.Tk()
tk_host.wm_title('"the second hand somehow ..." drone program')

tk_host.geometry("400x140+300+300")
tk_host.resizable(0, 0)

main_note_text = (
    'This is the electronic drone program for '
    '"the second hand somehow different this time around." '
    'The program starts with the oscillator paused. '
    'When the conductor gives Cue A, press \'Play.\' '
    'Once \'Play\' is pressed for the first time, a time in the '
    'bottom left corner will start to help you stay oriented '
    'in regards to cue timing. '
    'See your part for further instructions.')
main_note = tk.Label(tk_host, text=main_note_text,
                     justify='left', wraplength=380)
main_note.grid(row=0, column=0, columnspan=4, sticky='NE')

play_pause_text = tk.StringVar(tk_host, 'Play', 'Pause/Pause')

timer_string = tk.StringVar(tk_host, '0:00', 'Timer')
timer_label = tk.Label(tk_host, textvariable=timer_string)
timer_label.grid(row=2, column=0, sticky='SW')

start_time = tk.DoubleVar(tk_host, 0, 'start_time')


def print_amps():
    for osc in oscillators:
        bar_length = int((osc.amp / 1) * 100)
        print('{0}: {1}'.format(osc.frequency, '.' * bar_length))
    print('============================================')


def increment_timer():
    if tk_host.getvar('start_time') == 0:
        tk_host.setvar('start_time', time.time())
    elapsed = int(time.time() - tk_host.getvar('start_time'))
    minutes, seconds = divmod(elapsed, 60)
    minutes = str(minutes)
    seconds = str(seconds)
    if len(seconds) == 1:
        seconds = '0%s' % seconds
    display_time = "{0}:{1}".format(minutes, seconds)
    timer_string.set(display_time)

    print_amps()

    tk_host.after(1000, increment_timer)


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
            if tk_host.getvar('start_time') == 0:
                increment_timer()


def fade_out_action():
    for osc in oscillators:
        osc.play_mode = 'STOPPING'
        play_pause_text.set('Play')


def timer_reset_action():
    tk_host.setvar('start_time', time.time())


def quit_action():
    # Confirm that we really want to quit
    if not messagebox.askyesno(
            'Quit?', 'Are you sure you want to quit?'):
        return False
    out_stream.close()
    pa_host.terminate()
    quit()


def close_button():
    if not quit_action():
        return
    tk_host.destroy()


tk_host.protocol('WM_DELETE_WINDOW', close_button)

pause_resume_button = tk.Button(tk_host, textvariable=play_pause_text,
                                command=pause_resume_action)
pause_resume_button.grid(row=1, column=0, sticky='SW')
fade_out_button = tk.Button(tk_host, text="Cue P", command=fade_out_action)
fade_out_button.grid(row=1, column=1, sticky='S')
timer_reset_button = tk.Button(tk_host, text="Reset Timer",
                               command=timer_reset_action)
timer_reset_button.grid(row=1, column=2, sticky='S')
quit_button = tk.Button(tk_host, text="Quit", command=quit_action)
quit_button.grid(row=1, column=3, sticky='SE')

tk_host.mainloop()

while True:
    time.sleep(CHUNK_SIZE / SAMPLE_RATE)

# This shouldn't be reachable, but just in case, to prevent a
# runaway pyaudio process ...
out_stream.close()
pa_host.terminate()
