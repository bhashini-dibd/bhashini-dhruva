from better_profanity import profanity
import traceback
from indicnlp.tokenize import indic_tokenize
import pandas as pd

df = pd.read_csv('module/services/utilities/profanity/profanity_words_list.csv')

# Initialize an empty dictionary to store lang_code sets
lang_code_sets = {}

# Iterate over columns (excluding the first column assuming it contains lang_code)
for column in df.columns[0:]:
    lang_code = column
    profane_set = set(df[lang_code].to_list())
    lang_code_sets[lang_code] = profane_set

class ProfanityFilter():
    def english_censor(self, text):
        return profanity.censor(text,"")   
    
    def indic_censor(self, language, text):
        # For URDU : ur, 
        print(f"BEFORE CENSORING TEXT :: {text} and language :: {language}")
        tokens = []
        for token in indic_tokenize.trivial_tokenize(text,lang=language): 
            if token not in lang_code_sets[language]:
                tokens.append(token)
        print(f"AFTER CENSORING TEXT :: {text} and language :: {language}")
        return " ".join(tokens)

    def censor_words(self, language, text):
        try:
            if language == "en":
                return self.english_censor(text)
            else:
                return self.indic_censor(language,text)
        except:
            print(f"Traceback of exception {traceback.format_exc()}")
