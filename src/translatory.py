from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class Translator:
    def __init__(self):
        model_name = "ai4bharat/indictrans2-en-indic"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)

    def translate(self, text, target_lang="eng_Latn"):
        input_text = f"san_Deva {target_lang} {text}"
        inputs = self.tokenizer(input_text, return_tensors="pt")

        outputs = self.model.generate(**inputs, max_length=256)
        translated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return translated