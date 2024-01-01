from better_profanity import profanity
import traceback

profanity.load_censor_words()

class ProfanityFilter():
    def english_censor(self, text):
        return profanity.censor(text,"")   
    
    def hindi_censor(self, text):
        return text

    def censor_words(self, language, text):
        try:
            if language == "en":
                return self.english_censor(text)
            if language == "hi":
                return self.hindi_censor(text)
            else:
                return text
        except:
            print(f"Traceback of exception {traceback.format_exc()}")
