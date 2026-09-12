import core.router
import core.intent
import skills.system_skills
import platform
import pyttsx3


def main():
    print("Hello This is Your New Ai Assistant NOVA !!!! : Greeting's Boss ")
    print(f"Looks Like you're using {platform.system()}")

    engine = pyttsx3.init()
    engine.setProperty("rate", 120)
    engine.say("System's Online State Your Needs!")
    engine.runAndWait()

    while True:
        try:
            user_input = input("Enter your command: ")

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                engine.say("Goodbye!")
                engine.runAndWait()
                break

            try:
                response = core.intent.runtime(user_input)
            except (ConnectionError, TimeoutError, ValueError, OSError):
                response = core.router.route(user_input)

            print(f"Assistant: {response}")
            engine.say(str(response))
            engine.runAndWait()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()