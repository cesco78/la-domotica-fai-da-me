#!/usr/bin/env python3

# funzioni in Python utili per i progetti
# fatti da Francesco Tucci

import time
import datetime

# restituisce la data odierna alle 00:01:00
def adesso_mezzanotte():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d 00:01:00')
    return st

# restituisce la data di oggi nel formato aaaa-mm-gg
def oggi():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    return st

# restituisce la data di oggi nel formato mm-gg
def oggi_breve():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%m-%d')
    return st

# restituisce la data di domanii nel formato mm-gg
def domani_breve():
    ts = datetime.datetime.now() + datetime.timedelta(days=1)
    st = ts.strftime('%m-%d')
    return st

# restituisce l'ora attuale
def oggi():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M')
    return st
