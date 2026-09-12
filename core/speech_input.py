import contextlib
import os
import speech_recognition as sr


@contextlib.contextmanager
def _silence_stderr():
    """Suppress ALSA/PyAudio messages from the terminal."""
    try:
        stderr_fd = os.dup(2)
        with open(os.devnull, "w") as devnull:
            os.dup2(devnull.fileno(), 2)
            yield
    except OSError:
        yield
    finally:
        try:
            os.dup2(stderr_fd, 2)
            os.close(stderr_fd)
        except (UnboundLocalError, OSError):
            pass


def listen():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True

    try:
        with _silence_stderr():
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(
                    source,
                    timeout=30,
                    phrase_time_limit=30,
                )

        return recognizer.recognize_google(audio)

    except (
        sr.WaitTimeoutError,
        sr.UnknownValueError,
        sr.RequestError,
        OSError,
    ):
        return None