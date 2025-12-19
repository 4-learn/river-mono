
export SDL_AUDIODRIVER=dummy
export ALSA_CARD=none
export ALSA_PCM_CARD=none

uvicorn main:app --host 0.0.0.0 --port 9005 --log-level info
