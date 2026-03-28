import sys
import time
from unittest.mock import Mock, patch

sys.path.insert(0, ".")

import pygame

pygame.init()

import config


def test_audio_cooldown_integration():
    with patch.object(pygame.mixer, "Sound") as mock_sound:
        mock_instance = Mock()
        mock_sound.return_value = mock_instance

        import importlib
        import audio

        importlib.reload(audio)

        am = audio.AudioManager()

        mock_sound.reset_mock()
        mock_instance.reset_mock()

        am.trigger("HUMAN_DETECTED")
        am.trigger("HUMAN_DETECTED")

        assert mock_instance.play.call_count == 1


def test_priority_interrupt():
    with patch.object(pygame.mixer, "stop") as mock_stop:
        with patch.object(pygame.mixer, "Sound") as mock_sound:
            mock_instance = Mock()
            mock_sound.return_value = mock_instance

            import importlib
            import audio

            importlib.reload(audio)

            am = audio.AudioManager()

            am.trigger("HUMAN_DETECTED")
            mock_stop.reset_mock()
            am.trigger("ALERT")

            mock_stop.assert_called()


if __name__ == "__main__":
    from unittest.mock import Mock, patch

    test_audio_cooldown_integration()
    test_priority_interrupt()
    print("All audio tests passed!")
