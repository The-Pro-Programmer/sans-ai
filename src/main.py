from translatory import Translator
from correction_store import CorrectionStore
from input_processor import clean_text

translator = Translator()
store = CorrectionStore()

def run():
    text = input("Enter Sanskrit text: ")
    text = clean_text(text)

    # Step 1: Check memory
    saved = store.get(text)
    if saved:
        print("\n✅ Found saved translation:")
        print(saved)
        return

    # Step 2: Translate
    output = translator.translate(text)
    print("\n🤖 Model Translation:")
    print(output)

    # Step 3: Ask user for correction
    choice = input("\nIs this correct? (y/n): ")

    if choice.lower() == "n":
        corrected = input("Enter correct translation: ")
        store.save(text, corrected)
        print("✅ Saved for future use!")

if __name__ == "__main__":
    run()