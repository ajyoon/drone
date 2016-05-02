#!/usr/bin/env python

from .network import Network
from .nodes import Value, WeightListNode


def piano_events_network():
    """
    Constructs and returns a network with two states: 1 (play) and 0 (don't play)
    Designed so that, when passed to document_tools.pdf_scribe, 'don't play' results in a space equal to the
    global font size (shared.Globals.FontSize)
    :return: instance of chance.network.Network
    """
    network = Network()
    dense_play = Value(1)
    play = Value(1)
    light_play = Value(1)
    light_rest = Value(0)
    rest = Value(0)
    dense_rest = Value(0)

    dense_play.add_link(dense_play, 40)
    dense_play.add_link(light_play, 1)
    dense_play.add_link(dense_rest, 2)

    play.add_link(dense_play, 2)
    play.add_link(play, 10)
    play.add_link(light_play, 4)
    play.add_link(light_rest, 5)
    play.add_link(rest, 4)

    light_play.add_link(play, 2)
    light_play.add_link(light_rest, 4)

    light_rest.add_link(rest, 3)
    light_rest.add_link(dense_rest, 1)
    light_rest.add_link(light_rest, 2)
    light_rest.add_link(light_play, 2)

    rest.add_link(rest, 4)
    rest.add_link(dense_rest, 3)
    rest.add_link(light_play, 1)

    dense_rest.add_link(dense_rest, 100)
    dense_rest.add_link(rest, 2)
    dense_rest.add_link(light_play, 1)

    network.add_nodes([dense_play, play, light_play, light_rest, rest, dense_rest])
    return network


def viola_1_events_network():
    """
    Constructs and returns a network with two states: 1 (play) and 0 (don't play)
    Designed so that, when passed to document_tools.pdf_scribe, 'don't play' results in a space equal to the
    global font size (shared.Globals.FontSize)
    :return: instance of chance.network.Network
    """
    network = Network()
    dense_play = Value(1)
    play = Value(1)
    light_play = Value(1)
    light_rest = Value(0)
    rest = Value(0)
    dense_rest = Value(0)

    dense_play.add_link(dense_play, 5)
    dense_play.add_link(light_play, 1)
    dense_play.add_link(dense_rest, 2)

    play.add_link(dense_play, 1)
    play.add_link(play, 10)
    play.add_link(light_play, 4)
    play.add_link(light_rest, 5)
    play.add_link(rest, 4)

    light_play.add_link(play, 2)
    light_play.add_link(light_rest, 4)

    light_rest.add_link(rest, 3)
    light_rest.add_link(dense_rest, 1)
    light_rest.add_link(light_rest, 2)
    light_rest.add_link(light_play, 2)

    rest.add_link(rest, 6)
    rest.add_link(dense_rest, 4)
    rest.add_link(light_play, 1)

    dense_rest.add_link(dense_rest, 500)
    dense_rest.add_link(rest, 2)
    dense_rest.add_link(light_play, 1)

    network.add_nodes([dense_play, play, light_play, light_rest, rest, dense_rest])
    return network

def speaker_1_events_network():
    """
    Constructs and returns a network with two states: 1 (play) and 0 (don't play)
    Designed so that, when passed to document_tools.pdf_scribe, 'don't play' results in a space equal to the
    global font size (shared.Globals.FontSize)
    :return: instance of chance.network.Network
    """
    network = Network()
    dense_play = Value(1)
    play = Value(1)
    light_play = Value(1)
    light_rest = Value(0)
    rest = Value(0)
    dense_rest = Value(0)

    dense_play.add_link(dense_play, 5)
    dense_play.add_link(light_play, 1)
    dense_play.add_link(dense_rest, 2)

    play.add_link(dense_play, 2)
    play.add_link(play, 10)
    play.add_link(light_play, 4)
    play.add_link(light_rest, 5)
    play.add_link(rest, 4)

    light_play.add_link(play, 2)
    light_play.add_link(light_rest, 4)

    light_rest.add_link(rest, 3)
    light_rest.add_link(dense_rest, 1)
    light_rest.add_link(light_rest, 2)
    light_rest.add_link(light_play, 2)

    rest.add_link(rest, 4)
    rest.add_link(dense_rest, 3)
    rest.add_link(light_play, 1)

    dense_rest.add_link(dense_rest, 400)
    dense_rest.add_link(rest, 2)
    dense_rest.add_link(light_play, 1)

    network.add_nodes([dense_play, play, light_play, light_rest, rest, dense_rest])
    return network