import sys
import platform
import core.router
import core.intent
import skills.system_skills
from core.speech_output import speak


def run_cli_mode():
    """Terminal fallback / CLI mode."""
    print("Hello This is Your New Ai Assistant NOVA !!!! : Greeting's Boss ")
    print(f"Looks Like you're using {platform.system()}")

    speak("Greeting's!")

    while True:
        try:
            user_input = input("Enter your command: ")

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                speak("Goodbye!")
                break

            try:
                response = core.intent.runtime(user_input)
            except (ConnectionError, TimeoutError, ValueError, OSError):
                response = core.router.route(user_input)

            print(f"Assistant: {response}")
            speak(str(response))

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


def main():
    # If explicitly requested with --cli flag, run terminal mode
    if "--cli" in sys.argv:
        run_cli_mode()
        return

    # Default: Launch Desktop Window Application
    try:
        from ui.chat_window import launch_gui
        launch_gui()
    except Exception as e:
        print(f"[Warning: Failed to launch desktop window: {e}]")
        print("Falling back to terminal mode...")
        run_cli_mode()


if __name__ == "__main__":
    main()